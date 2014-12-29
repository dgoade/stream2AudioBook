__author__ = 'dgoade'

import sys
import os.path
import logging

class Working_dir():

    def __init__(self, dir_name, logging_dict = None ):

        if logging_dict:
            logger = logging.getLogger('Working_dir.{0}.__init__'.format(__name__))
            log_msg = 'Logging config dictionary passed so using logging'
            logger.debug(log_msg)
        else:
            log_msg = "No logging config dictionary passed to using print"
            print log_msg

#        if dir_name:
#            log_msg = 'verifying output dir at {0}'.format(test_dir)
#            logger.debug(log_msg)
#
#            if os.path.isdir(test_dir):
#                log_msg = 'output dir exists at {0}'.format(test_dir)
#                logger.debug(log_msg)
#                self.output_dir = test_dir
#            else:
#                log_msg1 = 'output dir does not exist at {0}'
#                log_msg2 = 'so creating it'.format(test_dir)
#                log_msg = '{0} {1}'.format(log_msg1, log_msg2)
#                logger.debug(log_msg)
#                try:
#                    os.makedirs(test_dir)
#                    self.output_dir = test_dir
#                    log_msg = 'output dir created successfully'
#                    logger.debug(log_msg)
#                except OSError as exception:
#                    log_msg1 = 'Exception occurred trying to create'
#                    log_msg2 = 'output dir: {0}'.format(test_dir)
#                    log_msg = '{0} {1}'.format(log_msg1, log_msg2)
#                    logger.exception(log_msg)
#                    rval = False
#        else:
#            log_msg1 = 'No output dir configured. Add an output_dir'
#            log_msg2 = 'setting to the config file to specify one.'
#            log_msg = '{0} {1}'.format(log_msg1, log_msg2)
#            logger.debug(log_msg)
#            log_msg1 = 'No output dir configured. All output will'
#            log_msg2 = 'be sent to the current dir.'
#            log_msg = '{0} {1}'.format(log_msg1, log_msg2)
#            logger.warn(log_msg)
