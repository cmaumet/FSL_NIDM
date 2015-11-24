#!/usr/bin/env python
"""
Test of NIDM FSL export tool


@author: Camille Maumet <c.m.j.maumet@warwick.ac.uk>
@copyright: University of Warwick 2013-2014
"""
import unittest
import os
from rdflib.graph import Graph
import shutil
import sys
import glob
import json
from export_test_data import ExportTestData

import logging
logger = logging.getLogger(__name__)
# Display log messages in console
logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w',
                    format='%(levelname)s - %(message)s')

RELPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add FSL NIDM export to python path
sys.path.append(RELPATH)

# Add nidm common testing code folder to python path
NIDM_DIR = os.path.join(RELPATH, "nidm")
# In TravisCI the nidm repository will be created as a subtree, however locally
# the nidm directory will be accessed directly
logging.debug(NIDM_DIR)

if not os.path.isdir(NIDM_DIR):
    NIDM_DIR = os.path.join(os.path.dirname(RELPATH), "nidm")

NIDM_RESULTS_DIR = os.path.join(NIDM_DIR, "nidm", "nidm-results")
TERM_RESULTS_DIRNAME = "terms"
# ORIGINAL_TEST_DATA_DIR = os.path.join(TEST_DIR, "original_data")

path = os.path.join(NIDM_RESULTS_DIR, "test")
sys.path.append(path)


from TestResultDataModel import TestResultDataModel
from TestCommons import *
from CheckConsistency import *


from ddt import ddt, data

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

test_configfile = os.path.join(TEST_DIR, "config.json")
test_data_dir = None
if os.path.isfile(test_configfile):
    with open(test_configfile) as config_file:
        test_config = json.load(config_file)
        test_data_dir = test_config['test_data_folder']

testexport = ExportTestData(test_data_dir)
test_files = testexport.export_all()

# # Find all test examples to be compared with ground truth
# test_files = glob.glob(os.path.join(TEST_DIR, 'fsl_*', 'nidm', '*.ttl'))
# # For test name readability remove path to test file
test_files = [x.replace(testexport.test_data_dir, "") for x in test_files]
logging.info("Test files:\n\t" + "\n\t".join(test_files))

@ddt
class TestFSLResultDataModel(unittest.TestCase, TestResultDataModel):

    # @classmethod
    # def setUpClass(cls):
        # # Original data directory => this will be replaced by data stored at
        # # https://github.com/incf-nidash/nidmresults-examples
        # # *** Once for all, run the export
        # for ttl_name in test_files:
        #     ttl = TEST_DIR+ttl_name
        #     test_dir = os.path.dirname(ttl)

        #     # If test data is available (usually if the test is run locally)
        #     # then compute a fresh export
        #     with open(os.path.join(test_dir, 'config.json')) as data_file:
        #         metadata = json.load(data_file)
        #     data_dir = os.path.join(ORIGINAL_TEST_DATA_DIR, metadata["data_dir"])
        #     version = metadata["version"]

        #     #  Turtle file obtained with FSL NI-DM export tool
        #     provn = ttl.replace(".ttl", ".provn")

        #     if os.path.isdir(data_dir):
        #         logging.debug("Computing NIDM FSL export")

        #         # Export to NIDM using FSL export tool
        #         # fslnidm = FSL_NIDM(feat_dir=DATA_DIR_001);
        #         fslnidm = FSLtoNIDMExporter(feat_dir=data_dir, version=version)
        #         fslnidm.parse()
        #         export_dir = fslnidm.export()
        #         # Copy provn export to test directory
        #         shutil.copy(os.path.join(export_dir, 'nidm.provn'),
        #                     os.path.join(provn))
        #         shutil.copy(os.path.join(export_dir, 'nidm.ttl'),
        #                     os.path.join(ttl))

    def setUp(self):
        # Retreive owl file for NIDM-Results
        owl_file = os.path.join(NIDM_RESULTS_DIR, TERM_RESULTS_DIRNAME,
                                'nidm-results.owl')
        import_files = glob.glob(
            os.path.join(os.path.dirname(owl_file),
                         os.pardir, os.pardir, "imports", '*.ttl'))

        TestResultDataModel.setUp(
            self, owl_file, import_files, test_files,
            test_data_dir,
            parent_gt_dir=os.path.join(test_data_dir, "ground_truth"))

    @data(*test_files)
    def test_class_consistency_with_owl(self, ttl):
        """
        Test: Check that the classes used in the ttl file are defined in the
        owl file.
        """
        ex = self.ex_graphs[ttl]
        ex.owl.check_class_names(ex.graph, ex.name, True)

    @data(*test_files)
    def test_attributes_consistency_with_owl(self, ttl):
        """
        Test: Check that the attributes used in the ttl file comply with their
        definition (range, domain) specified in the owl file.
        """
        ex = self.ex_graphs[ttl]
        ex.owl.check_attributes(ex.graph, "FSL example001", True)

    @data(*test_files)
    def test_examples_match_ground_truth(self, ttl):
        """
        Test03: Comparing that the ttl file generated by FSL and the expected
        ttl file (generated manually) are identical
        """

        ex = self.ex_graphs[ttl]

        for gt_file in ex.gt_ttl_files:
            logging.info("Ground truth ttl: " + gt_file)

            # RDF obtained by the ground truth export
            gt = Graph()
            gt.parse(gt_file, format='turtle')

            self.compare_full_graphs(gt, ex.graph, ex.exact_comparison, True)

if __name__ == '__main__':
    unittest.main()


