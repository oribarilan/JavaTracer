import rarfile
import logging
import sys
import collections
import pickle
import glob

log_format = '[%(asctime)s]|| [%(levelname)s]: %(message)s'
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_console_channel = logging.StreamHandler(sys.stdout)
log_console_channel.setLevel(logging.DEBUG)
logger.addHandler(log_console_channel)

#iterating zip files with traces text files
def traceToFuncName(trace):
    return trace.split(',',1)[0]

def bytesToStr(bs):
    return bs.decode("utf-8")

def bytesTraceToFuncName(bs):
    return traceToFuncName(bytesToStr(bs))

counter = collections.Counter()
logger.info("start")
for rfname in glob.glob("*.rar"):
    logger.info('accessing rar file: %s', rfname)
    with rarfile.RarFile(rfname) as rf:
        for finfo in rf.infolist():
            logger.info('updating counter for trace file: %s', finfo.filename)
            with rf.open(finfo.filename) as f:
                counter.update(map(bytesTraceToFuncName, f))

logging.info("done updating counter")
logging.info("pickeling counter")
with open('counter.pkl', 'wb') as picklef:
    pickle.dump(counter, picklef)
logging.info("done pickeling counter")
logging.info("most comming 5 methods:")
logging.info(counter.most_common(5))