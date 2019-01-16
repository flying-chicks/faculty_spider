from urllib.parse import urlparse
from .safe_connect_mongo import MongoProxy
from ..settings import MONGO_HOST, MAX_ACCESS, LOGGING
from pymongo import MongoClient


class AccessLimit(object):
    """
    Control the crawling scale.
    """

    def __init__(self, client=None):
        self.client = MongoProxy(MongoClient(host=MONGO_HOST, port=27017, socketTimeoutMS=30000,
                                             connectTimeoutMS=30000)) if client is None else MongoProxy(client)
        self.db = self.client.cache
        self.init_max_access = MAX_ACCESS

    def exceed_max_access(self, url):
        """
        :param url: URL string.
        :return: boolean.
        """
        parsed = urlparse(url)
        result = self.db.domain.find_one({'_id': parsed.netloc})

        if not result:
            self.db.domain.insert_one({'_id': parsed.netloc, 'access': 1,
                                       'max_access': self.init_max_access, 'target': 0})
            return False

        access = result['access'] + 1
        self.db.domain.update_one({'_id': parsed.netloc}, {'$set': {'access': access}})
        max_access = result['max_access']

        if access >= max_access * 0.5 and result['target'] <= 5:
            max_access = 0
            self.db.domain.update_one({'_id': parsed.netloc}, {'$set': {'max_access': max_access}})

        if access >= max_access:  # if the count > max_access then return True
            LOGGING.info(u'{} exceeds max access!'.format(url))
            return True

        return False

    def update_max_access(self, url):
        """
        :param url: URL string.
        :return: null.
        """
        parsed = urlparse(url)
        result = self.db.domain.find_one({'_id': parsed.netloc})
        if not result:
            return None
        max_access = result['max_access']
        access = result['access']
        target_hat = result['target'] + 1
        self.db.domain.update_one({'_id': parsed.netloc}, {'$set': {'target': target_hat}})
        if max_access - access <= access * 0.5:
            increase = 50
        else:
            increase = 0
        max_access_hat = max_access + increase
        self.db.domain.update_one({'_id': parsed.netloc}, {'$set': {'max_access': max_access_hat}})

    def close(self):
        print('Closing the mongo client...')
        self.client.close()
