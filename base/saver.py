# -*- coding: utf-8 -*-
"""
Created on Sun Feb 12 10:56:36 2017

@author: KenYu
"""
from datetime import datetime, timedelta
from pymongo import MongoClient
from .utils.safe_connect_mongo import MongoProxy
from .settings import MONGO_HOST
from .utils.mongo_base import advanced_compress, safe_encrypt, SafeInsertMany


class InfoStore(object):
    def __init__(self, client=None, db='no_target_db', collection='no_target_col', expires=timedelta(days=730)):
        """
        :db: the name of database, must be "no_target_db" or "target_db".
        :collection: the name of collection, must be "no_target_col" when db is "no_target_db",
        university name or college name when db is "target_db"
        :client: instance of pymongo.mongo_client.MongoClient.
        :expires:instance of datetime.timedelta.update or delete the webpage if beyond expires.
        """
        # connect to mongodb
        self.client = MongoProxy(MongoClient(host=MONGO_HOST, port=27017, socketTimeoutMS=30000,
                                             connectTimeoutMS=30000)) if client is None else MongoProxy(client)

        # connect to a database named 'store' in mongodb
        self.db = getattr(self.client, db)

        self.collection = getattr(self.db, collection)

        # create a timestamp index to a collection
        self.collection.create_index('timestamp', expireAfterSeconds=expires.total_seconds())

        self.safe_insert_many = SafeInsertMany(self.collection, 30)

    def save_target(self, webpage_url, webpage, content, name, anchor_text, image_url):
        """
        Save the value for this url
        """
        record = {'_id': safe_encrypt(webpage),
                  'webpage': advanced_compress(webpage),
                  'content': advanced_compress(content),
                  'name': name,
                  'anchor_text': anchor_text,
                  'webpage_url': webpage_url,
                  'image_url': image_url,
                  'timestamp': datetime.utcnow(),
                  }
        self.safe_insert_many(record)

    def save_not_target(self, url, webpage, content):
        """
        :param url: URL string
        :param webpage: webpage string
        :param content: textual content.
        """
        record = {
            '_id': safe_encrypt(webpage),
            'webpage_url': url,
            'webpage': advanced_compress(webpage),
            'content': advanced_compress(content)
        }
        self.safe_insert_many(record)

    def close(self):
        print('Closing the mongo client...')
        self.safe_insert_many.close()
        self.client.close()
