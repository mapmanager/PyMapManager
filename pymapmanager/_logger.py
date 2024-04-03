import logging
import os
import sys

from logging.handlers import RotatingFileHandler

from platformdirs import user_data_dir  # to get log path

def setLogLevel(newLogLevel : str = 'INFO'):
    """Set the global loggin level.
    
    Can update this during runtime and all logs will follow the level.
    """
    logger = logging.getLogger(__name__)

    logger.info(f'setLogLevel() newLogLevel "{newLogLevel}"')
    logger.info(f'   logging to file: {getLoggerFilePath()}')

    if newLogLevel == 'DEBUG':
        logLevel = logging.DEBUG
    elif newLogLevel == 'INFO':
        logLevel = logging.INFO
    elif newLogLevel == 'WARNING':
        logLevel = logging.WARNING
    elif newLogLevel == 'ERROR':
        logLevel = logging.ERROR
    elif newLogLevel == 'CRITICAL':
        logLevel = logging.CRITICAL
    else:
        errStr  = f'did not understand new log level "{newLogLevel}"'
        logger.error(errStr)
        return
    
    logger.setLevel(logLevel)

def getLoggerFilePath():
    """Get the full path to the log file using platformdirs.
    """
    appName = 'MapManager'
    appDir = user_data_dir(appName)
    logFilePath = os.path.join(appDir, 'mapmanager.log')
    return logFilePath

# Create a custom logger with the name as the module name
logger = logging.getLogger(__name__)

handler = logging.StreamHandler(sys.stdout)

logFilePath = getLoggerFilePath()
f_handler = RotatingFileHandler(logFilePath, maxBytes=2e6, backupCount=1)

# I want the class name of the caller
# this gives us the filename _lologger()
# [%(name)s()]
# [%(module)s()]
#formatter = logging.Formatter('%(levelname)7s - [%(module)s()] %(filename)s %(funcName)s() line:%(lineno)d -- %(message)s')
formatter = logging.Formatter('%(levelname)7s - %(filename)s %(funcName)s() line:%(lineno)d -- %(message)s')
handler.setFormatter(formatter)
f_handler.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(f_handler)
