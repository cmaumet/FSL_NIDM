#!/usr/bin/env python
"""
Test of NIDM FSL export tool


@author: Camille Maumet <c.m.j.maumet@warwick.ac.uk>
@copyright: University of Warwick 2013-2014
"""
import unittest
import os
from rdflib.graph import Graph
import glob

import logging
logger = logging.getLogger(__name__)
# Display log messages in console
logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w',
                    format='%(levelname)s - %(message)s')

TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exported")

from nidmresults.test.test_results_doc import TestResultDataModel
from nidmresults.test.test_commons import *
from nidmresults.test.check_consistency import *

from ddt import ddt, data

# Find all test examples to be compared with ground truth
test_files = glob.glob(os.path.join(TEST_DIR, 'ex*', '*.ttl'))
# For test name readability remove path to test file
# test_files = [x.replace(TEST_DIR, "") for x in test_files]
logging.info("Test files:\n\t" + "\n\t".join(test_files))


@ddt
class TestFSLResultDataModel(unittest.TestCase, TestResultDataModel):

    def setUp(self):
        gt_dir = os.path.join(TEST_DIR, '_ground_truth')

        TestResultDataModel.setUp(self, gt_dir)

    @data(*test_files)
    def test_class_consistency_with_owl(self, ttl):
        """
        Test: Check that the classes used in the ttl file are defined in the
        owl file.
        """
        ex = self.load_graph(ttl)
        ex.owl.check_class_names(ex.graph, ex.name, True)

    @data(*test_files)
    def test_attributes_consistency_with_owl(self, ttl):
        """
        Test: Check that the attributes used in the ttl file comply with their
        definition (range, domain) specified in the owl file.
        """
        ex = self.load_graph(ttl)
        ex.owl.check_attributes(ex.graph, "FSL example001", True)

    @data(*test_files)
    def test_examples_match_ground_truth(self, ttl):
        """
        Test03: Comparing that the ttl file generated by FSL and the expected
        ttl file (generated manually) are identical
        """

        ex = self.load_graph(ttl)

        for gt_file in ex.gt_ttl_files:
            logging.info("Ground truth ttl: " + gt_file)

            # RDF obtained by the ground truth export
            gt = Graph()
            gt.parse(gt_file, format='turtle')

            self.compare_full_graphs(gt, ex.graph, ex.owl,
                                     ex.exact_comparison, True)

if __name__ == '__main__':
    unittest.main()
