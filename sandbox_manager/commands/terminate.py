#!/usr/bin/env python3
"""
Deletes an specified sandbox instance.

Also updates the configuration of the defined HAProxy server to enable access
to sandbox.

Documentation of the arguments can be found in their own description.

**Changelog**

* 17/06/2015 - Pablo - First script version.
* 02/03/2016 - Pablo - Make library pep8 compilant.
"""
import argparse
import sys

import sandbox_manager.iaas
import sandbox_manager.proxy


def main(argv=None):
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Creates a sandbox")
    parser.add_argument('instance_name', type=str,
                        help="Sandbox instance name to delete")
    args = parser.parse_args()

    # Get instance by name
    instance = sandbox_manager.iaas.get_instance(args.instance_name)
    # Remove instance HAProxy configuration file
    sandbox_manager.proxy.remove_instance(instance)
    # Terminate instance
    sandbox_manager.iaas.delete_instance(instance)

    return 0

if (__name__ == "__main__"):
    sys.exit(main(sys.argv))
