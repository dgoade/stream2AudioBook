#!/usr/bin/env python

import os
import os.path
import sys
import re
import logging
from logging.config import dictConfig
import getopt
import yaml
#import pprint
#import fnmatch
#from pprint import pformat

from mutagen.id3 import ID3, TIT2
from mutagen.easyid3 import EasyID3

def usage():
    print """
        usage: s2ab-tag.py 
            -a [list|tag] 
            [-d directory]
            [-f frame]
            [-h|--help]
            [-i infile]
            [-r fileRegex] 
            [--loglevel DEBUG|INFO|WARN|ERROR|CRITICAL] 
            [-v[erbose]]
    """

def init():

    global Action
    global Directory
    global Help
    global Frame
    global InFile
    global FileRegex
    global LogLevel
    global Verbose

    global StreamFileRegex

    StreamFileRegex=r'.*Radio-(\w\w)-(\d\d)(\d\d)-(\d\d)-(\d\d)-(\d+)\.*'

    Action='list'
    Directory="."
    Help=False
    Frame=None
    InFile=None
    FileRegex=None
    LogLevel='INFO'
    Verbose=False

    rval=True

    #logging.config.fileConfig('./logging.conf')
    f = open('./s2ab.yml')


    loggingConfig = yaml.safe_load(f)
    f.close()

    logging.config.dictConfig(loggingConfig)

    logDir='./logs'
    #logFileName='%s/s2ab-tag.log' % (logDir)

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 
            "a:d:f:hi:r:l:v", 
            ["action=", 
            "directory=", 
            "frame=", 
            "help", 
            "infile=", 
            "loglevel=", 
            "file-regex="])

    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-v", "--verbose"):
            Verbose = True
        elif o in ("-a", "--action"):
            Action = a
        elif o in ("-d", "--directory"):
            Directory = a
        elif o in ("-f", "--frame"):
            Frame = a
        elif o in ("-h", "--help"):
            usage()
            Help=True
            rval=False
        elif o in ("-i", "--infile"):
            InFile = a
        elif o in ("-r", "--file-regex"):
            FileRegex = a
        elif o in ("-l", "--loglevel"):
            LogLevel = a
        else:
            assert False, "unhandled option"

    if rval:
        if os.path.exists(logDir): 
            pass 
        else:
            if os.mkdir(logDir, 0777) != False:
                # chmod because the mkdir
                # mode still depends on umask
                if os.chmod(logDir, 0777) != False:
                    rval=True
                else:
                    print "Unable to set permissions on logs dir: %s" % logDir
                    rval=False
            else:
                 print "Unable to create logs directory: %s" % logDir 
    

    if rval:
        if os.access(logDir, os.W_OK):
            rval=True
        else:
            print "logs dir is not writeable"
            rval=False
        
    if rval:
        # assuming loglevel is bound to the string value obtained from the
        # command line argument. Convert to upper case to allow the user to
        # specify --log=DEBUG or --log=debug
        numeric_level = getattr(logging, LogLevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % LogLevel)
            rval=False

    if rval:
        # All you need to log to a file
        #logging.basicConfig(filename='%s' % logFileName, filemode='w', level=numeric_level)

        # To log to the console, too
        #logger = logging.getLogger()
        #logger.setLevel(numeric_level)
        #formatter = logging.Formatter("%(levelname)s - %(message)s")

        # Add the file handler
        #fh = logging.RotatingFileHandler(filename='%s/lockVobs.log', mode='a', maxBytes=1000, backupCount=5, encoding=None, delay=0)
        #fh = logging.FileHandler(filename='%s' % logFileName, mode='a')
        #fh.setLevel(numeric_level)
        #formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        #fh.setFormatter(formatter)
        #logger.addHandler(fh)

        if Verbose:
            # Add the console handler
            #ch = logging.StreamHandler()
            #ch.setLevel(numeric_level)
            ##formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            #formatter = logging.Formatter("%(levelname)s - %(message)s")
            #ch.setFormatter(formatter)
            #logger.addHandler(ch)
            pass

        if InFile:
            logging.debug('Looking for file: %s' % InFile)
            if InFile:
                if os.path.exists(InFile):
                    logging.debug('File specified is: %s' % InFile)
                    pass 
                else:
                    logger.error("Specified infile doesn't exist: %s" % InFile)
                    rval=False
        else:
            if FileRegex:
                logging.info("Will act on files matching: '%s'" % FileRegex)
            else:
                logMsg="Must specify either file or file regex with" 
                logMsg+="optional directory."
                logger.error(logMsg)
                rval=False


    if rval:
        logging.debug('Running with the following parameters:')
        logging.debug('     Action: %s' % Action)
        logging.debug('     InFile: %s' % InFile)
        logging.debug('     FileRegex: %s' % FileRegex)
        logging.debug('     Frame: %s' % Frame)

    return rval 

