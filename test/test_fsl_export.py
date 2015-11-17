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
    # The FSL export to NIDM will only be run locally (for now)
    from nidmfsl.fsl_exporter.fsl_exporter import FSLtoNIDMExporter

NIDM_RESULTS_DIR = os.path.join(NIDM_DIR, "nidm", "nidm-results")
TERM_RESULTS_DIRNAME = "terms"
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_TEST_DATA_DIR = os.path.join(TEST_DIR, "original_data")

path = os.path.join(NIDM_RESULTS_DIR, "test")
sys.path.append(path)


from TestResultDataModel import TestResultDataModel
from TestCommons import *
from CheckConsistency import *
import git
import tempfile

from ddt import ddt, data

# Find all test examples to be compared with ground truth
test_files = glob.glob(os.path.join(TEST_DIR, 'ex*', '*.ttl'))
# For test name readability remove path to test file
test_files = [x.replace(TEST_DIR, "") for x in test_files]
logging.info("Test files:\n\t" + "\n\t".join(test_files))


@ddt
class TestFSLResultDataModel(unittest.TestCase, TestResultDataModel):

    @classmethod
    def setUpClass(cls):
        # Check if a directory was specified to store test data (otherwise
        # create a temporary folder)
        test_configfile = os.path.join(TEST_DIR, "config.json")
        if os.path.isfile(test_configfile):
            with open(test_configfile) as config_file:
                test_config = json.load(config_file)
                test_data_dir = test_config['test_data_folder']
        else:
            test_data_dir = tempfile.mkdtemp()

        if not os.path.isdir(os.path.join(test_data_dir, ".git")):
            logging.debug("Cloning to " + test_data_dir)
            # Cloning test data repository
            data_repo = git.Repo.clone_from(
                "https://github.com/incf-nidash/nidmresults-examples.git",
                test_data_dir)
        else:
            # Updating test data repository
            logging.debug("Updating repository at " + test_data_dir)
            data_repo = git.Repo(test_data_dir)
            origin = data_repo.remote("origin")
            origin.pull()

        # Find all test data to be compared with ground truth
        # test_files = glob.glob(os.path.join(TEST_DATA_DIR, '*', '*.ttl'))
        test_dirs = next(os.walk(test_data_dir))[1]
        test_dirs.remove(".git")
        test_dirs.remove("ground_truth")
        for data_dirname in test_dirs:
            data_dir = os.path.join(test_data_dir, data_dirname)
            with open(os.path.join(data_dir, 'config.json'))\
                    as data_file:
                metadata = json.load(data_file)
            version = metadata["version"]
            software = metadata["software"]

            if software.lower() == "fsl":
                logging.debug("Computing NIDM FSL export")
                fslnidm = FSLtoNIDMExporter(feat_dir=data_dir, version=version)
                fslnidm.parse()
                export_dir = fslnidm.export()
                # Copy provn export to test directory
                shutil.copy(os.path.join(export_dir, 'nidm.provn'),
                            os.path.join(provn))
                shutil.copy(os.path.join(export_dir, 'nidm.ttl'),
                            os.path.join(ttl))
            else:
                print software

        # Original data directory => this will be replaced by data stored at
        # https://github.com/incf-nidash/nidmresults-examples
        # *** Once for all, run the export
        for ttl_name in test_files:
            ttl = TEST_DIR+ttl_name
            test_dir = os.path.dirname(ttl)

            # If test data is available (usually if the test is run locally)
            # then compute a fresh export
            with open(os.path.join(test_dir, 'config.json')) as data_file:
                metadata = json.load(data_file)
            data_dir = os.path.join(ORIGINAL_TEST_DATA_DIR, metadata["data_dir"])
            version = metadata["version"]

            #  Turtle file obtained with FSL NI-DM export tool
            provn = ttl.replace(".ttl", ".provn")

            if os.path.isdir(data_dir):
                logging.debug("Computing NIDM FSL export")

                # Export to NIDM using FSL export tool
                # fslnidm = FSL_NIDM(feat_dir=DATA_DIR_001);
                fslnidm = FSLtoNIDMExporter(feat_dir=data_dir, version=version)
                fslnidm.parse()
                export_dir = fslnidm.export()
                # Copy provn export to test directory
                shutil.copy(os.path.join(export_dir, 'nidm.provn'),
                            os.path.join(provn))
                shutil.copy(os.path.join(export_dir, 'nidm.ttl'),
                            os.path.join(ttl))

    def setUp(self):
        # Retreive owl file for NIDM-Results
        owl_file = os.path.join(NIDM_RESULTS_DIR, TERM_RESULTS_DIRNAME,
                                'nidm-results.owl')
        import_files = glob.glob(
            os.path.join(os.path.dirname(owl_file),
                         os.pardir, os.pardir, "imports", '*.ttl'))

        TestResultDataModel.setUp(self, owl_file, import_files, test_files,
                                  TEST_DIR, NIDM_RESULTS_DIR)

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
