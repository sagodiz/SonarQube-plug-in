#!/usr/bin/env python

# Copyright (c) 2014-2018, FrontEndART Software Ltd.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by FrontEndART Software Ltd.
# 4. Neither the name of FrontEndART Software Ltd. nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY FrontEndART Software Ltd. ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL FrontEndART Software Ltd. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
from urllib.request import urlopen
import os
import shutil
import subprocess
import zipfile
from time import sleep
import platform
import pycurl
from urllib.parse import urlencode
from io import BytesIO
import json

import common

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true', default=False,
                        help='Initialize')
    parser.add_argument('-sv', '--server-version', default='7.9.5',
                        help='Version of the SQ server (default=%(default)s)')
    parser.add_argument('-scv', '--scanner-version', default='4.5.0.2216',
                        help='Version of the SQ scanner (default=%(default)s)')
    parser.add_argument('-plgf', '--plugins-folder', default=None,
                        help='Folder containing the plugins to be tested (default=%(default)s)')
    parser.add_argument('-prjf', '--projects-folder', default='projectsfolder',
                        help='Folder containing the project to be analyzed (default=%(default)s)')
    parser.add_argument('-noa', '--number-of-attempts', default=20,
                        help='Number of checking the status of SonarQube server (default=%(default)s times)')
    parser.add_argument('-wait', '--wait', default=10,
                        help='Wait between checking the status of SonarQube server (default=%(default)s seconds)')
    parser.add_argument('-cf', '--client-folder', default='test',
                        help='Folder for downloading and unzipping SQ server and scanner (default=%(default)s)')
    parser.add_argument('-smd', '--sourcemeter-directory', default='test',
                        help='Folder for downloading and unzipping SourceMeter (default=%(default)s)')
    parser.add_argument('-tpn', '--test-project-name', default='test',
                        help='Name of teh project during testing. (default=%(default)s)')
    parser.add_argument('-lot', '--language-of-test', default='java',
                        help='Language of the test. (default=%(default)s)')
    parser.add_argument('--print-log', action='store_true',
                        help='Prints the SQ log files to the screen')

    return parser.parse_args()

def run_check(runnable):
    sys.stderr.write('Test command: %s\n' % ' '.join(runnable))

    try:
        ret = subprocess.check_call(runnable)
    except subprocess.CalledProcessError as err:
        return err.returncode

    return ret

def download_sq_server(version, dst):
    print('Downloading: SonarQube server (version %s)...' % version)
    sq = urlopen('https://binaries.sonarsource.com/Distribution/'
                         'sonarqube/sonarqube-%s.zip' % version)
    dl = sq.read()
    path = os.path.join(dst, 'sonarqube-%s.zip' % version)
    with open(path, 'wb') as f:
        f.write(dl)
    print('SonarQube server download is completed! (version %s)' % version)

def download_sq_scanner(version, system, dst):
    system = system.lower()
    print('Downloading: SonarQube scanner (version %s)...' % version)
    sq = urlopen('https://binaries.sonarsource.com/Distribution/'
                         'sonar-scanner-cli/sonar-scanner-cli-%s-%s.zip' % (version, system))
    dl = sq.read()
    path = os.path.join(dst, 'sonar-scanner-cli-%s-%s.zip' % (version, system))
    with open(path, 'wb') as f:
        f.write(dl)
    print('SonarQube scanner download is completed! (version %s)' % version)

def unzip(file, dst):
    print('Unzipping files...')
    with zipfile.ZipFile(file, "r") as zip_ref:
        zip_ref.extractall(dst)
    dst = os.path.join(os.getcwd(), dst)
    print('Unzip finished! (%s)' % dst)

def copy_all_files_from_folder(src, dst):
    if src:
        src_files = os.listdir(src)
        for file_name in src_files:
            full_file_name = os.path.join(src, file_name)
            if (os.path.isfile(full_file_name)):
                shutil.copy(full_file_name, dst)
    else:
        plugins = ['core', 'gui']
        for plugin in plugins:
            path = ['src', 'sonarqube-%s-plugin' % plugin, 'target', 'sourcemeter-%s-plugin-2.0.1.jar' % plugin]
            path  = os.path.join(*path)
            shutil.copy(path, dst)

        languages = ['cpp', 'csharp', 'java', 'python', 'rpg']
        for language in languages:
            path = ['src', 'sonarqube-analyzers', 'sourcemeter-analyzer-%s' % language, 'target', 'sourcemeter-analyzer-%s-plugin-2.0.1.jar' % language]
            path  = os.path.join(*path)
            shutil.copy(path, dst)
    print('Copy finished!')

def start_sq_server(version, system, dst):
    cmd = ''
    cwd = os.getcwd()
    if system == 'Windows':
        sonar_location = cwd + '\\' + dst + '\\' + 'sonarqube-%s\\bin\\windows-x86-64\\StartSonar.bat' % version
        common.run_cmd('start', [sonar_location])
    elif system == 'Linux':
        sonar_location = cwd + '/' + dst + '/sonarqube-%s' % version

        temp = sonar_location
        for root, dirs, files in os.walk(temp):
            for file in files:
                file_path = os.path.join(root, file)
                os.chmod(file_path, 0o744)

        cmd = os.path.join(sonar_location, 'bin/linux-x86-64/sonar.sh')
        common.run_cmd(cmd, ['start', '&'])
    print('Starting SQ server...')

