"""Implement reverse proxy configuration methods."""
from sandbox_manager.conf import SandboxConfig


if SandboxConfig().has_section('haproxy'):
    from sandbox_manager.proxy import haproxy
    proxy = haproxy
else:
    from sandbox_manager.proxy import mock
    proxy = mock


# This is dirty and I know it
def get_cookie_value(instance_name):
    """Wrapper get cookie value method"""
    return proxy.get_cookie_value(instance_name)


def add_instance(instance_name, duration, tags=[]):
    """Wrapper add instance to proxy method."""
    return proxy.add_instance(instance_name, duration, tags)


def remove_instance(instance_name):
    """Wrapper remove instance from proxy method."""
    return proxy.remove_instance(instance_name)

def list_instances():
    """Wrapper list all instance file instances."""
    return proxy.list_instances()
