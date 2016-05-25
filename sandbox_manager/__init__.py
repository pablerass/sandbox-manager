"""Module to deploy dynamic instances into an iaas.

This library should be configured properly before its use.
"""
import __main__
import logging
import logging.config
import os
import sys

__version__ = '1.0b1'

# Application paths
BASE_DIR = '/opt/sandbox_manager'
CONF_DIR = os.path.join(BASE_DIR, 'conf')
TMP_DIR = os.path.join(BASE_DIR, 'tmp')
LOG_DIR = os.path.join(BASE_DIR, 'log')
VAR_DIR = os.path.join(BASE_DIR, 'var')

# Logging configuration
DEBUG_LOG_FILE = os.path.join(LOG_DIR, 'debug.log')
MAIN_LOG_FILE = os.path.join(LOG_DIR, 'main.log')

LOGGING_DICT = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)-7s - %(name)s - %(message)s',
            'datefmt': '%Y/%m/%d %H:%M:%S',
        },
        'simple': {
            'format': '%(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'file_last': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': DEBUG_LOG_FILE,
            'encoding': 'utf-8',
            'maxBytes': 5120000,
            'backupCount': 10,
        },
        'file_perm': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'verbose',
            'filename': MAIN_LOG_FILE,
            'encoding': 'utf-8',
            'interval': 1,
            'when': 'midnight',
            'backupCount': 30,
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'sb-mgr': {
            'level': 'DEBUG',
            'handlers': ['file_perm', 'file_last', 'console'],
        },
        'requests': {
            'level': 'DEBUG',
            'handlers': ['file_last'],
        }
    }
}

# TODO: This is dirty, dirty
if 'unittest' not in sys.modules:
    try:
        logging.config.dictConfig(LOGGING_DICT)
    except ValueError as e:
        del LOGGING_DICT['handlers']['file_last']
        del LOGGING_DICT['handlers']['file_perm']
        del LOGGING_DICT['loggers']['requests']
        LOGGING_DICT['loggers']['sb-mgr']['handlers'] = ['console']
        logging.config.dictConfig(LOGGING_DICT)

        logger = logging.getLogger('sb-mgr')
        logger.error('Unable to create log files, logging only to console')
