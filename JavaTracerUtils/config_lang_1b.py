class Config:
    # region bug configurations
    PROJECT_ROOT_PATH = r"/Users/ori/pergit/defects/lang_1_buggy"
    BUG_PROJECT = 'lang'
    BUG_ID = 1
    IGNORED_CLASS_LIST = ['FastDateFormatTest', 'ExtendedMessageFormatTest']
    # this requires complete names: <package>.<class>.<method>(parameters)
    # example: 'fraction.BigFraction.BigFraction(double_double_int_int)'
    # another example: 'org.apache.commons.lang3.math.NumberUtils.createNumber(java.lang.String)'
    actual_faults_method_fullname_set = frozenset({'org.apache.commons.lang3.math.NumberUtils.createNumber(java.lang.String)'})
    ON_THE_FLY = True  # don't create intermediate files -> this improves performance
    # endregion

    DEBUG = False
    FAIL_SAMPLE_RATE = 1.00
    SUCCESS_SAMPLE_RATE = 1.00