def main():

    logger = logging.getLogger()
    diskNumDict = {};
    fileDict = {};

    if init():
        logger.info('Initialized successfully.')
        if Directory:
            if InFile:
                fileDict[InFile]=InFile
                #listFilesWithTags(fileDict)
            elif FileRegex:
                fileDict=filesMatching(Directory, FileRegex)        
                #listFilesWithTags(fileDict)
        if Action.upper() == 'TAG':
            diskNumDict = assignDiskNums(Directory, StreamFileRegex)
            if len(diskNumDict):
                tagFiles(fileDict, diskNumDict)
            else:
                logger.error('Failed to assign disk numbers.')

        else:
            listFilesWithTags(fileDict)
    else:
        if Help:
            pass
        else:
            #logger.error('Failed to initialize.')
            print "Failed to initialize."

def listFilesWithTags(fileDict):

    rval=True
    logger = logging.getLogger()

    if len(fileDict):
        logger.info('Listing all files in scope:' )
        for file in fileDict:
            logger.info('%s' % file)
            audio = EasyID3(file)
            for key in audio:
                logger.info('%s: %s' % (key, audio[key]))
    else:
        logger.info('No files in scope to list.' )
        rval=False

    return rval
        

def tagFiles(fileDict, diskNumDict):

    logger = logging.getLogger()

    logger.info('Listing tags before changes.' )
    rval=listFilesWithTags(fileDict)

    if rval:

       # Radio-MS-0110-14-06-001.mp3 
        logger.info('Listing all files in scope:' )
        for file in fileDict:
            logger.info('%s' % file)
            audio = EasyID3(file)

            # These are the keys that you can edit with EasyID3 
            #['albumartistsort', 
            #'musicbrainz_albumstatus', 
            #'lyricist', 
            #'releasecountry', 
            #'date', 
            #'performer', 
            #'musicbrainz_albumartistid', 
            #'composer', 
            #'encodedby', 
            #'tracknumber', 
            #'musicbrainz_albumid', 
            #'album', '
            #asin', 
            #'musicbrainz_artistid', 
            #'mood', 
            #'copyright', 
            #'author', 
            #'media', 
            #'length', 
            #'version', 
            #'artistsort', 
            #'titlesort', 
            #'discsubtitle', 
            #'website', 
            #'musicip_fingerprint', 
            #'conductor', 
            #'compilation', 
            #'barcode', 
            #'performer:*', 
            #'composersort', 
            #'musicbrainz_discid', 
            #'musicbrainz_albumtype', 
            #'genre', 
            #'isrc', 
            #'discnumber', 
            #'musicbrainz_trmid', 
            #'replaygain_*_gain', 
            #'musicip_puid', 
            #'artist', 
            #'title', 
            #'bpm',
            #'musicbrainz_trackid', 
            #'arranger', 
            #'albumsort', 
            #'replaygain_*_peak', 
            #'organization']

            #audio["title"] = u"An easy example"
            #audio["discnumber"] = u"1"
            #audio.save()

            deriveTagsFromFile(file, diskNumDict)
        
    logger.info('Listing tags after changes.' )
    rval=listFilesWithTags(fileDict)

