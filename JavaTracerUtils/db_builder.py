"""
Module Description
"""
import glob
import json
import logging
import os
import os.path as path
import sqlite3
import subprocess
import uuid
from typing import TextIO, Dict, FrozenSet

from test_suite_information import TestSuiteInformation
from trace import Trace

TEST_METHOD_TRACES_LOG_FILENAME = 'test_method_traces.log'

logger = logging.getLogger('logger')

MAX_SIZE_FOR_TRACE_FILE_IN_MB = 100


class MavenTestTraceDbFactory(object):

    def __init__(self, test_files_list_path, project_root_path, log_file_path, output_data_root_path,
                 bug_project, bug_id: int, actual_faults_method_name_set: FrozenSet[str]):
        """
        Invoking this class will initially create the following raw data:
        ...\<test_class_name>\<test_method_name>\tmethod_info.log -
                                all method invoked during the test, and if test is faulty
        ...\<test_class_name>\<test_method_name>\test_method_traces.log -
                                all traces of methods invoked during the test

        Then, it will transform all of this data to an sql storage:
            TODO explain storage location and form

        :param bug_project:
        :param bug_id:
        :param test_files_list_path:  path to mvn .lst file that contains a list of all test files
        example: "C:\git-opensource\commons-math\target\maven-status\maven-compiler-plugin\testCompile\default-testCompile\inputFiles.lst"
        :param project_root_path: the root path for the project (e.g. "C:\git-opensource\commons-math")
        :param log_file_path: the path for the file with all of the traces (e.g. "C:\git-opensource\commons-math\traces0.log")
        :param output_data_root_path: root path to dump all data
        """
        self.bug_project = bug_project
        self.bug_id = bug_id
        self.tsuite_info = self.get_test_suit_info(test_files_list_path)
        self.project_root_path = project_root_path
        self.log_file_path = log_file_path
        assert not os.path.exists(self.log_file_path), f'log file at {self.log_file_path} exists, delete it'
        self.output_data_path = path.join(output_data_root_path, bug_project, str(bug_id))
        assert not os.path.exists(self.output_data_path), f'path {self.output_data_path} exists, clean previous data'
        self.build_raw_data()
        self.build_sqlite_db()
        self.actual_faults_method_name_set = actual_faults_method_name_set
        logger.info('done building MavenTestTraceDbFactory')

    @staticmethod
    def get_test_suit_info(test_files_list_path, filter_out_invalid=True):
        """
        :param filter_out_invalid: filters out invalid tests (@Deprecated or @Ignore)
        :return: TestSuiteInformation object with all test methods
        """
        logger.info("populating test-suit-information (get all test methods inside every test file)")
        tsuite_info = TestSuiteInformation(test_files_list_path)
        logger.info(f"found total of {len(tsuite_info.tinfos)} methods in test suit")
        if filter_out_invalid:
            logger.info("filtering out invalid tests (e.g. only @Tests without @Deprecated or @Ignore)")
            tsuite_info.filter_in_valid_tests()
            logger.info(f"total of {len(tsuite_info.tinfos)} valid test methods")
        return tsuite_info

    def invoke_individual_tests_with_tracer(self):
        # run each test to get results
        print_count = 0
        for idx, tinfo in enumerate(self.tsuite_info.tinfos):
            output = self.run_test(tinfo.tfile_name, tinfo.tmethod_name)
            tinfo.add_result_from_output(output)
            self.route_traces_to_test_folder(tinfo.tfile_name, tinfo.tmethod_name)
            if idx + 1 == print_count:
                logger.debug(f"invoked {idx +1} out of {len(self.tsuite_info.tinfos)} test methods")
                print_count = 0
            print_count += 1
        logger.debug(f"invoked 100% of all test methods")
        logger.info(f'each test class and test method tracer were stored at: "{self.output_data_path}"')

    def run_test(self, test_class_name, test_method_name):
        """
        Run a single test method, and return output
        :param test_class_name: the name of the test class, example: FunctionUtilsTest
        :param test_method_name: the name of the test method, example: testCompose
        :return: surefire output string
        """
        command = f"mvn -f={self.project_root_path}\\pom.xml surefire:test -Dtest={test_class_name}#{test_method_name}"
        command = command.split(' ')
        logger.debug(f"handling {test_class_name}, {test_method_name}")
        output = subprocess.run(command, stdout=subprocess.PIPE, shell=True, cwd=self.project_root_path)
        surefire_output = output.stdout.decode(encoding='utf-8', errors='ignore')
        return surefire_output

    def route_traces_to_test_folder(self, tfile_name, tmethod_name):
        """
        rerouting traces from the last test ran, to its relevant directory
        :param tfile_name: the name of the test class (also, file name), example: FunctionUtilsTest
        :param tmethod_name: the name of the test method, example: testCompose
        :return: None
        """
        test_dir = f"{self.output_data_path}\\{tfile_name}\\{tmethod_name}"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        os.rename(src=self.log_file_path, dst=f"{test_dir}\\test_method_traces.log")

    def create_tmethod_info_files(self):
        """
        create file with the information about the each test method
        """
        logger.info('listing all methods participated in a test')
        for tinfo in self.tsuite_info.tinfos:
            tmethod_dir_path = f"{self.output_data_path}\\{tinfo.tfile_name}\\{tinfo.tmethod_name}"
            methodset = self.get_methodset_for_tmethod_traces(tmethod_dir_path)
            with open(f"{tmethod_dir_path}\\tmethod_info.log", 'w') as tmethod_info_file:
                info = dict()
                info["methodset"] = []
                for method in methodset:
                    info["methodset"].append(method)
                info["isFaulty"] = tinfo.is_faulty
                tmethod_info_file.write(json.dumps(info))
        logger.info(
            f'tmethod info file were stored at "{self.output_data_path}\\<test_class>\\<test_method>\\methodset.log"')

    def get_methodset_for_tmethod_traces(self, tmethod_dir_path):
        """
        take all methods from this method
        :param tmethod_dir_path: path for the relevant log file
        :return: a set of the methods ran in this test
        """
        methodset = set()
        with open(f"{tmethod_dir_path}\\test_method_traces.log", 'r') as tmethod_file:
            for trace in tmethod_file:
                methodset.add(trace.split(',')[0])
        return methodset

    def build_raw_data(self):
        self.invoke_individual_tests_with_tracer()
        self.create_tmethod_info_files()

    def build_sqlite_db(self):
        logger.info(f'building bugdb at {self.output_data_path} - start')
        db = sqlite3.connect(path.join(self.output_data_path, 'bugdb.sqlite'))
        self.db_create_tables(db)
        self.db_ingest_data(db)
        self.db_create_indexes(db)

    def db_ingest_data(self, db):
        logger.info("ingesting data to db - start")
        cursor = db.cursor()
        map_from_methodfullname_to_guid = dict()
        for tinfo in self.tsuite_info.tinfos:
            if tinfo.tmethod_fullname not in map_from_methodfullname_to_guid:
                map_from_methodfullname_to_guid[tinfo.tmethod_fullname] = str(uuid.uuid4())

        # ingest outcomes
        logger.info("ingesting data to db step 1 of 3 - ingesting outcomes")
        outcomes = [(map_from_methodfullname_to_guid[tinfo.tmethod_fullname], int(tinfo.is_faulty))
                    for tinfo in self.tsuite_info.tinfos]
        cursor.executemany('''
                  INSERT INTO outcomes(tmid, is_faulty)
                  VALUES(?,?)
                  ''', outcomes)
        db.commit()

        # ingest traces
        logger.info("ingesting data to db step 2 of 3 - ingesting traces")
        # example: r"C:\personal-git\Thesis\ThesisScripts\data\**\*.log"
        generic_path_to_traces_log_file = path.join(self.output_data_path, '**', TEST_METHOD_TRACES_LOG_FILENAME)
        for logfilename in glob.iglob(generic_path_to_traces_log_file, recursive=True):
            tmid = '.'.join(logfilename.split('\\')[-3:-1])
            with open(logfilename, mode="r") as log_file:
                traces_generator = self.create_generator_from_logs(tmid, log_file, map_from_methodfullname_to_guid)
                cursor.executemany('''
                            INSERT INTO traces(tmid, mid, vector)
                            VALUES(?,?,?)
                            ''', traces_generator)
        db.commit()

        # ingest methods
        logger.info("ingesting data to db step 3 of 3 - ingesting methods")
        # flipping (method_id, method_name) intentionally
        values = [(method_id, method_name, 1) if method_name in actual_faults_method_name_set
                  else (method_id, method_name, 0)
                  for (method_name, method_id) in map_from_methodfullname_to_guid.items()]
        cursor.executemany('''
                        INSERT INTO methods(method_id, method_name, is_faulty)
                        VALUES(?,?,?)
                        ''', values)
        db.commit()

    @staticmethod
    def create_generator_from_logs(tmid: str, log_file: TextIO, map_from_methodfullname_to_guid: Dict[str, str]):
        for log in log_file:
            trace = Trace(tmid, log)
            trace.tmid = map_from_methodfullname_to_guid[trace.tmid]
            if trace.mid not in map_from_methodfullname_to_guid:
                map_from_methodfullname_to_guid[trace.mid] = str(uuid.uuid4())
            trace.mid = map_from_methodfullname_to_guid[trace.mid]
            yield (trace.tmid, trace.mid, trace.vector)

    def db_create_tables(self, db):
        logger.info('building bugdb at {self.output_data_path} - creating tables')
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE outcomes(
                tmid TEXT PRIMARY KEY, 
                is_faulty INTEGER
            )
        ''')
        db.commit()
        cursor.execute('''
            CREATE TABLE traces(
                tmid TEXT, 
                mid TEXT, 
                vector TEXT, 
                FOREIGN KEY(tmid) REFERENCES outcomes(tmid)
            )
        ''')
        db.commit()
        cursor.execute('''
            CREATE TABLE methods(
                method_id TEXT PRIMARY KEY, 
                method_name TEXT,
                is_faulty INTEGER
            )
        ''')
        db.commit()

    def db_create_indexes(self, db):
        logger.info('building bugdb at {self.output_data_path} - adding post-ingestion indexes')
        cursor = db.cursor()
        cursor.execute('''
                CREATE INDEX `idx_traces_tmids` ON `traces` (
                    `tmid`
                )
        ''')
        db.commit()
        cursor.execute('''
                CREATE INDEX `idx_traces_mids` ON `traces` (
                    `mid`
                )
        ''')
        db.commit()

