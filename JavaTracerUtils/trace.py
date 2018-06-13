class Trace(object):
    def __init__(self, tmid_name: str, trace_str: str):
        trace_str = trace_str.rstrip('\n')
        trace_str = trace_str.rstrip('\r')
        self.tmid_name = tmid_name
        self.tmid_guid = None
        self.mid_name = trace_str[:trace_str.find(',')]
        self.mid_guid = None
        self.vector = trace_str[trace_str.find(',')+1:]