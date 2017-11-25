import sqlite3
import os
import logging
import sys

log_format = '[%(asctime)s] {0}|| [%(levelname)s]: %(message)s'
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_console_channel = logging.StreamHandler(sys.stdout)
log_console_channel.setLevel(logging.DEBUG)
logger.addHandler(log_console_channel)

## db setup

DB_PATH = 'database/tracesdb'
logger.info("setting up new traces db at '%s'", DB_PATH)
if os.path.isfile(DB_PATH):
    os.remove(DB_PATH)
    logger.info("reomved previous traces db at '%s'", DB_PATH)
db = sqlite3.connect(DB_PATH)
logger.info("db connected to '%s'", DB_PATH)


