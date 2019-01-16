# -*- coding: utf-8 -*-
"""
Created on Sun Feb 12 10:56:36 2017

@author: KenYu
"""
from pickle import dumps, loads
from zlib import compress, decompress
from bson.binary import Binary
from hashlib import sha224
from pymongo.errors import BulkWriteError, DuplicateKeyError


def advanced_compress(obj):
    return Binary(compress(dumps(obj)))


def advanced_decompress(obj):
    return loads(decompress(obj))


def safe_encrypt(string):
    string = string.encode('utf-8') if type(string).__name__ != 'bytes' else string
    return sha224(string).hexdigest()


class SafeInsertMany(object):
    def __init__(self, collection, num_buffers):
        self._collection = collection
        self._buffers = []
        self._num_buffers = num_buffers

    def __call__(self, record):
        if len(self._buffers) < self._num_buffers:
            self._buffers.append(record)
            return None

        try:
            self._collection.insert_many(self._buffers)
        except BulkWriteError:
            for r in self._buffers:
                try:
                    self._collection.insert_one(r)
                except DuplicateKeyError:
                    continue

        finally:
            self._buffers = []

    def close(self):
        if len(self._buffers) is 0:
            return None

        try:
            self._collection.insert_many(self._buffers)
        except BulkWriteError:
            for r in self._buffers:
                try:
                    self._collection.insert_one(r)
                except DuplicateKeyError:
                    continue
        finally:
            self._buffers = []
