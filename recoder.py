#!/usr/bin/env python

import sys
import os.path
import yaml
import logging
import re
from utils.loggingConfigurator import loggingConfigurator
from utils.workingDir import workingDir
from utils.executer import Executer
from logging.config import dictConfig
from pprint import pformat

class Recoder():

    config_dict = {}

    default_config = {
        'log_dir': 'logs',
        'input_dir': '.',
        'output_dir': 'output'
    }

    raw_files = []

    def __init__(self, **kwargs):

        rval = True
        logger_name = '{0}.__init__'.format(__name__)

        if 'config_file' in kwargs:
            config_file = kwargs['config_file']

        if 'logging_configurator' in kwargs:
            logging_configurator = kwargs['logging_configurator']
        else:
            logging_configurator = loggingConfigurator()

        logger = logging.getLogger(logger_name)

        log_msg = "Now running Recoder"
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
            if 'recoder' in self.config_dict:
                log_msg = 'Recoder config settings found'
                logger.debug(log_msg)
                recoder_config = self.config_dict['recoder']
            else:
                log_msg = 'No recoder config settings found'
                logger.error(log_msg)
                rval = False

        if rval:
            if 'output_dir' in recoder_config:
                output_dir = recoder_config['output_dir']
                log_msg = "Output dir setting found: {0}".format(output_dir)
            else:
                output_dir = self.default_output_dir
                log_msg = ("No output dir configured"
                " -- using default output dir".format(output_dir))
                logger.debug(log_msg)

            working_dir = workingDir()
            if working_dir.verify_dir(dir_desc = "output dir",
                                      dir_name = output_dir):
                self.output_dir = output_dir
            else:
                rval = False

        if rval:
            if 'ffmpeg_exe' in recoder_config:
                ffmpeg_exe = recoder_config['ffmpeg_exe']
                log_msg = "ffmpeg_exe setting found: {0}".format(ffmpeg_exe)
                logger.debug(log_msg)
            else:
                log_msg = ("No ffmpeg_exe setting found"
                           " -- can't recode without that.")
                logger.error(log_msg)
                rval = False

        if rval:
            if os.path.isfile(ffmpeg_exe):
                log_msg = "ffmpeg file exists: {0}".format(ffmpeg_exe)
                logger.debug(log_msg)
            else:
                log_msg = ("ffmpeg file does not exist: {0}"
                           " -- can't recode without that.".format(ffmpeg_exe))
                logger.error(log_msg)
                rval = False

        if rval:
            if os.access(ffmpeg_exe, os.X_OK):
                log_msg = "ffmpeg is executable: {0}".format(ffmpeg_exe)
                logger.debug(log_msg)
            else:
                log_msg = "ffmpeg is not executable: {0}".format(ffmpeg_exe)
                logger.error(log_msg)
                rval = False

        if rval:
            if 'ffprobe_exe' in recoder_config:
                ffprobe_exe = recoder_config['ffprobe_exe']
                log_msg = "ffprobe_exe setting found: {0}".format(ffprobe_exe)
                logger.debug(log_msg)
            else:
                log_msg = ("No ffprobe_exe setting found"
                " -- can't tell duration without that.")
                logger.error(log_msg)
                rval = False

        if rval:
            if os.path.isfile(ffprobe_exe):
                log_msg = "ffprobe file exists: {0}".format(ffprobe_exe)
                logger.debug(log_msg)
            else:
                log_msg = ("ffprobe file does not exist: {0} -- can't tell"
                           " duration without that.".format(ffprobe_exe))
                logger.error(log_msg)
                rval = False

        if rval:
            if os.access(ffprobe_exe, os.X_OK):
                log_msg = "ffprobe is executable: {0}".format(ffprobe_exe)
                logger.debug(log_msg)
            else:
                log_msg = "ffprobe is not executable: {0}".format(ffprobe_exe)
                logger.error(log_msg)
                rval = False

        if rval:
            if 'input_dir' in recoder_config:
                input_dir = recoder_config['input_dir']
                log_msg = "Input dir setting found: {0}".format(input_dir)
            else:
                input_dir = self.default_config['input_dir']
                log_msg = ("No input dir configured"
                " -- using default input dir: {0}".format(input_dir))
                logger.debug(log_msg)

            working_dir = workingDir()
            if working_dir.verify_dir(dir_desc = "input dir",
                                      dir_name = input_dir):
                self.input_dir = input_dir
            else:
                rval = False

        if rval:
            log_msg = "Recoder configuration is valid."
            logger.info(log_msg)
        else:
            log_msg = "Recoder configuration is invalid."
            logger.error(log_msg)

    def recode_files(self, **kwargs):

        rval = True
        logger_name = '{0}.recode_files'.format(__name__)
        logger = logging.getLogger(logger_name)

        if 'regex' in kwargs:
            regex = kwargs['regex']
        else:
            regex = '.*\.flv'

        if 'increments' in kwargs:
            increments = kwargs['increments']
        else:
            increments = '00:01:00'

        flv_file_list = self.load_input_files_by_regex(regex)

        file_count = len(flv_file_list)
        if file_count:
            log_msg = "Flv files found: {0}".format(file_count)
            logger.debug(log_msg)
        else:
            log_msg = "No flv files found."
            logger.info(log_msg)
            rval = False

        if rval:
            rval = self.flv_to_mp3(flv_file_list, increments)

        return rval

    def load_input_files_by_regex(self, regex):

        rval = True
        file_list = []
        logger_name = '{0}.load_input_files_by_regex'.format(__name__)
        logger = logging.getLogger(logger_name)

        try:
            log_msg = ("Compiling regex: [{0}]".format(regex))
            logger.debug(log_msg)
            file_pattern = re.compile(r'{0}'.format(regex))
        except Exception:
            log_msg = "Exception occurred compiling regex: [{0}]".format(regex)
            logger.exception(log_msg)
            rval = False

        if rval:
            log_msg = ("Looking in {0} for files matching regex: {1}"
                       .format(self.input_dir, regex))
            logger.info(log_msg)

            for root, dirs, files in os.walk(self.input_dir):
                for file in files:
                    file_match = file_pattern.match(file)
                    if file_match:
                        path = os.path.join(root, file)
                        log_msg = "Found file: {0}".format(path)
                        logger.debug(log_msg)
                        file_list.append(path)


        return file_list

    def flv_to_mp3(self, file_list, increments):

        rval = True
        logger_name = '{0}.flv_to_mp3'.format(__name__)
        logger = logging.getLogger(logger_name)

        file_name_regex = '(.*)\.flv$'
        file_name_pattern = re.compile(r'{0}'.format(file_name_regex))

        exe = self.config_dict['recoder']['ffmpeg_exe']
        out_dir = self.config_dict['recoder']['output_dir']

        executer = Executer()

        coded_file_count = 0
        failed_count = 0
        for flv_file in file_list:
            #log_msg = "Recoding: {0}".format(flv_file)
            #logger.info(log_msg)
            flv_file_name = os.path.basename(flv_file)

            #mp3_file_name = re.sub('\.flv$', '.mp3', flv_file_name)
            file_name_match = file_name_pattern.match(flv_file_name)
            if file_name_match:
                if file_name_match.group(1):
                    mp3_file_name_prefix = file_name_match.group(1)
                else:
                    log_msg = ("Skipping file because failed to parse"
                    " the input file name: {0}".format(flv_file_name))
                    logger.error(log_msg)
                    continue

            duration = self.get_duration(flv_file)

            minutes = int(duration / 60)
            if minutes <= 0:
                minutes = 1

            for position in range(0, minutes):
                mp3_file_name = '{0}-{1}.mp3'.format(mp3_file_name_prefix,
                                                     str(position).zfill(3))
                log_msg = "Creating: {0}".format(mp3_file_name)
                logger.debug(log_msg)

                mp3_path = os.path.join(out_dir, mp3_file_name)
                com = "{0} -y -ss {3} -t {4} -i {1} {2}".format(exe,
                                                        flv_file,
                                                        mp3_path,
                                                        (position * 60),
                                                        increments)
                log_msg = "command: {0}".format(com)
                logger.debug(log_msg)
                com_result = executer.exec_com(com)

                if com_result:
                    coded_file_count += 1
                else:
                    failed_count += 1

        if failed_count:
            log_msg = ("{0} files coded successfully / "
                       "{1} failures"
                       .format(coded_file_count, failed_count))
            logger.warn(log_msg)
            rval = False
        else:
            log_msg = ("All {0} files recoded successfully"
                       .format(coded_file_count))
            logger.info(log_msg)

        return rval

    def get_duration(self, input_file):

        rval = 0
        logger_name = '{0}.get_duration'.format(__name__)
        logger = logging.getLogger(logger_name)

        exe = self.config_dict['recoder']['ffprobe_exe']
        out_dir = self.config_dict['recoder']['output_dir']

        executer = Executer()

        log_msg = "Getting info for: {0}".format(input_file)
        logger.debug(log_msg)

        com = ("{0} -i {1} -show_entries format=duration -v quiet"
        " -of csv='p=0'").format(exe, input_file)

        log_msg = "command: {0}".format(com)
        logger.debug(log_msg)
        rval, stdout, stderr = executer.exec_com(com)

        if rval == 0:
            log_msg = "Duration={0}".format(stdout)
            logger.debug(log_msg)
            rval = float(stdout)

        return rval

