"""
This class represents a single test method and its result
"""
import re


class TestInfo(object):
    """
    This class represents a single test method and its result
    """
    def __init__(self, tfile_full_path, tfile_name, tmethod_name, tannotations_lst):
        self.tfile_full_path = tfile_full_path
        self.tfile_name = tfile_name
        self.tmethod_name = tmethod_name
        self.tmethod_fullname = f"{tfile_name}.{tmethod_name}"  # class_name.method_name
        self.packages_class_method_fullname = '.'.join(tfile_full_path.replace('\\','.').split('.')[-4:-1]) \
                                              + '.' + tmethod_name
        self.tannotations = tannotations_lst
        self.is_faulty = None

    def add_result_from_output(self, test_output_str_result):
        """
        :param test_output_str_result: output given by `surefire` when running this single test
        :return:
        """
        result_idx = test_output_str_result.rfind("Tests run: 1")
        if result_idx == -1:
            print("WARNING - unexpected result from mvn surefire")
            print(test_output_str_result)
            print("WARNING- unexpected result from mvn surefire")
            self.is_faulty = False
            return
        result_dirty = test_output_str_result[result_idx:]
        result = result_dirty[:result_dirty.find('\n')]
        result_vector = re.findall('\\b\\d+\\b', result)  # ['1', '0', '0', '0']
        result_vector = list(map(int, result_vector))
        num_of_tests, failures, errors, skipped = result_vector[0], result_vector[1], result_vector[2], result_vector[3]
        assert num_of_tests < 2  # expecting only 1 test, allowing zero
        self.is_faulty = (failures + errors > 0)  # failed tests often result in an error
        assert skipped == 0  # test was skipped
