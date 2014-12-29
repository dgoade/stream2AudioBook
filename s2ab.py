#!/usr/bin/env python

__author__ = 'dgoade'

import sys
import logging
import getopt
from recoder import Recoder
from utils.executer import Executer
from utils.loggingConfigurator import loggingConfigurator

def usage():

    print "look at the code and figure it out, slick"

def main():

    rval = True
    help = False
    log_level = "error"
    no_op = False
    verbose = False
    action = 'recode'
    config_file = "s2ab.yml"
    regex = ".*"

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

    logging_configurator = loggingConfigurator()
    recode = Recoder(logging_configurator = logging_configurator,
                     config_file = config_file)

    recode.recode_files(regex=regex)


    if rval:
        log_msg = "Recoder completed successfully"
    else:
        log_msg = "Recoder failed"

    logging.debug(log_msg)

if __name__ == "__main__":
    main()