def validate_running_of_sq_server(version, number_of_attempts, wait):
    number_of_attempts = int(number_of_attempts)
    while not number_of_attempts == 0:
        try:
            contents = urlopen('http://localhost:9000/api/system/ping').read()
            return True
        except:
            print('SonarQube is not started yet, rechecking...' + ' (%d attempt(s) left)' % number_of_attempts)
            number_of_attempts -= 1
            sleep(float(wait))
    return False

def create_user_in_sq(username = 'myuser', password = 'mypassword'):

    crl = pycurl.Curl()
    #crl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
    crl.setopt(crl.URL, 'http://127.0.0.1:9000/api/users/create')
    crl.setopt(pycurl.USERPWD, 'admin:admin')
    data = [('login', username),
    ('password', password),
    ('password_confirmation', password),
    ('name', 'name'),
    ('email', 'mail@email.com'),]
    pf = urlencode(data)

    # Sets request method to POST,
    # Content-Type header to application/x-www-form-urlencoded
    # and data to send in request body.
    crl.setopt(crl.POSTFIELDS, pf)
    crl.perform()

    code = crl.getinfo(pycurl.HTTP_CODE)
    print(code)
    crl.close()

    crl = pycurl.Curl()
    #crl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
    crl.setopt(crl.URL, 'http://127.0.0.1:9000/api/user_groups/add_user')
    crl.setopt(pycurl.USERPWD, 'admin:admin')
    data = [('login', username),
    ('name', 'sonar-administrators'),]
    pf = urlencode(data)
    crl.setopt(crl.POSTFIELDS, pf)
    crl.perform()

    code_admin = crl.getinfo(pycurl.HTTP_CODE)
    crl.close()
    return (code == 200 and code_admin == 204) # 204 means OK

def set_sm(toolchaindir, admin_user = 'myuser', admin_pwd = 'mypassword'):
    crl = pycurl.Curl()
    #crl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
    crl.setopt(crl.URL, 'http://127.0.0.1:9000/api/settings/set')
    crl.setopt(pycurl.USERPWD, f"{admin_user}:{admin_pwd}")
    data = [('key', 'sm.toolchaindir'),
            ('value', toolchaindir),]
    pf = urlencode(data)
    crl.setopt(crl.POSTFIELDS, pf)
    crl.perform()

    code = crl.getinfo(pycurl.HTTP_CODE)
    crl.close()

    return code == 204

def set_default_profile(profile, language, admin_user = 'myuser', admin_pwd = 'mypassword'):
    crl = pycurl.Curl()
    #crl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
    crl.setopt(crl.URL, 'http://127.0.0.1:9000/api/qualityprofiles/set_default')
    crl.setopt(pycurl.USERPWD, f"{admin_user}:{admin_pwd}")
    data = [('language', language),
            ('qualityProfile', profile),]
    pf = urlencode(data)
    crl.setopt(crl.POSTFIELDS, pf)
    crl.perform()

    code = crl.getinfo(pycurl.HTTP_CODE)
    crl.close()
    
    return code == 204 # 204 marks OK

def create_project(project_name = 'test_project', admin_user = 'myuser', admin_pwd = 'mypassword'):
    crl = pycurl.Curl()
    #crl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
    crl.setopt(crl.URL, 'http://127.0.0.1:9000/api/projects/create')
    crl.setopt(pycurl.USERPWD, f"{admin_user}:{admin_pwd}")
    data = [('name', project_name),
            ('project', project_name),]
    pf = urlencode(data)
    crl.setopt(crl.POSTFIELDS, pf)
    crl.perform()
    crl.getinfo(pycurl.HTTP_CODE)
    crl.close()
    
    crl = pycurl.Curl()
    data_resp = BytesIO()
    #crl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
    crl.setopt(crl.URL, 'http://127.0.0.1:9000/api/user_tokens/generate')
    crl.setopt(pycurl.USERPWD, f"{admin_user}:{admin_pwd}")
    crl.setopt(pycurl.WRITEFUNCTION, data_resp.write)
    data = [('name', project_name),]
    pf = urlencode(data)
    crl.setopt(crl.POSTFIELDS, pf)
    crl.perform()
    code_token = crl.getinfo(pycurl.HTTP_CODE)
    crl.close()

    token = None
    if 200 == code_token:
        response = json.loads(data_resp.getvalue())
        token = response['token']

    return token


