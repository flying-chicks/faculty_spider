# -*- encoding: utf-8 -*-
"""
by Ken Yu

@ Tue Jul 18 18:43:49 2017
"""

from ..utils.safe_connect_mongo import MongoProxy
from ..settings import MONGO_HOST
from datetime import timedelta, datetime
from pymongo import MongoClient, errors


class MongoQueue:
    # record processing status
    OUTSTANDING, PROCESSING, COMPLETE = range(3)

    def __init__(self, client=None, timeout=300):
        # connect to the mongodb client api.
        self.client = MongoProxy(MongoClient(host=MONGO_HOST, port=27017, socketTimeoutMS=30000,
                                             connectTimeoutMS=30000)) if client is None else MongoProxy(client)

        # connect to the database named 'cache'.
        self.db = self.client.cache
        self.timedelta = timedelta(seconds=timeout)

    def __bool__(self):
        """
        if all url in the crawl_queue have been already processed return False, otherwise True.
        """
        # 'crawl_queue' is a collection in database named 'cache'
        record = self.db.crawl_queue.find_one({'status': {'$ne': self.COMPLETE}})  # '$ne' means 'not equal'
        return True if record else False

    def __contains__(self, url):
        record = self.db.crawl_queue.find_one({'_id': url})
        return True if record else False

    def push(self, url):
        """
        push the unique url into the queue.
        """
        try:
            self.db.crawl_queue.insert({'_id': url, 'status': self.OUTSTANDING})
        except errors.DuplicateKeyError:
            # the url has already been in the queue and the url will be not pushed into queue.
            pass

    def clean(self):
        self.db.crawl_queue.drop()

    def pop(self):
        """
        get the url from the queue and modify the process statue from 'OUTSTANDING' to 'PROCESSING'.
        """
        record = self.db.crawl_queue.find_one_and_update(
            filter={'status': self.OUTSTANDING},
            update={'$set': {'status': self.PROCESSING, 'timestamp': datetime.now()}})
        if record:
            return record['_id']
        else:
            self.repair()
            raise KeyError()

    def is_complete(self, url):
        record = self.db.crawl_queue.find_one({'_id': url, 'status': self.COMPLETE})
        return True if record else False

    def complete(self, url, host):
        """
        after pop, modify the process statue from 'PROCESSING' to 'COMPLETE'.
        """
        self.db.crawl_queue.update_one({'_id': url}, {'$set': {'status': self.COMPLETE, 'host': host}})

    def repair(self):
        """
        if seconds when a url was processed are more than 300, modify the process statue from COMPLETE to OUTSTANDING.
        """
        record = self.db.crawl_queue.find_one_and_update(
            filter={'timestamp': {'$lt': datetime.now() - self.timedelta},
                    'status': {'$ne': self.COMPLETE}},
            update={'$set': {'status': self.OUTSTANDING}}
        )
        if record:
            print(u'Released:{}'.format(record['_id']))

    def close(self):
        print('Closing the mongo client...')
        self.client.close()
