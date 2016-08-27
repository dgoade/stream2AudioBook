#!/usr/bin/env python

import sys
import os
import time  
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler  

import getopt
import yaml
import logging
from recoder import Recoder
from utils.loggingConfigurator import loggingConfigurator
from utils.workingDir import workingDir
from pprint import pformat
import ntpath

class RawFileHandler(PatternMatchingEventHandler):
    patterns = ["*.flv"]

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

        log_msg = "'{0}' event occurred for '{1}'"
        log_msg = log_msg.format(event.event_type, event.src_path)
        logger.debug(log_msg)
        #print event.src_path, event.event_type  # print now only for degug

        size = os.path.getsize(event.src_path)
        if size > 0:
            log_msg = "File {0} has content -- processing".format(event.src_path)
            logger.debug(log_msg)

            regex = ntpath.basename(event.src_path)

            logging_configurator = loggingConfigurator()
            recode = Recoder(logging_configurator = logging_configurator,
                             config_file = 'recoder.yml')
            rval = recode.recode_files(regex=regex)

            if rval:
                log_msg = "Recoder completed successfully"
            else:
                log_msg = "Recoder failed"

            logging.debug(log_msg)

        else:
            log_msg = "File {0} has no content so ignoring it for now".format(event.src_path)
            logger.debug(log_msg) 

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

class RawDirObserver():

    config_dict = {}

    default_config = {
        'log_dir': 'logs',
        'watch_dir': '.'
    }

    def __init__(self, **kwargs):

        rval = True
        logger_name = '{0}.__init__'.format(__name__)
        config_file = "watcher.yml"

        if 'config_file' in kwargs:
            config_file = kwargs['config_file']

        if 'logging_configurator' in kwargs:
            logging_configurator = kwargs['logging_configurator']
        else:
            logging_configurator = loggingConfigurator()

        logger = logging.getLogger(logger_name)

        log_msg = "Now running RawDirObserver"
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
            if 'RawDirObserver' in self.config_dict:
                log_msg = 'RawDirObserver config settings found'
                logger.debug(log_msg)
                observer_config = self.config_dict['RawDirObserver']
            else:
                log_msg = 'No RawDirObserver config settings found'
                logger.error(log_msg)
                rval = False

        if rval:
            if 'watch_dir' in observer_config:
                watch_dir = observer_config['watch_dir']
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
            log_msg = "RawDirObserver configuration is valid."
            logger.debug(log_msg)
        else:
            log_msg = "RawDirObserver configuration is invalid."
            logger.error(log_msg)

    def schedule(self):

        rval = True
        logger_name = '{0}.schedule'.format(__name__)
        logger = logging.getLogger(logger_name)

        watch_dir = self.config_dict['RawDirObserver']['watch_dir']

        observer = Observer()
        observer.schedule(RawFileHandler(),
                          path=watch_dir)
        observer.start()

        try:
            log_msg = "Watching directory for changes: {0}".format(watch_dir)
            logger.info(log_msg)
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()

        observer.join()

        return rval

def main():

    rval = True
    help = False
    log_level = "error"
    no_op = False
    verbose = False
    action = 'watch'
    config_file = "watcher.yml"
    regex = ".*\.flv$"

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "a:c:hl:nr:v",
                                   ["action=",
                                    "config="
                                    "help",
                                    "loglevel=",
                                    "regex=",
                                    "noop", "verbose"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        rval = False

    if rval:
        no_op = False
        verbose = False
        for o, a in opts:
            if o in ("-a", "--action"):
                action = a
            elif o in ("-c", "--config"):
                config_file = a
            elif o in ("-h", "--help"):
                help = True
                usage()
                rval = False
            elif o in ("-l", "--loglevel"):
                log_level = a
            elif o in ("-n", "--noop"):
                no_op = True
            elif o in ("-r", "--regex"):
                regex = a
            elif o in ("-v", "--verbose"):
                verbose = True
            else:
                assert False, "unhandled option"

    if rval:
        print "You passed these args:"
        print ("action: %s" % action)
        print ("config_file: %s" % config_file)
        print ("help: %s" % help)
        print ("loglevel: %s" % log_level)
        print ("noop: %s" % no_op)
        print ("regex: %s" % regex)
        print ("verbose: %s" % verbose)

    if rval:
        logging_configurator = loggingConfigurator()
        raw_dir_observer = RawDirObserver(logging_configurator = logging_configurator,
                         config_file = config_file)
        rval = raw_dir_observer.schedule()

    if rval:
        log_msg = "RawDirObserver completed successfully"
    else:
        log_msg = "RawDirObserver failed"

    logging.debug(log_msg)

if __name__ == '__main__':
    main()

