"""
    SoftLayer.utils
    ~~~~~~~~~~~~~~~
    Utility function/classes

    :license: MIT, see LICENSE for more details.
"""
import re

import six

# pylint: disable=pointless-except, no-member, invalid-name

UUID_RE = re.compile(r'^[0-9a-f\-]{36}$', re.I)
KNOWN_OPERATIONS = ['<=', '>=', '<', '>', '~', '!~', '*=', '^=', '$=', '_=']

configparser = six.moves.configparser
string_types = six.string_types
StringIO = six.StringIO
xmlrpc_client = six.moves.xmlrpc_client


def lookup(dic, key, *keys):
    """A generic dictionary access helper.

    This helps simplify code that uses heavily nested dictionaries. It will
    return None if any of the keys in *keys do not exist.

    ::

        >>> lookup({'this': {'is': 'nested'}}, 'this', 'is')
        nested

        >>> lookup({}, 'this', 'is')
        None

    """
    if keys:
        return lookup(dic.get(key, {}), *keys)
    return dic.get(key)


class NestedDict(dict):
    """This helps with accessing a heavily nested dictionary.

    Dictionary where accessing keys that don't exist will return another
    NestedDict object.

    """

    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        return self.setdefault(key, NestedDict())

    def to_dict(self):
        """Converts a NestedDict instance into a real dictionary.

        This is needed for places where strict type checking is done.
        """
        new_dict = {}
        for key, val in self.items():
            if isinstance(val, NestedDict):
                new_dict[key] = val.to_dict()
            else:
                new_dict[key] = val
        return new_dict


def query_filter(query):
    """Translate a query-style string to a 'filter'.

    Query can be the following formats:

    Case Insensitive
      'value' OR '*= value'    Contains
      'value*' OR '^= value'   Begins with value
      '*value' OR '$= value'   Ends with value
      '*value*' OR '_= value'  Contains value

    Case Sensitive
      '~ value'   Contains
      '!~ value'  Does not contain
      '> value'   Greater than value
      '< value'   Less than value
      '>= value'  Greater than or equal to value
      '<= value'  Less than or equal to value

    :param string query: query string

    """
    try:
        return {'operation': int(query)}
    except ValueError:
        pass

    if isinstance(query, string_types):
        query = query.strip()
        for operation in KNOWN_OPERATIONS:
            if query.startswith(operation):
                query = "%s %s" % (operation, query[len(operation):].strip())
                return {'operation': query}
        if query.startswith('*') and query.endswith('*'):
            query = "*= %s" % query.strip('*')
        elif query.startswith('*'):
            query = "$= %s" % query.strip('*')
        elif query.endswith('*'):
            query = "^= %s" % query.strip('*')
        else:
            query = "_= %s" % query

    return {'operation': query}


class IdentifierMixin(object):
    """Mixin used to resolve ids from other names of objects.

    This mixin provides an interface to provide multiple methods for
    converting an 'indentifier' to an id

    """
    resolvers = []

    def resolve_ids(self, identifier):
        """Takes a string and tries to resolve to a list of matching ids.

        What exactly 'identifier' can be depends on the resolvers

        :param string identifier: identifying string
        :returns list:
        """

        return resolve_ids(identifier, self.resolvers)


def resolve_ids(identifier, resolvers):
    """Resolves IDs given a list of functions.

    :param string identifier: identifier string
    :param list resolvers: a list of functions
    :returns list:
    """

    # Before doing anything, let's see if this is an integer
    try:
        return [int(identifier)]
    except ValueError:
        pass  # It was worth a shot

    # This looks like a globalIdentifier (UUID)
    if len(identifier) == 36 and UUID_RE.match(identifier):
        return [identifier]

    for resolver in resolvers:
        ids = resolver(identifier)
        if ids:
            return ids

    return []
