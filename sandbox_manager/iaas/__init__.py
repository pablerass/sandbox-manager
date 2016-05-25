"""Implement IaaS instances management methods."""
from sandbox_manager.conf import SandboxConfig


if SandboxConfig().has_section('nova'):
    from sandbox_manager.iaas import nova
    iaas = nova
elif SandboxConfig().has_section('aws'):
    from sandbox_manager.iaas import aws
    iaas = aws
else:
    from sandbox_manager.iaas import mock
    iaas = mock


# TODO: This is dirty and I know it
def launch_instance():
    """Wrapper launch instance method."""
    return iaas.launch_instance()


def instance_exists(instance):
    """Wrapper instance exists method."""
    return iaas.instance_exists(instance)


def get_instance(instance_name):
    """Wrapper get instance metthod."""
    return iaas.get_instance(instance_name)


def delete_instance(instance):
    """Wrapper delete instance method."""
    return iaas.delete_instance(instance)


def get_instance_ip(instance):
    """Wrapper get instance ip."""
    return iaas.get_instance_ip(instance)
