__author__ = 'dgoade'

import sys
import re
import os.path
import logging
from pprint import pformat

class audioFileInfo():

    logger = None
    file_prefix = "Radio"

    def __init__(self, logging_dict = None ):

        rval = True
        logger_name = '{0}.__init__'.format(__name__)
        logger = logging.getLogger(logger_name)

    def get_audio_file_info(self, **kwargs):

        rval = False
        info_dict = {}
        logger_name = '{0}.get_audio_file_info'.format(__name__)
        logger = logging.getLogger(logger_name)

        if 'file_prefix' in kwargs:
            self.file_prefix = kwargs['file_prefix']

        if 'file_path' in kwargs:
            file_path = kwargs['file_path']

        if file_path:
            if os.path.isfile(file_path):
                log_msg = 'file exists: {0}'.format(file_path)
                logger.debug(log_msg)
                rval = True
            else:
                log_msg = "file doesn't exist: {0}".format(file_path)
                logger.error(log_msg)
        else:
            log_msg = 'No file passed -- doing nothing.'
            logger.error(log_msg)

        if rval:
            try:
                regex = ('^(.*)\/'   # directory
                '({0})'             # prefix
                '-([^-]+)'          # author / artist
                '-(\w\w)'           # month
                '(\w\w)'            # day
                '-([^-]+)'          # hours
                '-([^-]+)'          # minutes
                '\.(flv)$')          # extension / file type
                regex = regex.format(self.file_prefix)

                log_msg = 'Getting information about: {0}'\
                ' using regex: {1}'.format(file_path, regex)
                logger.debug(log_msg)

                file_pattern = re.compile(r'{0}'.format(regex))

            except Exception:
                log_msg = ("Exception occurred compiling regex:"
                           ": {0}".format(regex))
                logger.exception(log_msg)
                rval = False

        if rval:
            file_match = file_pattern.match(file_path)
            if file_match:
                log_msg = 'Parsed info from file name'
                logger.debug(log_msg)

                if file_match.group(1):
                    log_msg = "group(1): {0}".format(file_match.group(1))
                    logger.debug(log_msg)
                    info_dict['directory'] = file_match.group(1)

                if file_match.group(2):
                    log_msg = "group(2): {0}".format(file_match.group(2))
                    logger.debug(log_msg)
                    info_dict['prefix'] = file_match.group(2)

                if file_match.group(3):
                    log_msg = "group(3): {0}".format(file_match.group(3))
                    logger.debug(log_msg)
                    info_dict['author'] = file_match.group(3)
                    info_dict['artist'] = file_match.group(3)

                if file_match.group(4):
                    log_msg = "group(4): {0}".format(file_match.group(4))
                    logger.debug(log_msg)
                    info_dict['month'] = file_match.group(4)

                if file_match.group(5):
                    log_msg = "group(5): {0}".format(file_match.group(5))
                    logger.debug(log_msg)
                    info_dict['day'] = file_match.group(5)

                if file_match.group(6):
                    log_msg = "group(6): {0}".format(file_match.group(6))
                    logger.debug(log_msg)
                    info_dict['hours'] = file_match.group(6)

                if file_match.group(7):
                    log_msg = "group(7): {0}".format(file_match.group(7))
                    logger.debug(log_msg)
                    info_dict['minutes'] = file_match.group(7)

                if file_match.group(8):
                    log_msg = "group(8): {0}".format(file_match.group(8))
                    logger.debug(log_msg)
                    info_dict['extension'] = file_match.group(8)
                    info_dict['type'] = file_match.group(8)

                log_msg = 'Information dictionary follows:'
                logger.debug(log_msg)
                logger.debug(pformat(info_dict))

            else:
                log_msg = "File doesn't match naming convention"
                logger.error(log_msg)


        return rval, info_dict
