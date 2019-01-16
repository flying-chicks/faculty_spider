# -*- coding: utf-8 -*-
"""
Created on Sun Feb 12 10:56:36 2017
@author: KenYu
"""

from datetime import datetime, timedelta
from pymongo import MongoClient
from .utils.safe_connect_mongo import MongoProxy
from .settings import MONGO_HOST
from .utils.mongo_base import advanced_compress, advanced_decompress


class MongoCache(object):
    def __init__(self, client=None, expires=timedelta(days=730)):
        """
        :client: instance of pymongo.mongo_client.MongoClient.
        :expires:instance of datetime.timedelta.update or delete the webpage if beyond expires.
        """
        # connect to mongodb
        self.client = MongoProxy(MongoClient(host=MONGO_HOST, port=27017, socketTimeoutMS=30000,
                                             connectTimeoutMS=3000)) if client is None else MongoProxy(client)

        # connect to a database named 'cache' in mongodb
        self.db = self.client.cache

        # web-page is a collection in cache
        # create a timestamp index to cached webpages.
        self.db.webpage.create_index('timestamp',
                                     expireAfterSeconds=expires.total_seconds())

    def __getitem__(self, url):
        """
        Load the value at the url.s
        """
        record = self.db.webpage.find_one({'_id': url})
        if record:
            return advanced_decompress(record['result'])
        else:
            raise KeyError('{} not in the database!'.format(url))

    def __setitem__(self, url, result):
        """
        Save the value for this url
        """
        record = {
            'result': advanced_compress(result),
            'timestamp': datetime.utcnow()
        }
        self.db.webpage.update_one({'_id': url}, {'$set': record}, upsert=True)

    def close(self):
        print('Closing the mongo client...')
        self.client.close()
