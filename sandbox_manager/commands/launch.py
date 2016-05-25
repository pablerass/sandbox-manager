#!/usr/bin/env python3
"""
Launches a sandbox image and deploys the artifacts specified by parameter.

The instance is terminated after the specified duration in minutes by
programing its deletion. Also updates the configuration of the defined
reverse proxy server to enable access to sandbox.

Is designed to work only in EuroCloud projects.

The deploy is launched by executing the ``/opt/deploy.sh`` script present in
the image.

Documentation of the arguments can be found in their own description.

**Changelog**

* 17/06/2015 - Pablo - First script version.
* 02/03/2016 - Pablo - Make library pep8 compilant.
"""
import argparse
import glob
import logging
import sys

import sandbox_manager.deploy
import sandbox_manager.iaas
import sandbox_manager.proxy
import sandbox_manager.schedule

from sandbox_manager.conf import SandboxConfig


DEFAULT_DURATION = 120


def main(argv=None):
    """Main function."""
    logger = logging.getLogger('sb-mgr.launch')

    # Parse arguments
    parser = argparse.ArgumentParser(description="Launch a sandbox")
    parser.add_argument('--artifacts', type=str, default='', nargs='*',
                        help=("Source artifacts directory to be deployed into "
                              "sandbox, accept wildcards"))
    parser.add_argument('--duration', type=int, default=DEFAULT_DURATION,
                        help="Sandbox machine duration in minutes")
    parser.add_argument('--tags', type=str, default=[], nargs='+',
                        help=("Tags to add to sandbox instance and "
                              "configuration"))
    parser.add_argument('--deployArgs', type=str, default=[], nargs='+',
                        help=("Arguments to be passed to sandbox image deploy "
                              "script"))
    args = parser.parse_args()

    # Launch instance
    instance = sandbox_manager.iaas.launch_instance()
    try:
        # Deploy artifacts
        if args.artifacts:
            # Generate full list of artifacts
            artifact_list = []
            for artifact_expr in args.artifacts:
                artifact_list.extend(glob.glob(artifact_expr))
            logger.debug('Artifacts to load "%s"', ", ".join(artifact_list))
            # Deploying artifacts
            sandbox_manager.deploy.deploy_app(instance, artifact_list,
                                              args.deployArgs)

        # Create proxy file
        sandbox_manager.proxy.add_instance(instance, args.duration, args.tags)

        # Program instance shutdown after specified duration
        sandbox_manager.schedule.program_instance_delete(instance,
                                                         args.duration)

        # Show instance cookie information
        access_url = SandboxConfig().get('proxy', 'external_url')
        logger.info('Sandbox ready to be accessed')
        logger.info('# Sandbox cookie: {cookie_value}'.format(
                    cookie_value=sandbox_manager.iaas.
                    get_cookie_value(instance)))
        logger.info('# Sandbox access URL: {url}'.format(url=access_url))
    except Exception:
        # If there is a failure, delete te instance
        logger.exception('Error creating sandbox instance, undoing work...')
        sandbox_manager.proxy.remove_instance(instance)
        sandbox_manager.iaas.delete_instance(instance)

        return 1

    return 0

if (__name__ == "__main__"):
    sys.exit(main(sys.argv))
