import logging
from db_builder import MavenTestTraceDbFactory
import datetime

# region bug configurations
PROJECT_ROOT_PATH = r"C:\defects\math_1_buggy"
BUG_PROJECT = 'math'
BUG_ID = 1
# this requires complete names: <package>.<class>.<method>(parameters)
# example: 'fraction.BigFraction.BigFraction(double_double_int_int)'
actual_faults_method_fullname_set = frozenset({'fraction.BigFraction.BigFraction(double_double_int_int)',
                                               'fraction.Fraction.Fraction(double_double_int_int)'})
ON_THE_FLY = True  # don't create intermediate files -> this improves performance
# endregion

DEBUG = True
FAIL_SAMPLE_RATE = '0.01'
SUCCESS_SAMPLE_RATE = '1.00'

# config log
BUG_CONFIGS = {
    'DATE': str(datetime.datetime.now()),
    'DEBUG': str(DEBUG),
    'SAMPLE_RATE': SAMPLE_RATE,
    'PROJECT_ROOT_PATH': PROJECT_ROOT_PATH,
    'BUG_PROJECT': BUG_PROJECT,
    'BUG_ID': str(BUG_ID),
    'ACTUAL_FAULTS': str(list(actual_faults_method_fullname_set)),
    'ON_THE_FLY': str(ON_THE_FLY)
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

if DEBUG:
    # sample file
    TEST_FILES_LIST_PATH = rf"C:\git\JavaTracer\JavaTracerUtils\data\mockInputFiles.lst"
    # TEST_FILES_LIST_PATH = r"C:\git\JavaTracer\JavaTracerUtils\data\inputFiles.lst"
else:
    TEST_FILES_LIST_PATH = rf"{PROJECT_ROOT_PATH}\target\maven-status\maven-compiler-plugin\testCompile\default-testCompile\inputFiles.lst"

TRACES_LOG_FILE_PATH = rf"{PROJECT_ROOT_PATH}\traces0.log"
OUTPUT_DATA_ROOT_PATH = r"C:\git\JavaTracer\JavaTracerUtils\data"


# Build raw data storage, then SQLite storage
db_builder = MavenTestTraceDbFactory(project_root_path=PROJECT_ROOT_PATH, test_files_list_path=TEST_FILES_LIST_PATH,
                                     log_file_path=TRACES_LOG_FILE_PATH, output_data_root_path=OUTPUT_DATA_ROOT_PATH,
                                     bug_project=BUG_PROJECT, bug_id=BUG_ID,
                                     actual_faults_method_fullname_set=actual_faults_method_fullname_set,
                                     on_the_fly=ON_THE_FLY,
                                     bug_configurations_to_log=BUG_CONFIGS)

# remove raw data storage