def analyze(dst, # folder of client (Where scanner is extracted.)
            scanner_version, 
            system, # system teh test runs on
            abs_project_path, 
            token, # token for the user to upload results
            language = 'java', # analyzed project's language
            binary_path = '', # if needed for the language like java
            project_key = 'test_project', # select project
            server_address = 'http://localhost:9000'):

    scanner_binary = os.path.join(dst, f"sonar-scanner-{scanner_version}-{system}", "bin")
    if system == 'Windows':
        # windows
        scanner_binary += '\sonar-scanner.bat'
    else:
        # linux
        scanner_binary += '/sonar-scanner.sh'

    parameters = [f"-Dsonar.projectBaseDir={abs_project_path}", 
                f"-Dsonar.projectKey={project_key}",
                f"-Dsonar.host.url={server_address}"]
    if language == 'java':
        parameters.append(f"-Dsonar.java.binaries={binary_path}")

    common.run_cmd(scanner_binary, parameters)

def validate_results(project_name, language, admin_user = 'myuser', admin_pwd = 'mypassword'):
    crl = pycurl.Curl()
    data_resp = BytesIO()

    parameters = f"?componentKey={project_name}&metricKeys="

    if language == 'java':
        parameters += "SM_JAVA_LOGICAL_LEVEL1"

    crl.setopt(crl.URL, 'http://127.0.0.1:9000/api/measures/component' + parameters)
    crl.setopt(pycurl.USERPWD, f"{admin_user}:{admin_pwd}")
    crl.setopt(pycurl.WRITEFUNCTION, data_resp.write)
    crl.perform()
    crl.close()
    data = json.loads(data_resp.getvalue())
    data = json.loads(data['component']['measures'][0]['value'])
    if 0 != data['level'][0]['metrics']['TLOC']:
        return True

    return False


def print_log(version, path):
    path = os.path.join(path, 'sonarqube-%s' % version, 'logs')
    for file in [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]:
        print('File name: ' + file)
        with open(os.path.join(path, file), 'r') as f_in:
            print(f_in.read())

def main(options):
    server_version = options.server_version
    scanner_version = options.scanner_version
    src_of_the_plugins = options.plugins_folder
    src_of_the_project = options.projects_folder
    noa = options.number_of_attempts
    wait = options.wait
    system = platform.system()
    dst = options.client_folder
    print_log_files = options.print_log
    sm_directory = options.sourcemeter_directory
    test_project_name = options.test_project_name
    language_of_test = options.language_of_test
    common.mkdir(dst)

    # 0, a) Try to build the plugins with 'build.py'
    
    common.run_cmd('python3', ['tools/build.py', '--all'])

    if options.init == True:
        # 0, b) download sonar-server'

        download_sq_server(server_version, dst)

        # 1) download sonar-scanner

        download_sq_scanner(scanner_version, system, dst)

        # 2) unzip both server and scanner

        src = os.path.join(dst, f"sonarqube-{server_version}.zip")
        unzip(src, dst)

        src = os.path.join(dst, f"sonar-scanner-cli-{scanner_version}-{system.lower()}.zip")
        unzip(src, dst)

    # 3) copy the plugins into the server dir

    path = [dst, f"sonarqube-{server_version}", 'extensions', 'plugins']
    path = os.path.join(*path)
    copy_all_files_from_folder(src_of_the_plugins, path)

    # 4) start the server with the defult config

    start_sq_server(server_version, system, dst)

    # 5) Validate the server is started succesfully

    sleep(60)
    if validate_running_of_sq_server(server_version, noa, wait):
        print('SonarQube started properly!')
    else:
        print(('SonarQube did not start in time (-noa=%s (number of attempts))' % (noa)))
        if print_log_files:
            print_log(server_version, dst)
        exit(5)

    # 6) Create sq user

    sleep(20)
    print('Creating user in SonarQube...')
    if not create_user_in_sq():
        print('Creating user failed.')
        exit(6)
    print('User successfully created.')
    
    # 7) Set SourceMeter directory

    print('Setting SourceMeter directory..')
    if not set_sm(sm_directory):
        print(f"Could not set SourceMeter directory to: '{sm_directory}'")
        exit(7)
    print(f"SourceMeter directory set to: '{sm_directory}'")
    
    print('Setting default profile to SourceMeter Way..')
    if not set_default_profile('SourceMeter Way', language_of_test):
        print('Setting profile failed.')
        exit(8)
    print('Profile set.')
    
    # 8) Creating project

    print('Creating project..')
    token = create_project(test_project_name)
    if token == None:
        print('Project creation failed.')
        exit(9)
    print('Project successfully created.')

    # 9) Analyzing project with sonar scanner using SM.

    print('Starting analyze project..')
    analyze(os.path.abspath(dst), 
            scanner_version, 
            system, 
            os.path.abspath('src/sonarqube-core-plugin'), 
            token,
            language_of_test,
            os.path.abspath('src/sonarqube-core-plugin/target/classes'),
            test_project_name)
    
    # 10) Checking the results
    
    print('Reading uploaded data from database..')
    sleep(5) # wait till the results are ready to read.
    if not validate_results(test_project_name, language_of_test):
        print('Could not read data or it was not correct.')
        exit(10)
    print('Successfully read data.')

if __name__ == "__main__":
    main(get_arguments())
