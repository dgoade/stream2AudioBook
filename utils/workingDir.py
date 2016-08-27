__author__ = 'dgoade'

import sys
import os.path
import logging

class workingDir():

    logger = None

    def __init__(self, logging_dict = None ):

        rval = True
        logger_name = '{0}.__init__'.format(__name__)
        logger = logging.getLogger(logger_name)

    def verify_dir(self, **kwargs):

        rval = True
        logger_name = '{0}.verify_working_dir'.format(__name__)
        logger = logging.getLogger(logger_name)

        if 'dir_name' in kwargs:
            dir_name = kwargs['dir_name']

        if 'dir_desc' in kwargs:
            dir_desc = kwargs['dir_desc']
        else:
            dir_desc = "working dir"

        if dir_name:
            log_msg = 'verifying {0}: {1}'.format(dir_desc, dir_name)
            logger.debug(log_msg)

            if os.path.isdir(dir_name):
                log_msg = '{0} exists: {1}'.format(dir_desc, dir_name)
                logger.debug(log_msg)
            else:
                log_msg = 'creating {0}: {1}'.format(dir_desc, dir_name)
                logger.debug(log_msg)
                try:
                    os.makedirs(dir_name)
                    log_msg = '{0} created: {0}'.format(dir_desc, dir_name)
                    logger.debug(log_msg)
                except OSError as exception:
                    log_msg = ("Exception occurred trying to create"
                    "{0}: {1}".format(dir_desc, dir_name))
                    logger.exception(log_msg)
                    rval = False
        else:
            log_msg = 'No {0} passed -- doing nothing.'.format(dir_desc)
            logger.debug(log_msg)

        return rval
