/**
 * Copyright (c) 2014-2017, FrontEndART Software Ltd.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. All advertising materials mentioning features or use of this software
 *    must display the following acknowledgement:
 *    This product includes software developed by FrontEndART Software Ltd.
 * 4. Neither the name of FrontEndART Software Ltd. nor the
 *    names of its contributors may be used to endorse or promote products
 *    derived from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY FrontEndART Software Ltd. ''AS IS'' AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL FrontEndART Software Ltd. BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package com.sourcemeter.analyzer.python.visitor;

import java.util.Arrays;
import java.util.List;

import org.sonar.api.batch.fs.FileSystem;
import org.sonar.api.batch.sensor.SensorContext;
import org.sonar.api.config.Configuration;

import graphlib.Node;
import graphlib.VisitorException;

import com.sourcemeter.analyzer.base.helper.FileHelper;
import com.sourcemeter.analyzer.base.jsontree.interfaces.MetricsInt;
import com.sourcemeter.analyzer.base.visitor.LogicalTreeSaverVisitor;
import com.sourcemeter.analyzer.python.core.Python;
import com.sourcemeter.analyzer.python.helper.VisitorHelperPython;
import com.sourcemeter.analyzer.python.jsontree.logical.base.LevelOneMetrics;
import com.sourcemeter.analyzer.python.jsontree.logical.base.LevelThreeMetrics;
import com.sourcemeter.analyzer.python.jsontree.logical.base.LevelTwoMetrics;
import com.sourcemeter.analyzer.python.jsontree.logical.extended.LevelOneMetricsEx;
import com.sourcemeter.analyzer.python.jsontree.logical.extended.LevelThreeMetricsEx;
import com.sourcemeter.analyzer.python.jsontree.logical.extended.LevelTwoMetricsEx;

public class LogicalTreeSaverVisitorPython extends LogicalTreeSaverVisitor {

    private static final List<Node.NodeType> levelOneTypes = Arrays.asList(new Node.NodeType("Package"));
    private static final List<Node.NodeType> levelTwoTypes = Arrays.asList(new Node.NodeType("Class"));
    private static final List<Node.NodeType> levelThreeTypes =  Arrays.asList(new Node.NodeType("Function"),
                                                                              new Node.NodeType("Method"));

    public LogicalTreeSaverVisitorPython(SensorContext sensorContext, FileSystem fileSystem, Configuration configuration) {
        super(levelOneTypes, levelTwoTypes, levelThreeTypes,
               sensorContext, new VisitorHelperPython(sensorContext, fileSystem), new Python());

        super.extendedMetrics = !"false".equals(FileHelper.getStringFromConfiguration(configuration, "sm.uploadAllMetrics"));
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void preNodeVisitorFunc(Node node) {

        MetricsInt levelOneMetrics;
        MetricsInt levelTwoMetrics;
        MetricsInt levelThreeMetrics;

        try {
            if (!super.extendedMetrics) {
                levelOneMetrics = new LevelOneMetrics();
                levelTwoMetrics = new LevelTwoMetrics();
                levelThreeMetrics = new LevelThreeMetrics();
                super.preNodeVisitorFunc(node, levelOneMetrics, levelTwoMetrics, levelThreeMetrics);

            } else {
                levelOneMetrics = new LevelOneMetricsEx();
                levelTwoMetrics = new LevelTwoMetricsEx();
                levelThreeMetrics = new LevelThreeMetricsEx();
                super.preNodeVisitorFunc(node, levelOneMetrics, levelTwoMetrics, levelThreeMetrics);
            }
        } catch (VisitorException e) {
            LOG.error("Error during saving the logical tree!");
        }
    }
}