def deriveTagsFromFile(fileName, diskNumDict):

    rval = 1
    tagDict={}

    logger = logging.getLogger()

    if diskNumDict[fileName]:
        tagDict['disknumber'] = diskNumDict[fileName]
        logMsg = 'diskNum for %s ' % fileName
        logMsg += ' was set to %s' % tagDict['disknumber']
        logger.debug(logMsg)
    else:
        logMsg = 'No diskNum could be found for %s' % fileName
        logger.error(logMsg)
        rval = 0

    if rval:   
        # Radio-MS-0110-14-06-001.mp3 
        pattobj = re.compile(StreamFileRegex)

        matchobj=pattobj.match(fileName)
        if matchobj:
            tagDict['artist'] = matchobj.group(1)

            tagDict['album'] = '%s' % matchobj.group(1)
            tagDict['album'] += ' %s /' % matchobj.group(2)
            tagDict['album'] += ' %s' % matchobj.group(3)

            tagDict['tracknumber']=matchobj.group(6)
            tagDict['tracknumber']=matchobj.group(6)
            logger.debug('Tags derived from file name are:')
            logger.debug('  artist: %s' % tagDict['artist'])
            logger.debug('  album: %s' % tagDict['album'])
            logger.debug('  disknumber: %s' % tagDict['disknumber'])
            logger.debug('  tracknumber: %s' % tagDict['tracknumber'])
        else:
            logMsg = "Can't derive tags from file name."
            logger.error(logMsg)
    else:
        logMsg = 'Not setting any tags without knowing diskNum.'
        logger.error(logMsg)
        
        
def assignDiskNums(rootDir, fileRegex):

    logger = logging.getLogger()
    fileDict = filesMatching(rootDir, fileRegex) 

    if len(fileDict):

        pattobj = re.compile(r'.*(Radio-\w\w-\d{4})-(\d\d)-(\d\d)-(\d+)\.*')

        diskNum = 1
        lastPrefix = None
        lastHour = None
        lastMin = None

        for filename in sorted(fileDict.iterkeys()):
            matchobj=pattobj.match(filename)
            if matchobj:
                prefix=matchobj.group(1)
                hour=matchobj.group(2)
                min=matchobj.group(3)

                logger.debug('prefix: %s' % prefix)
                logger.debug('hour: %s' % hour)
                logger.debug('min: %s' % min)

                if prefix == lastPrefix:
                    if hour == lastHour:
                        if min == lastMin:
                            pass
                        else:
                            diskNum += 1
                            lastmin = min
                            logMsg = 'Change of minutes -- incrementing'
                            logMsg += ' diskNum: %s' % diskNum
                            logger.debug(logMsg)
                    else:
                        diskNum += 1
                        lastHour = hour
                        lastMin = min
                        logMsg = 'Change of hour -- incrementing'
                        logMsg += ' diskNum: %s' % diskNum
                        logger.debug(logMsg)
                else:
                    diskNum = 1 
                    lastPrefix = prefix 
                    lastHour = hour
                    lastMin = min
                    logMsg = 'Change of prefix -- resetting'
                    logMsg += ' diskNum: %s' % diskNum
                    logger.debug(logMsg)

                fileDict[filename] = diskNum

            else:
                logMsg = 'Unable to parse the file name.' 
                logger.debug(logMsg)
    else:
        logMsg='No stream files found to assign disk numbers to.'
        logger.error(logMsg)

    return fileDict

def filesMatching(rootDir, fileRegex):
 
    logger = logging.getLogger()
    fileDict={}

    pattobj = re.compile( fileRegex) 

    # I don't need to recurse down the subdirs 
    # but if I did, this is how I would do it.    
    #for root, dirs, files in os.walk(rootDir):
    #    for filename in fnmatch.filter(files, '*'):
    #        filePath=os.path.join(root, filename)
    #        logger.info('file: %s' %  filePath)    
    #        fileDict[filePath]=filePath

    # os.listdir is fine for my needs
    for filename in os.listdir(rootDir): 
        filePath=os.path.join(rootDir, filename)

        matchobj=pattobj.match(filename)
        if matchobj:
            logger.debug('matching file: %s' %  filePath)    
            fileDict[filePath]=filePath

    return fileDict

if __name__ == "__main__":
    main()


