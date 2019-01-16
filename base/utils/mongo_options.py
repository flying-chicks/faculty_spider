# -*- encoding: utf-8 -*-
"""
by Ken Yu
@ Tue Jul 18 18:43:49 2017

validate URL http://icanhazip.com/
"""

from pymongo import MongoClient
from .safe_connect_mongo import MongoProxy
from ..downloader.get_static import safe_from_string, html_getter
from ..settings import MONGO_HOST
from pymongo.errors import DuplicateKeyError
from time import sleep
from queue import Queue
import threading
from datetime import timedelta, datetime
import codecs


class MongoProxiesPool(object):
    def __init__(self, client=None, expires=timedelta(days=30)):
        """
        :client: instance of pymongo.mongo_client.MongoClient.
        :expires:instance of datetime.timedelta.update or delete the webpage if beyond expires.
        """
        # connect to mongodb
        self.client = MongoProxy(MongoClient(host=MONGO_HOST, port=27017, socketTimeoutMS=30000,
                                             connectTimeoutMS=30000)) if client is None else MongoProxy(client)

        # connect to a database named 'cache' in mongodb
        self.db = self.client.cache

        # ProxiesPool is a collection in cache
        # create a timestamp index to ProxiesPool
        self.db.ProxiesPool.create_index('timestamp',
                                         expireAfterSeconds=expires.total_seconds())

    def __getitem__(self, protocol):
        """
        load the ips according to the protocol.
        """
        protocol = protocol.lower()
        records = self.db.ProxiesPool.find({'protocol': protocol})
        if records.count():
            proxies = [{record['protocol']: record['ip']} for record in records]
            return proxies
        else:
            raise IndexError('There is no {0} record!'.format(protocol))

    def __setitem__(self, protocol, ip):
        """
        save the ip and protocol
        """
        protocol = protocol.lower()
        record = {'ip': ip, 'protocol': protocol, 'timestamp': datetime.utcnow()}
        self.db.ProxiesPool.insert_one(record)

    def __len__(self):
        """
        return the number of proxy ips.
        """
        count = self.db.HeadersPool.count()
        return count

    def clean(self):
        self.db.ProxiesPool.drop()

    def close(self):
        print('Closing the mongo client...')
        self.client.close()


def ip_get_by_html(queue, url='http://www.xicidaili.com/'):
    """
    :queue <Queue.Queue>
    """
    headers = {'User-Agent': ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                              "Chrome/59.0.3071.115 Safari/537.36")}
    result = html_getter(url, headers=headers)
    if result['html'] is None:
        return None
    tree = safe_from_string(result['html'].strip())
    for elem in tree.cssselect('table tr')[2:]:
        results = elem.cssselect('td')
        if len(results) <= 5:
            continue
        ip = results[1].text_content().strip()
        port = results[2].text_content().strip()
        protocol = results[5].text_content().strip()
        queue.put_nowait({'protocol': protocol, 'ip': ip + ':' + port})


def ip_get_by_api(queue, api='http://tvp.daxiangdaili.com/ip/?tid=557857422543148&num=1000&category=2'):
    """
    :param queue: :queue <Queue.Queue>
    :param api: url
    """
    headers = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                              'Chrome/59.0.3071.115 Safari/537.36')}
    result = html_getter(api, headers=headers)
    if result['html'] is None:
        return None
    results = result['html'].strip().split('\r\n')
    for ret in results:
        queue.put_nowait({'protocol': 'http', 'ip': ret.strip()})


def validate_save(queue):
    proxies_pool = MongoProxiesPool()
    url = 'http://icanhazip.com/'
    headers = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                              'Chrome/59.0.3071.115 Safari/537.36')}
    result = html_getter(url, headers=headers)
    text_raw = result['html']
    if text_raw is None:
        return None

    while not queue.empty():
        receive = queue.get_nowait()
        proxy = {receive['protocol']: receive['ip']}
        result = html_getter(url=url, ip=proxy, headers=headers)
        text_proxy = result['html']
        if text_proxy is None:  # cannot return the html then the proxy is not effective
            print(u'{} is not effective!'.format(proxy))
            continue
        if text_proxy != text_raw:
            print(u'{} is effective.'.format(proxy))
            proxies_pool[receive['protocol']] = receive['ip']
        else:
            print(u'{} is not effective!'.format(proxy))
        sleep(10)


SLEEP_TIME = 2  # the interval between threads


def threaded_get_ip(url, max_threads=15, ip_getter=ip_get_by_api):
    """
    retrieve, validate and store proxy IP by multiple threads.
    :param url: the URL retrieving proxy IP.
    :param max_threads: <unsigned int>  max threads number.
    :param ip_getter: function retrieving proxy IP.
    """
    queue = Queue(-1)
    threads = []  # thread pool
    producer_thread = threading.Thread(target=ip_getter, args=(queue, url))
    producer_thread.setDaemon(True)
    producer_thread.start()
    producer_thread.join()

    # create threads in batch
    for i in range(max_threads):
        consumer_thread = threading.Thread(target=validate_save, args=(queue,))
        consumer_thread.setDaemon(True)
        threads.append(consumer_thread)

    # start threads in batch
    for i in range(max_threads):
        threads[i].start()
        sleep(SLEEP_TIME)  # the interval between threads

    # check whether the thread is stopped in batch
    for i in range(max_threads):
        threads[i].join()


# ==============================================================================
class MongoHeadersPool(object):
    def __init__(self, client=None):
        self.client = MongoProxy(MongoClient(host=MONGO_HOST, port=27017, socketTimeoutMS=30000,
                                             connectTimeoutMS=30000)) if client is None else MongoProxy(client)
        self.db = self.client.cache

    def import_data(self, filename, sep='\n'):
        with codecs.open(filename, mode='r', encoding='GB18030') as fr:
            text = fr.read()
            for line in text.split(sep):
                try:
                    self.db.HeadersPool.insert_one({'_id': line.strip()})
                except DuplicateKeyError:  # duplicate key then skip
                    continue

    def __len__(self):
        """
        return the number of proxy ips.
        """
        count = self.db.HeadersPool.count()
        return count

    def clean(self):
        self.db.HeadersPool.drop()

    def insert_data(self, headers):
        try:
            self.db.HeadersPool.insert_one({'_id': headers})
        except DuplicateKeyError:  # duplicate key then skip
            print(u'duplicate key error!')

    def export_data(self, n=20):
        records = self.db.HeadersPool.find({})
        if self.db.HeadersPool.count():
            headers = [{'User-Agent': record['_id']} for record in records][:n]
            return headers
        else:
            raise IndexError('There is no record!')

    def close(self):
        print('Closing the mongo client...')
        self.client.close()
