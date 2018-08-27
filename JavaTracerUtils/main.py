import logging

from data.config import Config
from db_builder import MavenTestTraceDbFactory
import datetime
from os import path

# config log
BUG_CONFIGS = {
    'DATE': str(datetime.datetime.now()),
    'DEBUG': str(Config.DEBUG),
    'FAIL_SAMPLE_RATE': str(Config.FAIL_SAMPLE_RATE),
    'SUCCESS_SAMPLE_RATE': str(Config.SUCCESS_SAMPLE_RATE),
    'PROJECT_ROOT_PATH': Config.PROJECT_ROOT_PATH,
    'BUG_PROJECT': Config.BUG_PROJECT,
    'BUG_ID': str(Config.BUG_ID),
    'ACTUAL_FAULTS': str(list(Config.actual_faults_method_fullname_set)),
    'ON_THE_FLY': str(Config.ON_THE_FLY),
    'IGNORED_CLASSES': str(','.join(Config.IGNORED_CLASS_LIST))
}

# =================================================================================================================

# region logger setup
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s | %(levelname)s] - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
# endregion

if Config.DEBUG:
    # sample file
    TEST_FILES_LIST_PATH = rf"C:\git\JavaTracer\JavaTracerUtils\data\mockInputFiles.lst"
    # TEST_FILES_LIST_PATH = r"C:\git\JavaTracer\JavaTracerUtils\data\inputFiles.lst"
else:
    TEST_FILES_LIST_PATH = path.join(Config.PROJECT_ROOT_PATH,'target','maven-status','maven-compiler-plugin','testCompile','default-testCompile','inputFiles.lst')

TRACES_LOG_FILE_PATH = path.join(Config.PROJECT_ROOT_PATH,'traces0.log')
OUTPUT_DATA_ROOT_PATH = '/Users/ori/pergit/JavaTracer/JavaTracerUtils/data'


# Build raw data storage, then SQLite storage
db_builder = MavenTestTraceDbFactory(project_root_path=Config.PROJECT_ROOT_PATH,
                                     test_files_list_path=TEST_FILES_LIST_PATH,
                                     log_file_path=TRACES_LOG_FILE_PATH,
                                     output_data_root_path=OUTPUT_DATA_ROOT_PATH,
                                     bug_project=Config.BUG_PROJECT,
                                     bug_id=Config.BUG_ID,
                                     actual_faults_method_fullname_set=Config.actual_faults_method_fullname_set,
                                     on_the_fly=Config.ON_THE_FLY,
                                     bug_configurations_to_log=BUG_CONFIGS,
                                     fail_sample_rate=Config.FAIL_SAMPLE_RATE,
                                     success_sample_rate=Config.SUCCESS_SAMPLE_RATE,
                                     ignored_test_files=Config.IGNORED_CLASS_LIST)

# remove raw data storage
