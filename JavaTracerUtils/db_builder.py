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
from typing import TextIO, Dict, FrozenSet, List
from test_info import TestInfo
from queue import Queue

from test_suite_information import TestSuiteInformation
from trace import Trace
from os import path

TEST_METHOD_TRACES_LOG_FILENAME = 'test_method_traces.log'

logger = logging.getLogger('logger')

MAX_SIZE_FOR_TRACE_FILE_IN_MB = 100


class MavenTestTraceDbFactory(object):

    def __init__(self, test_files_list_path, project_root_path, log_file_path, output_data_root_path,
                 bug_project, bug_id: int, actual_faults_method_fullname_set: FrozenSet[str],
                 on_the_fly: bool, bug_configurations_to_log: Dict[str, str],
                 fail_sample_rate: float, success_sample_rate: float,
                 ignored_test_files: List[str], is_sample_only_faulty: bool):
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
        :param actual_faults_method_fullname_set: a frozenset of the real faulty methods (full names)
        """
        # define
        self.ignored_test_files = ignored_test_files
        self.bug_project = bug_project
        self.bug_id = bug_id
        self.tsuite_info = self.get_test_suit_info(test_files_list_path)
        self.project_root_path = project_root_path
        self.log_file_path = log_file_path
        assert not os.path.exists(self.log_file_path), f'log file at {self.log_file_path} exists, delete it'
        self.output_data_path = path.join(output_data_root_path, bug_project, str(bug_id))
        self.bug_db_path = path.join(self.output_data_path, 'bugdb.sqlite')
        assert not os.path.exists(self.bug_db_path), f'path {self.bug_db_path} exists, clean previous bugdb'
        self.actual_faults_method_fullname_set = actual_faults_method_fullname_set
        self.map_from_methodfullname_to_guid = dict()
        self.fail_sample_rate = fail_sample_rate
        self.success_sample_rate = success_sample_rate
        self.is_sample_only_faulty = is_sample_only_faulty
        # prepare
        if not os.path.exists(self.output_data_path):
            os.makedirs(self.output_data_path)

        # build
        logger.info(f'building bugdb at {self.output_data_path} - start')

        self.db = self.db_init(bug_configurations_to_log)

        self.db_create_tables()
        # traces and outcomes
        self.invoke_individual_tests_with_tracer(on_the_fly)
        if not on_the_fly:
            self.db_ingest_data_from_intermediate_files()
        # methods index
        self.db_ingest_methods()
        self.db_create_indexes()

        self.db.close()
        logger.info('done building MavenTestTraceDbFactory')

    def set_tracer_sample_rate(self, sample_rate: float):
        config_file_name = "agent_config.cfg"
        config_path = path.join(self.project_root_path, config_file_name)
        assert path.exists(config_path), f"missing config: {config_path}"
        with open(config_path, "w") as cfg:
            cfg.write(str(sample_rate))

    def db_init(self, bug_configurations_to_log):
        db = sqlite3.connect(path.join(self.bug_db_path))
        cursor = db.cursor()
        cursor.execute('PRAGMA synchronous = OFF')
        cursor.execute('PRAGMA journal_mode = OFF')  # disable logging for performance

        cursor.execute('''
            CREATE TABLE metadata(
                name TEXT, 
                value TEXT
            )
        ''')

        cursor.executemany('''
                  INSERT INTO metadata(name, value)
                  VALUES(?,?)
                  ''', bug_configurations_to_log.items())

        db.commit()
        cursor.close()

        return db

    def get_test_suit_info(self, test_files_list_path, filter_out_invalid=True):
        """
        :param filter_out_invalid: filters out invalid tests (@Deprecated or @Ignore)
        :return: TestSuiteInformation object with all test methods
        """
        logger.info("populating test-suit-information (get all test methods inside every test file)")
        tsuite_info = TestSuiteInformation(test_files_list_path)
        logger.info(f"found total of {len(tsuite_info.tinfos)} methods in test suit")
        if filter_out_invalid:
            logger.info("filtering out invalid tests (e.g. only @Tests without @Deprecated or @Ignore)")
            tsuite_info.filter_in_valid_tests(additional_classes_to_filter=self.ignored_test_files)
            logger.info(f"total of {len(tsuite_info.tinfos)} valid test methods")
        return tsuite_info

    def invoke_individual_tests_with_tracer(self, on_the_fly: bool):
        run_once = self.fail_sample_rate == self.success_sample_rate
        if run_once:
            logger.info("Fail and Success sample rates are the same, running once on all tests")
            total = len(self.tsuite_info.tinfos)
            self.set_tracer_sample_rate(sample_rate=self.fail_sample_rate)
            for idx, tinfo in enumerate(self.tsuite_info.tinfos):
                logger.debug(f"{idx+1}/{total}\t\t: handling {tinfo.tfile_name}, {tinfo.tmethod_name} [PASSING]")
                assert not os.path.isfile(self.log_file_path), "log file should not exists before running individual test"
                output = self.run_test(tinfo.tfile_name, tinfo.tmethod_name)
                tinfo.add_result_from_output(output)
                if on_the_fly:
                    self.db_ingest_test_to_bugdb(tinfo)
                else:
                    self.route_traces_to_test_folder(tinfo.tfile_name, tinfo.tmethod_name)
        else:
            # run each test to get results
            total = len(self.tsuite_info.tinfos)
            self.set_tracer_sample_rate(sample_rate=0.0)
            # 1 - run with 0 sample rate, just to check if test failed or pass
            for idx, tinfo in enumerate(self.tsuite_info.tinfos):
                logger.debug(f"{idx+1}/{total}\t\t: checking {tinfo.tfile_name}, {tinfo.tmethod_name}")
                output = self.run_test(tinfo.tfile_name, tinfo.tmethod_name)
                tinfo.add_result_from_output(output)

            if os.path.isfile(self.log_file_path): #TODO file should not be here, assert instead of check
                logger.warning(f"deleting log_file at {self.log_file_path}")
                os.remove(self.log_file_path)

            count = self.tsuite_info.remove_wrongly_executed_test()
            logger.debug(f"{count} tests could not be invoked properly (deleted)")

            # 2 - run again with the relevant sample rate
            passing_tests = [tinfo for tinfo in self.tsuite_info.tinfos if not tinfo.is_faulty]
            self.set_tracer_sample_rate(sample_rate=self.success_sample_rate)
            for idx, tinfo in enumerate(passing_tests):
                logger.debug(f"{idx+1}/{len(passing_tests)}\t\t: handling {tinfo.tfile_name}, {tinfo.tmethod_name} [PASSING]")
                assert not os.path.isfile(self.log_file_path), "log file should not exists before running individual test"
                self.run_test(tinfo.tfile_name, tinfo.tmethod_name)
                if on_the_fly:
                    self.db_ingest_test_to_bugdb(tinfo)
                else:
                    self.route_traces_to_test_folder(tinfo.tfile_name, tinfo.tmethod_name)

            failing_tests = [tinfo for tinfo in self.tsuite_info.tinfos if tinfo.is_faulty]
            self.set_tracer_sample_rate(sample_rate=self.fail_sample_rate)
            for idx, tinfo in enumerate(failing_tests):
                logger.debug(f"{idx+1}/{len(failing_tests)}\t\t: handling {tinfo.tfile_name}, {tinfo.tmethod_name} [FAILING]")
                assert not os.path.isfile(self.log_file_path), "log file should not exists before running individual test"
                self.run_test(tinfo.tfile_name, tinfo.tmethod_name)
                if on_the_fly:
                    self.db_ingest_test_to_bugdb(tinfo)
                else:
                    self.route_traces_to_test_folder(tinfo.tfile_name, tinfo.tmethod_name)

        logger.debug(f"invoked 100% of all test methods")
        logger.info(f'each test class and test method tracer were stored at: "{self.output_data_path}"')

    def run_test(self, test_class_name, test_method_name):
        """
        Run a single test method, and return output
        :param test_class_name: the name of the test class, example: FunctionUtilsTest
        :param test_method_name: the name of the test method, example: testCompose
        :return: surefire output string
        """
        command = f"mvn surefire:test -f={path.join(self.project_root_path, 'pom.xml')} -Dtest={test_class_name}#{test_method_name}"
        logger.info(f"executing command: {command}")
        # windows:
        # command = command.split(' ')
        # output = subprocess.run(command, stdout=subprocess.PIPE, shell=True, cwd=self.project_root_path)
        # output = output.stdout
        # mac:
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, cwd=self.project_root_path)
        stdout, stderr = p.communicate()
        surefire_output = stdout.decode(encoding='utf-8', errors='ignore')

        return surefire_output

    def db_ingest_test_to_bugdb(self, tinfo: TestInfo):
        cursor = self.db.cursor()
        if tinfo.packages_class_method_fullname not in self.map_from_methodfullname_to_guid:
            self.map_from_methodfullname_to_guid[tinfo.packages_class_method_fullname] = self.gen_method_id()

        # ingest outcomes
        outcomes = (self.map_from_methodfullname_to_guid[tinfo.packages_class_method_fullname], int(tinfo.is_faulty))
        cursor.execute('''
                  INSERT INTO outcomes(tmid, is_faulty)
                  VALUES(?,?)
                  ''', outcomes)

        # ingest traces
        if os.path.exists(self.log_file_path):
            with open(self.log_file_path, mode="r") as log_file:
                traces_generator = self.create_generator_from_logs(tinfo.packages_class_method_fullname, log_file,
                                                                   self.is_sample_only_faulty)
                cursor.executemany('''
                            INSERT INTO traces(tmid, mid, vector)
                            VALUES(?,?,?)
                            ''', traces_generator)
        else:
            logger.warning('log file was not created (probably due to random sampling)')
        self.db.commit()
        cursor.close()

        # remove log file
        if os.path.isfile(self.log_file_path):
            os.remove(self.log_file_path)
        else:
            logger.warning(f"log file is missing but should exists at {self.log_file_path}")


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
        if os.path.exists(self.log_file_path):  # could be missing if agent sampling is ON
            os.rename(src=self.log_file_path, dst=f"{test_dir}\\test_method_traces.log")

    def create_tmethod_info_files(self):
        """
        TODO delete this
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

    def db_ingest_data_from_intermediate_files(self):
        logger.info("ingesting data to db - start")
        cursor = self.db.cursor()
        for tinfo in self.tsuite_info.tinfos:
            if tinfo.packages_class_method_fullname not in self.map_from_methodfullname_to_guid:
                self.map_from_methodfullname_to_guid[tinfo.packages_class_method_fullname] = self.gen_method_id()

        # ingest outcomes
        logger.info("ingesting data to db step 1 of 3 - ingesting outcomes")
        outcomes = [(self.map_from_methodfullname_to_guid[tinfo.packages_class_method_fullname], int(tinfo.is_faulty))
                    for tinfo in self.tsuite_info.tinfos]
        cursor.executemany('''
                  INSERT INTO outcomes(tmid, is_faulty)
                  VALUES(?,?)
                  ''', outcomes)

        # ingest traces
        logger.info("ingesting data to db step 2 of 3 - ingesting traces")
        # example: r"C:\personal-git\Thesis\ThesisScripts\data\**\*.log"
        generic_path_to_traces_log_file = path.join(self.output_data_path, '**', TEST_METHOD_TRACES_LOG_FILENAME)
        for logfilename in glob.iglob(generic_path_to_traces_log_file, recursive=True):
            tmid_name = '.'.join(logfilename.split('\\')[-3:-1])
            with open(logfilename, mode="r") as log_file:
                traces_generator = self.create_generator_from_logs(tmid_name, log_file,
                                                                   self.is_sample_only_faulty)
                cursor.executemany('''
                            INSERT INTO traces(tmid, mid, vector)
                            VALUES(?,?,?)
                            ''', traces_generator)
        self.db.commit()
        cursor.close()

    @staticmethod
    def is_test_method(method_name: str) -> bool:
        # in rare-cases test name might start with a capital T
        return method_name.lower().rfind('.test') > -1

    def db_ingest_methods(self):
        values = []
        for (method_name, method_id) in self.map_from_methodfullname_to_guid.items():
            if method_name in self.actual_faults_method_fullname_set:
                is_true_fault = 1
            else:
                is_true_fault = 0

            if self.is_test_method(method_name):
                is_test_method = 1
            else:
                is_test_method = 0
            values.append((method_id, method_name, is_true_fault, is_test_method))

        cursor = self.db.cursor()
        logger.info("ingesting data to db step 3 of 3 - ingesting methods")
        cursor.executemany('''
                        INSERT INTO methods(method_id, method_name, is_real_faulty, is_test_method)
                        VALUES(?,?,?,?)
                        ''', values)
        self.db.commit()
        cursor.close()

    def gen_method_id(self):
        # there is no need to use the whole guid
        uuid_split = str(uuid.uuid4()).split('-')
        short_uuid = uuid_split[0] + uuid_split[1]
        return short_uuid

    def create_generator_from_logs(self, tmid_name: str, log_file: TextIO, generate_only_faulty_method_traces: bool):
        '''
        :param tmid_name: identifier for the test method, example: 'BigFractionFormatTest.testDenominatorFormat'
        :param log_file: file handler for the log file
        :param generate_only_faulty_method_traces: wiil only generate traces for faulty methods
        :return:
        '''
        for log in log_file:
            trace = Trace(tmid_name, log)
            if generate_only_faulty_method_traces and trace.mid_name not in self.actual_faults_method_fullname_set:
                continue
            trace.tmid_guid = self.map_from_methodfullname_to_guid[trace.tmid_name]
            if trace.mid_name not in self.map_from_methodfullname_to_guid:
                self.map_from_methodfullname_to_guid[trace.mid_name] = self.gen_method_id()
            trace.mid_guid = self.map_from_methodfullname_to_guid[trace.mid_name]
            yield (trace.tmid_guid, trace.mid_guid, trace.vector)

    def db_create_tables(self):
        logger.info('building bugdb at {self.output_data_path} - creating tables')
        cursor = self.db.cursor()
        cursor.execute('''
            CREATE TABLE outcomes(
                tmid TEXT PRIMARY KEY, 
                is_faulty INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE traces(
                tmid TEXT, 
                mid TEXT, 
                vector TEXT, 
                FOREIGN KEY(tmid) REFERENCES outcomes(tmid)
            )
        ''')
        cursor.execute('''
            CREATE TABLE methods(
                method_id TEXT PRIMARY KEY, 
                method_name TEXT,
                is_real_faulty INTEGER,
                is_test_method INTEGER
            )
        ''')
        self.db.commit()
        cursor.close()

    def db_create_indexes(self):
        logger.info('building bugdb at {self.output_data_path} - adding post-ingestion indexes')
        cursor = self.db.cursor()
        cursor.execute('''
                CREATE INDEX `idx_traces_tmids` ON `traces` (
                    `tmid`
                )
        ''')
        cursor.execute('''
                CREATE INDEX `idx_traces_mids` ON `traces` (
                    `mid`
                )
        ''')
        cursor.execute('''
                CREATE INDEX `idx_methods_isfaulty` ON `methods` (
                    `is_real_faulty`
                )
        ''')
        cursor.execute('''
                CREATE INDEX `idx_methods_istest` ON `methods` (
                    `is_test_method`
                )
        ''')
        self.db.commit()
        cursor.close()

