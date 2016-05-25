"""Manage nova sandboxes."""
import logging
import os

import boto3
import botocore

import sandbox_manager

from sandbox_manager.conf import SandboxConfig


# Instance functions
def _connect_aws():
    logger = logging.getLogger('sb-mgr.iaas.aws._connect_aws')

    # Load configuration
    logger.debug('Loading configuration')
    try:
        conf = SandboxConfig()
        AWS_ACCESS_KEY = conf.get('aws', 'acces_key_id')
        AWS_SECRET_KEY = conf.get('aws', 'secret_access_key')
        AWS_REGION = conf.get('aws', 'region')
    except Exception as e:
        logger.critical('Unable to load AWS connection configuration')
        raise e

    # Connect to Nova
    conn = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,
                         aws_secret_access_key=AWS_SECRET_KEY,
                         region_name=AWS_REGION)
    logger.info('Connected to AWS region %s', AWS_REGION)
    logger.debug('AWS connection user is %s', AWS_ACCESS_KEY)

    # Return Nova connection
    return conn


def launch_instance():
    """Launch a new sandbox instance. Waits until it is active.

    :returns: The new instance.
    :rtype: boto3.resources.factory.ec2.Instance
    """
    logger = logging.getLogger('sb-mgr.iaas.aws.launch_instance')

    # Load configuration
    logger.debug('Loading configuration')
    try:
        conf = SandboxConfig()
        SANDBOX_USER = conf.get('sandbox', 'user')

        SANDBOX_KEY_NAME = conf.get('sandbox', 'key_name')
        SANDBOX_TYPE = conf.get_int('sandbox', 'type')
        # TODO: Extract image id from highest version of image name
        SANDBOX_IMAGE = conf.get('sandbox', 'image')
        SANDBOX_SUBNET = conf.get('sandbox', 'subnet')
        SANDBOX_SECURITY_GROUP = conf.get('sandbox', 'security_group')

        SANDBOX_INSTANCE_NAME = 'Sandbox - {image}'.format(SANDBOX_IMAGE)
    except Exception as e:
        logger.critical('Unable to load sandbox instance configuration')
        raise e

    with _connect_aws().resource('ec2') as ec2:
        # Launch the instance
        instance = ec2.create_instances(
            ImageId=SANDBOX_IMAGE,
            InstanceType=SANDBOX_TYPE,
            SubnetId=SANDBOX_SUBNET,
            SecurityGroups=[SANDBOX_SECURITY_GROUP],
            KeyName=SANDBOX_KEY_NAME,
            MinCount=1, MaxCount=1)[0]
        # Tag instance
        ec2.create_tags(Resources=[instance.id],
                        Tags=[{'Key': 'Name', 'Value': SANDBOX_INSTANCE_NAME}])
        logger.info('Created instance %s, wait until it becomes active',
                    instance.id)
        logger.debug('Instance %s image  : %s', instance.id,
                     SANDBOX_IMAGE)
        logger.debug('Instance %s type : %s', instance.id,
                     SANDBOX_TYPE)
        logger.debug('Instance %s keypair: %s', instance.id,
                     SANDBOX_KEY_NAME)
        logger.debug('Instance %s subnet: %s', instance.id,
                     SANDBOX_SUBNET)
        logger.debug('Instance %s security group: %s', instance.id,
                     SANDBOX_SECURITY_GROUP)
        logger.debug('Instance %s name: %s', instance.id,
                     SANDBOX_INSTANCE_NAME)

        # Wait until instance becomes active
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance.id])
        logger.debug('Instance %s is now active', instance.id)

        # Return the instance name
        return instance.id


def instance_exists(instance_id):
    """Check if an instance exists in AWS with the same name.

    :param instance_id: The id of the instance to check.
    :type instance: str

    :returns: If an instant with the specified name exists.
    :rtype: bool
    """
    logger = logging.getLogger('sb-mgr.iaas.aws.instance_exists')

    # Check if instance exists
    try:
        get_instance(instance_id)
        logger.debug('Instance %s exists', instance_id)
        return True
    except botocore.exceptions.ClientError:
        return False


def get_instance(instance_id):
    """Retrieve instance from AWS using its id.

    :param instance_id: The id of the instance to retrieve.
    :type instance_id: str

    :returns: The instance with the specified id.
    :rtype: boto3.resources.factory.ec2.Instance
    """
    logger = logging.getLogger('sb-mgr.iaas.aws.get_instance')

    with _connect_aws().resources('ec2') as ec2:
        try:
            # Get the instance
            logger.debug('Getting instance {instance}'.format(
                         instance=instance_id))
            instance = ec2.Instance(instance_id)
            instance.load()
            logger.debug('Loaded instance %s', instance_id)

            # Return the instance
            return instance
        except botocore.exceptions.ClientError as e:
            logger.warning('Instance %s does not exist', instance_id)
            raise e


def terminate_instance(instance):
    """Terminate the specified instance.

    :param instance: The instance id object to delete.
    :type instance: str or boto3.resources.factory.ec2.Instance
    """
    logger = logging.getLogger('sb-mgr.iaas.aws.terminate_instance')

    # Check if the argument is an instance or a string
    if isinstance(instance, str):
        instance_id = instance
        instance = get_instance(instance_id)
    else:
        instance_id = instance.id

    # Delete the instance
    with _connect_aws().resources('ec2') as ec2:
        instance.terminate()
        logger.info('Instance %s terminated', instance_id)


def get_instance_ip(instance):
    """Get instance ip.

    :param instance: The instance name or objetc to get its ip.
    :type instance: str or boto3.resources.factory.ec2.Instance

    :returns: The instance ip.
    :rtype: str
    """
    logger = logging.getLogger('sb-mgr.iaas.aws.get_instance_ip')

    # Check if the argument is an instance or a string
    if isinstance(instance, str):
        instance_id = instance
        instance = get_instance(instance_id)
    else:
        instance_id = instance.id

    # Get instance ip
    instance_ip = instance.private_ip_address
    logger.debug('Instance %s ip is %s', instance_id, instance_ip)
    return instance_ip
