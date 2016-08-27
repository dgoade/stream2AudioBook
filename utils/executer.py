__author__ = 'david.goade'

import logging
import logging.config
from fabric.api import hide,local,env,settings,warn_only

class Executer():

    def exec_com(self, com_name):

        '''
        function for general-purpose automation tasks
        that require executing an external shell com
        using fabric and capturing the stdout and stderr
        while keeping them separate.
        '''

        rval = 0
        logger_name = '{0}.flv_to_mp3'.format(__name__)
        logger = logging.getLogger(logger_name)

        com="{0}".format(
            com_name)

        log_msg = 'Running external shell com: {0}'.format(com_name)

        try:
            with hide('everything'):
                proc=local(com, capture=True)
                logger.debug('return_code={0}'.format(proc.return_code))

                if proc.return_code == 0:
                    log_msg = 'Command executed successfully: {0}'
                    log_msg = log_msg.format(com)
                    logger.debug(log_msg)
                    rval = proc.return_code
                else:
                    log_msg = 'Command execution failed: {0}'
                    log_msg = log_msg = format(com)
                    logger.error(log_msg)

            rval = proc.return_code

        except Exception:
            log_msg = "Exception occurred executing command"
            logger.exception(log_msg)
            rval = 1

        if( rval == 0 ):
            if( logger.isEnabledFor('DEBUG') ):
                if( proc.stdout ):
                    log_msg = "--stdout from external com follows:\n{0}"
                    log_msg = log_msg.format(proc.stdout)
                    logger.debug(log_msg)
                if( proc.stderr ):
                    log_msg = "--stderr from external com follows:\n{0}"
                    log_msg = log_msg.format(proc.stderr)
                    logger.debug(log_msg)
        else:
            if( proc.stdout ):
                log_msg = "--stdout from external com follows:\n{0}"
                log_msg = log_msg.format(proc.stdout)
                logger.error(log_msg)
            if( proc.stderr ):
                log_msg = "--stderr from external com follows:\n{0}"
                log_msg = log_msg.format(proc.stderr)
                logger.error(log_msg)

        return rval, proc.stdout, proc.stderr
