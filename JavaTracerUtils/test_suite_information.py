"""
Describes a test suite
"""
from pathlib import Path
from typing import List

from java_testclass_parser import JavaTestClassFileParser
from test_info import TestInfo
import os
import logging
from shutil import rmtree

logger = logging.getLogger('logger')


class TestSuiteInformation(object):
    def __init__(self, tfiles_list_path):
        '''
        This class holds all of the information from the test suite.
        This constructor, analyzes the test suite files (classes) create a TestInfo instance for each test method,
        together with its proper annotations (e.g. @Ignore)

        :param tfiles_list_path: path to mvn .lst file that contains a list of all test files
        example: "commons-math\target\maven-status\maven-compiler-plugin\testCompile\default-testCompile\inputFiles.lst"
        '''
        print_count = 0
        abstract_count = 0
        self.tinfos = []
        with open(tfiles_list_path, "r") as tfiles_paths:
            tfile_paths_list = list(tfiles_paths)
            for idx, tfile_path in enumerate(tfile_paths_list):
                tfile_path = tfile_path.rstrip('\n')
                tfile_name = Path(tfile_path).stem
                if tfile_name.endswith('AbstractTest'):
                    abstract_count += 1
                    continue
                tmethodnameTannotations = JavaTestClassFileParser.parse_and_return_methodnameTannotations(tfile_path)
                for (tmethod_name, annotations) in tmethodnameTannotations:
                    self.tinfos.append(TestInfo(tfile_path, tfile_name, tmethod_name, annotations))
                if print_count == 20:
                    logger.debug(f"processed {idx +1} out of {len(tfile_paths_list)} test files information")
                    print_count = 0
                print_count += 1
        logger.debug(f"ignored {abstract_count} abstract test classes")
        logger.debug(f"added {len(self.tinfos)} test files information")

    def filter_in_valid_tests(self, additional_classes_to_filter: List[str]):
        tinfos_filtered = []
        for tinfo in self.tinfos:
            isTest = 'Test' in tinfo.tannotations
            isDeprecated = 'Deprecated' in tinfo.tannotations
            isIgnore = 'Ignore' in tinfo.tannotations
            isConfiguredToBeIgnored = tinfo.tfile_name in additional_classes_to_filter
            if isTest and not isDeprecated and not isIgnore and not isConfiguredToBeIgnored:
                tinfos_filtered.append(tinfo)
        self.tinfos = tinfos_filtered

    @DeprecationWarning
    def filter_out_big_trace_files(self, max_size_in_mb):
        deleted_count = 0
        for (idx, tinfo) in enumerate(self.tinfos):
            tmethod_dir_path = f"{self.data_path}\\{tinfo.tfile_name}\\{tinfo.tmethod_name}"
            traces_file_path = f"{tmethod_dir_path}\\test_method_traces.log"
            statinfo = os.stat(traces_file_path)
            size_b = statinfo.st_size
            size_mb = (size_b >> 20)
            logger.info(f"{traces_file_path} size: {size_mb} MB, max size allowed: {max_size_in_mb}")
            if size_mb > max_size_in_mb:
                deleted_count += 1
                logger.info(f"deleting {traces_file_path}. size: {size_mb} MB, max size allowed: {max_size_in_mb}")
                rmtree(tmethod_dir_path)
                del self.tsuite_info.tinfos[idx]
        return deleted_count

    def remove_wrongly_executed_test(self):
        count = 0
        for tinfo in self.tinfos:
            if tinfo.wrongly_executed:
                self.tinfos.remove(tinfo)
                count += 1
        return count