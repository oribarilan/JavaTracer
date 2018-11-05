class Config:
    # region bug configurations
    PROJECT_ROOT_PATH = r"/Users/ori/pergit/defects/math_1_buggy"
    BUG_PROJECT = 'math'
    BUG_ID = 1
    IGNORED_CLASS_LIST = ['FastCosineTransformerTest', 'FastSineTransformerTest', 'FastMathStrictComparisonTest',
                          'CorrelatedRandomVectorGeneratorTest', 'FastMathTestPerformance']
    # this requires complete names: <package>.<class>.<method>(parameters)
    # example: 'fraction.BigFraction.BigFraction(double_double_int_int)'
    # another example: 'org.apache.commons.lang3.math.NumberUtils.createNumber(java.lang.String)'
    actual_faults_method_fullname_set = frozenset(
        {
            'fraction.BigFraction.BigFraction(double_double_int_int)',
            'fraction.Fraction.Fraction(double_double_int_int)'
        })
    ON_THE_FLY = True  # don't create intermediate files -> this improves performance
    # endregion

    DEBUG = False
    FAIL_SAMPLE_RATE = 1.00
    SUCCESS_SAMPLE_RATE = 1.00

    # this will NOT override the ON_THE_FLY flag nor sampling rates -> will only sample traces from faulty methods
    # use `True` only when `actual_faults_method_fullname_set` is properly set
    SAMPLE_ONLY_ACTUAL_FAULTY_METHODS = True
