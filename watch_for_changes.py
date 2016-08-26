#!/usr/bin/env python

import sys
import os
import time  
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler  

import yaml
import logging
from utils.loggingConfigurator import loggingConfigurator
from utils.workingDir import workingDir
from utils.executer import Executer
from logging.config import dictConfig
from pprint import pformat

class RawFileHandler(PatternMatchingEventHandler):
    patterns = ["*.flv"]

    config_file = "s2ab.yml"
    config_dict = {}

    default_config = {
        'log_dir': 'logs',
        'watch_dir': '.'
    }

    def __init__(self, **kwargs):

        rval = True
        logger_name = '{0}.__init__'.format(__name__)
        config_file = "s2ab.yml"

        if 'config_file' in kwargs:
            config_file = kwargs['config_file']

        if 'logging_configurator' in kwargs:
            logging_configurator = kwargs['logging_configurator']
        else:
            logging_configurator = loggingConfigurator()

        logger = logging.getLogger(logger_name)

        log_msg = "Now running RawFileHandler"
        logging.debug(log_msg)

        if os.path.isfile(config_file):
            log_msg = "Config file exists: {0}".format(config_file)
            logging.debug(log_msg)
        else:
            log_msg = "Config file does not exist: {0}".format(config_file)
            logging.error(log_msg)
            rval = False

        if rval:
            try:
                log_msg = "Loading config"
                logging.debug(log_msg)
                f = open(config_file)
                config_dict = yaml.safe_load(f)
                f.close()

                if config_dict:
                    log_msg = "Loaded config dict successfully"
                    logging.debug(log_msg)
                    self.config_dict = config_dict
                else:
                    log_msg = "Failed to load config dict"
                    logging.error(log_msg)
                    rval = False

            except Exception:
                log_msg = "Exception occurred attempting to load config dict"
                logging.exception(log_msg)
                rval = False

        if rval:
            if 'logging' in self.config_dict:
                log_msg = "Logging settings found in config dict -- loading"
                logging.debug(log_msg)
                logging_config = self.config_dict['logging']

                logging_configurator.reconfigure_logging(logging_config)

                log_msg = 'Logging reconfigured successfully.'
                logger.debug(log_msg)

                log_msg =  'Logging pformatted data of the config_dict'
                logger.debug(log_msg)
                logger.debug(pformat(self.config_dict))

        if rval:
            # validate the configuration
            if 'RawFileHandler' in self.config_dict:
                log_msg = 'RawFileHandler config settings found'
                logger.debug(log_msg)
                rfh_config = self.config_dict['RawFileHandler']
            else:
                log_msg = 'No RawFileHandler config settings found'
                logger.error(log_msg)
                rval = False

        if rval:
            if 'watch_dir' in rfh_config:
                watch_dir = rfh_config['watch_dir']
                log_msg = "watch_dir setting found: {0}".format(watch_dir)
            else:
                watch_dir = self.default_config['watch_dir']
                log_msg = ("No watch dir configured"
                " -- using default watch dir: {0}".format(watch_dir))
                logger.debug(log_msg)

            working_dir = workingDir()
            if working_dir.verify_dir(dir_desc = "watch dir",
                                      dir_name = watch_dir):
                self.watch_dir = watch_dir
            else:
                rval = False

        if rval:
            log_msg = "RawFileHandler configuration is valid."
            logger.info(log_msg)
        else:
            log_msg = "RawFileHandler configuration is invalid."
            logger.error(log_msg)

    def process(self, event):
        """
        event.event_type 
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """

        rval = True
        logger_name = '{0}.process'.format(__name__)
        logger = logging.getLogger(logger_name)

        # the file will be processed here

        log_msg = "event {0} occurred for src_path {1}"
        log_msg = log_msg.format(event.src_path, event.event_type)
        logger.debug(log_msg)
        print event.src_path, event.event_type  # print now only for degug

        size = os.path.getsize(event.src_path)
        if size > 0:
            log_msg = "File {0} has content".format(event.src_path)
            logger.debug(log_msg)
        else:
            log_msg = "File {0} has no content".format(event.src_path)
            logger.debug(log_msg) 

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

def init():

    rval = True
    logger_name = '{0}.__init__'.format(__name__)
    config_file = "s2ab.yml"

    if 'config_file' in kwargs:
        config_file = kwargs['config_file']

    if 'logging_configurator' in kwargs:
        logging_configurator = kwargs['logging_configurator']
    else:
        logging_configurator = loggingConfigurator()

    logger = logging.getLogger(logger_name)

    log_msg = "Now running RawFileHandler"
    logging.debug(log_msg)

    if os.path.isfile(config_file):
        log_msg = "Config file exists: {0}".format(config_file)
        logging.debug(log_msg)
    else:
        log_msg = "Config file does not exist: {0}".format(config_file)
        logging.error(log_msg)
        rval = False

    if rval:
        try:
            log_msg = "Loading config"
            logging.debug(log_msg)
            f = open(config_file)
            config_dict = yaml.safe_load(f)
            f.close()

            if config_dict:
                log_msg = "Loaded config dict successfully"
                logging.debug(log_msg)
                self.config_dict = config_dict
            else:
                log_msg = "Failed to load config dict"
                logging.error(log_msg)
                rval = False

        except Exception:
            log_msg = "Exception occurred attempting to load config dict"
            logging.exception(log_msg)
            rval = False

    if rval:
        if 'logging' in self.config_dict:
            log_msg = "Logging settings found in config dict -- loading"
            logging.debug(log_msg)
            logging_config = self.config_dict['logging']

            logging_configurator.reconfigure_logging(logging_config)

            log_msg = 'Logging reconfigured successfully.'
            logger.debug(log_msg)

            log_msg =  'Logging pformatted data of the config_dict'
            logger.debug(log_msg)
            logger.debug(pformat(self.config_dict))

    if rval:
        # validate the configuration
        if 'RawFileHandler' in self.config_dict:
            log_msg = 'RawFileHandler config settings found'
            logger.debug(log_msg)
            rfh_config = self.config_dict['RawFileHandler']
        else:
            log_msg = 'No RawFileHandler config settings found'
            logger.error(log_msg)
            rval = False

    if rval:
        if 'watch_dir' in rfh_config:
            watch_dir = rfh_config['watch_dir']
            log_msg = "watch_dir setting found: {0}".format(watch_dir)
        else:
            watch_dir = self.default_config['watch_dir']
            log_msg = ("No watch dir configured"
            " -- using default watch dir: {0}".format(watch_dir))
            logger.debug(log_msg)

        working_dir = workingDir()
        if working_dir.verify_dir(dir_desc = "watch dir",
                                  dir_name = watch_dir):
            self.watch_dir = watch_dir
        else:
            rval = False

    if rval:
        log_msg = "RawFileHandler configuration is valid."
        logger.info(log_msg)
    else:
        log_msg = "RawFileHandler configuration is invalid."
        logger.error(log_msg)

if __name__ == '__main__':

    if init():

        args = sys.argv[1:]
        observer = Observer()
        observer.schedule(RawFileHandler(), path=args[0] if args else '.')
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()

        observer.join()
    else:
        print "failed to initialize"
