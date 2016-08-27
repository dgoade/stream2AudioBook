__author__ = 'dgoade'

import sys
import logging
from utils.workingDir import workingDir
from logging.config import dictConfig

class loggingConfigurator():

    logger = None

    default_config = {
        # begin my additional keys to the logging config dictionary
        "log_dir": "logs",
        # end my additional keys to the logging config dictionary
        "version": 1,
        "formatters": {
            "simple": {
                "format": "%(asctime)s -"
                " %(name)s - %(levelname)s -"
                " %(message)s"
              }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
              },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "WARN",
                "formatter": "simple",
                "stream": "ext://sys.stderr"
          },
          # for now the default config will not log to a file
          #"file": {
          #  "class": "logging.handlers.RotatingFileHandler",
          #  "formatter": "simple",
          #  "filename": "logs/recoder.log",
          #  "mode": "a",
          #  "maxBytes": 12000,
          #  "backupCount": 5
          #}
        },
        "loggers": {
            "utils": {
                "level": "DEBUG",
                "handlers": [
                    "console"
                ],
                "propagate": False
            },
            "utils.loggingConfigurator": {
                "level": "DEBUG",
                "handlers": [
                    "console"
                ],
                "propagate": False
            },
            "utils.loggingConfigurator.__init__": {
                "level": "WARN",
                "handlers": [
                    "console"
                ],
                "propagate": False
            },
            "utils.loggingConfigurator.reconfigure_logging": {
                "level": "DEBUG",
                "handlers": [
                    "console"
                ],
                "propagate": False
            },
            "utils.loggingConfigurator.set_log_dir": {
                "level": "DEBUG",
                "handlers": [
                "console"
                ],
                "propagate": False
            }
        },
        "root": {
            "level": "DEBUG",
        }
    }

    def __init__(self, logging_config = None):

        rval = True
        logger_name = '{0}.__init__'.format(__name__)

        try:
            log_msg = "Loading default logging config"
            self.log_it('debug', log_msg)
            dictConfig(self.default_config)

        except Exception as e:
            sys.stderr.write('%s\n' % e)
            log_msg = "Failed to configure logging from default config"
            sys.stderr.write(log_msg)
            rval = False

        if rval:
            logger = logging.getLogger(logger_name)
            log_msg = "Now using default logging"
            logger.debug(log_msg)
        else:
            rval = True
            log_msg = "Attempting basic logging config"
            self.log_it('debug', log_msg)
            try:
                logging.basicConfig(stream=sys.stdout,
                                    level=logging.DEBUG,
                                    format="%(asctime)s - "
                                    "%(name)s - "
                                    "%(levelname)s - "
                                    "%(message)s")
                logger = logging.getLogger(logger_name)
                log_msg = "Now logging to stdout with basic logging config."
                logger.info(log_msg)

            except Exception as e:
                sys.stderr.write('%s\n' % e)
                log_msg = "Failed to configure logging using basicConfig"
                log_msg = " -- no logging is possible!"
                sys.stderr.write(log_msg)
                rval = False

        if rval:
            self.set_log_dir(self.default_config)

    def set_log_dir(self, logging_config):

        rval = True
        logger_name = '{0}.set_log_dir'.format(__name__)
        logger = logging.getLogger(logger_name)

        if 'log_dir' in logging_config:
            log_msg = "log_dir={0}".format(logging_config['log_dir'])
            logger.debug(log_msg)
        else:
            log_msg = "No log_dir defined in config"
            logger.error(log_msg)
            rval = False

        if rval:
            if logging_config['log_dir']:
                working_dir = workingDir()
                working_dir.verify_dir(dir_desc = 'log dir',
                                       dir_name = logging_config['log_dir'])

        return rval

    def reconfigure_logging(self, logging_config = None):

        rval = True
        logger_name = '{0}.reconfigure_logging'.format(__name__)
        logger = logging.getLogger(logger_name)

        if logging_config:
            log_msg = "Logging config was passed so loading it."
            logger.debug(log_msg)

            try:
                dictConfig(logging_config)

            except Exception:
                log_msg = "Failed to configure logging from passed dict"
                " -- using default config.\n"
                logger.exception(log_msg)
        else:
            log_msg = "No logging config was passed so just using"
            " default logging config."
            logger.debug(log_msg)

        return rval

    def log_it(self, log_level, log_msg):

        if self.logger:
            # this way, we can call any logging
            # method from this little wrapper as
            # long as there is a logging method
            # name that matches the log_level arg
            logging_method = getattr(self.logger, log_level)
            logging_method(log_msg)
            #self.logger.debug(log_msg)
        else:
            print log_msg
