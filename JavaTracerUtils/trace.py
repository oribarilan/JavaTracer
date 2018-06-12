class Trace(object):
    def __init__(self, tmid: str, trace_str: str):
        trace_str = trace_str.rstrip('\n')
        trace_str = trace_str.rstrip('\r')
        self.tmid = tmid
        self.mid = trace_str[:trace_str.find(',')]
        self.vector = trace_str[trace_str.find(',')+1:]