"""Manages sandbox manager scheduled commands."""

import logging
import os
import subprocess


def program_instance_termination(instance_name, duration):
    """Schedule a command that terminates an instance after specified duration.

    :param instance: The instance to terminate.
    :type instance: str

    :param duration: The instance to terminate.
    :type duration: str
    """
    logger = logging.getLogger('sb-mgr.schedule.program_instance_termination')

    # Get and check sandbox manager delete command
    delete_command = 'sandbox-terminate'

    # Schedule delete command
    at_command = ("echo \"{command} {params}\" | at now + {minutes} "
                  "minutes").format(minutes=duration, command=delete_command,
                                    params=instance_name)
    logger.debug('Command to run %s', at_command)

    DEV_NULL = open(os.devnull, 'w')
    at_process = subprocess.Popen(at_command, shell=True, cwd="/tmp",
                                  stdout=DEV_NULL, stderr=subprocess.STDOUT)
    at_process.wait()
    if at_process.returncode:
        raise subprocess.CalledProcessError(at_process.returncode,
                                            cmd=at_command)
    logger.info('Scheduled instance %s termination in %s minutes',
                instance_name, duration)
