# -*- encoding: utf-8 -*-
"""
by Ken Yu

@ Tue Jul 18 18:43:49 2017
"""

from pymongo.errors import AutoReconnect, ConnectionFailure, NetworkTimeout
from ..settings import LOGGING
import pymongo
import time


def safe_call_mongo(func):
    def Wrapper(*args, **kwargs):
        for i in range(5):
            try:
                return func(*args, **kwargs)
            except (AutoReconnect, ConnectionFailure, NetworkTimeout) as e:
                LOGGING.info(u"{} and reconnect!".format(e))
                time.sleep(pow(2, i))
        LOGGING.info(u'Error: failed to operation!')

    return Wrapper


class Executable(object):
    """docstring for Executable"""

    def __init__(self, mongo_method):
        super(Executable, self).__init__()
        self.mongo_method = mongo_method

    @safe_call_mongo
    def __call__(self, *args, **kwargs):
        return self.mongo_method(*args, **kwargs)


EXECUTABLE_MONGO_METHODS = set([typ for typ in dir(pymongo.collection.Collection) if not typ.startswith('_')])
EXECUTABLE_MONGO_METHODS.update(set([typ for typ in dir(pymongo.MongoClient) if not typ.startswith('_')]))
EXECUTABLE_MONGO_METHODS.update(set([typ for typ in dir(pymongo) if not typ.startswith('_')]))


class MongoProxy:
    """
    Proxy for MongoDB connection.
    Methods that are executable, i.e find, insert etc, get wrapped in an
    Executable-instance that handles AutoReconnect-exceptions transparently.
    """

    def __init__(self, connection):
        """
        connection is an ordinary MongoDB-connection.
        """
        self.connection = connection

    def __getitem__(self, key):
        """
        Create and return proxy around the method in the connection
        named "key".
        """
        return MongoProxy(getattr(self.connection, key))

    def __getattr__(self, key):
        """
        If key is the name of an executable method in the
        MongoDB connection, for instance find or insert, wrap this method in the Executable-class.
        Else call __getitem__(key).
        """
        if key in EXECUTABLE_MONGO_METHODS:
            return Executable(getattr(self.connection, key))
        return self[key]

    def __call__(self, *arg, **kwargs):
        return self.connection(*arg, **kwargs)

    def __dir__(self):
        return dir(self.connection)

    def __repr__(self):
        return self.connection.__repr__()
