import logging
from db_builder import MavenTestTraceDbFactory

# region bug configurations
PROJECT_ROOT_PATH = r"C:\defects\math_1_buggy"
BUG_PROJECT = 'math'
BUG_ID = 1
actual_faults_method_name_set = frozenset([])
# endregion

# region logger setup
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s | %(levelname)s] - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
# endregion

DEBUG = True

if DEBUG:
    # sample file
    TEST_FILES_LIST_PATH = rf"C:\git\JavaTracer\JavaTracerUtils\data\mockInputFiles.lst"
else:
    TEST_FILES_LIST_PATH = rf"{PROJECT_ROOT_PATH}\target\maven-status\maven-compiler-plugin\testCompile\default-testCompile\inputFiles.lst"

TRACES_LOG_FILE_PATH = rf"{PROJECT_ROOT_PATH}\traces0.log"
OUTPUT_DATA_ROOT_PATH = r"C:\git\JavaTracer\JavaTracerUtils\data"


# Build raw data storage, then SQLite storage
db_builder = MavenTestTraceDbFactory(project_root_path=PROJECT_ROOT_PATH, test_files_list_path=TEST_FILES_LIST_PATH,
                                     log_file_path=TRACES_LOG_FILE_PATH, output_data_root_path=OUTPUT_DATA_ROOT_PATH,
                                     bug_project=BUG_PROJECT, bug_id=BUG_ID)

# remove raw data storage