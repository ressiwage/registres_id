import logging, logging.config
from logging import StreamHandler, Formatter
import colorstreamhandler, sys



_LOGCONFIG = {
     "version": 1,
     "disable_existing_loggers": False,
 
     "handlers": {
         "console": {
             "class": "colorstreamhandler.ColorStreamHandler",
             "stream": "ext://sys.stderr",
             "level": "INFO"
         }
     },
 
     "root": {
         "level": "INFO",
         "handlers": ["console"]
     }
 }
 


def get_logger(name):
    
    logging.config.dictConfig(_LOGCONFIG)
    mylogger = logging.getLogger(name)
    mylogger.setLevel(logging.DEBUG)
    
    
    return mylogger