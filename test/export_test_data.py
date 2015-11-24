import os
import json
import git
import tempfile
import logging
from subprocess import check_call

RELPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add nidm common testing code folder to python path
NIDM_DIR = os.path.join(RELPATH, "nidm")
# In TravisCI the nidm repository will be created as a subtree, however locally
# the nidm directory will be accessed directly
logging.debug(NIDM_DIR)

# The FSL export to NIDM will only be run locally (for now)
from nidmfsl.fsl_exporter.fsl_exporter import FSLtoNIDMExporter

logger = logging.getLogger(__name__)
# Display log messages in console
logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w',
                    format='%(levelname)s - %(message)s')
TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class ExportTestData(object):
    def __init__(self, test_data_dir=None):
        if not test_data_dir:
            test_data_dir = tempfile.mkdtemp()
        self.test_data_dir = test_data_dir

    def export_all(self):
        """
        Export using NIDM-Results FSL exporter
        """
        test_data_dir = self.test_data_dir

        print test_data_dir
        print os.path.join(test_data_dir, ".git")
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

        # Not sure why this is needed on Travis CI to get the files 
        # (instead of pointers)
        check_call("cd "+test_data_dir+ "; git checkout .", shell=True)

        # print "\n\n\n --------------------"
        # check_call("cd "+test_data_dir+ "; git lfs ls-files", shell=True)
        # print "\n\n\n --------------------"        
            
        print "\n\n\n --------------------"        
        print "file "+test_data_dir+ "/fsl_voxelwise_p0001/stats/sigmasquareds.nii.gz"
        check_call("file "+test_data_dir+ "/fsl_voxelwise_p0001/stats/sigmasquareds.nii.gz", shell=True)
        check_call("file "+test_data_dir+ "/fsl_voxelwise_p0001/design.png", shell=True)
        print "\n\n\n --------------------"

        # Find all test data to be compared with ground truth
        # test_files = glob.glob(os.path.join(TEST_DATA_DIR, '*', '*.ttl'))
        test_dirs = next(os.walk(test_data_dir))[1]
        test_dirs.remove(".git")
        test_dirs.remove("ground_truth")

        test_files = list()

        test_dirs = [test_dirs[1]]
        print test_dirs

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
                nidm_dir = fslnidm.export()
                test_files.append(os.path.join(nidm_dir, "nidm.ttl"))
            else:
                print software

        return test_files
