"""
utils for discovery cluster

Based on the work by Danil Gusev for django-elasticache
https://github.com/gusdan/django-elasticache
"""
from distutils.version import StrictVersion
import re
from telnetlib import Telnet


class WrongProtocolData(ValueError):
    """
    Exception for raising when we get something unexpected
    in telnet protocol
    """
    def __init__(self, cmd, response):
        super(WrongProtocolData, self).__init__(
            'Unexpected response {} for command {}'.format(response, cmd))


def force_unicode(s, encoding='utf-8', errors='strict'):
    """ return the unicode representation of obj """
    if issubclass(type(s), unicode):
        return s
    try:
        return unicode(s, encoding=encoding, errors=errors)
    except UnicodeDecodeError:
        try:
            return s.decode('utf-8')
        except UnicodeDecodeError:
            ascii_text = str(s).encode('string_escape')
            return unicode(ascii_text)


def get_cluster_info(host, port=11211):
    """
    return dict with info about nodes in cluster and current version
    {
        'nodes': [
            'IP:port',
            'IP:port',
        ],
        'version': '1.4.4'
    }
    """
    client = Telnet(host, int(port))
    client.write(b'version\n')
    res = client.read_until(b'\r\n').strip()
    version_list = res.split(b' ')
    if len(version_list) != 2 or version_list[0] != b'VERSION':
        raise WrongProtocolData('version', res)
    version = version_list[1]
    if StrictVersion(force_unicode(version)) >= StrictVersion('1.4.14'):
        cmd = b'config get cluster\n'
    else:
        cmd = b'get AmazonElastiCache:cluster\n'
    client.write(cmd)
    res = client.read_until(b'\n\r\nEND\r\n')
    client.close()
    ls = list(filter(None, re.compile(br'\r?\n').split(res)))
    if len(ls) != 4:
        raise WrongProtocolData(cmd, res)

    try:
        version = int(ls[1])
    except ValueError:
        raise WrongProtocolData(cmd, res)
    nodes = []
    try:
        for node in ls[2].split(b' '):
            host, ip, port = node.split(b'|')
            nodes.append('{}:{}'.format(force_unicode(ip or host),
                                        force_unicode(port)))
    except ValueError:
        raise WrongProtocolData(cmd, res)
    return {
        'version': version,
        'nodes': nodes
    }
