from pymongo import MongoClient
from ..settings import ORGANIZATION_NAME, UPDATE_INTERVAL, MONGO_HOST
from collections import defaultdict


class CrawlStatus(object):
    OUTSTANDING, PROCESSING, COMPLETE = range(3)

    def __init__(self):
        self.client = MongoClient(MONGO_HOST)
        self.queue = self.client.get_database('cache').get_collection('crawl_queue')
        self.store = self.client.get_database('target_db').get_collection(ORGANIZATION_NAME)

        self.last_accumulate_per_mac = {}
        self.accumulates_per_mac = defaultdict(list)
        self.max_count = int(10 * 60 / UPDATE_INTERVAL)
        self.is_alive = True

    def status_per_mac(self, host):
        this_accumulate = self.queue.count({'host': host, 'status': self.COMPLETE})
        self.accumulates_per_mac[host].append(this_accumulate)

        if len(self.accumulates_per_mac[host]) >= self.max_count:
            self.is_alive = False if len(set(self.accumulates_per_mac[host])) is 1 else True
            self.accumulates_per_mac[host].clear()

        this_complete = this_accumulate - self.last_accumulate_per_mac.get(host, 0)
        self.last_accumulate_per_mac[host] = this_accumulate

        return {'alive': self.is_alive, 'complete': this_complete, 'accumulate': this_accumulate}

    def total_status(self):
        completes = self.queue.count({'status': self.COMPLETE})
        outstandings = self.queue.count({'status': self.OUTSTANDING})
        targets = self.store.count()
        missings = (completes - targets) / completes if completes > 0 else 0

        return [outstandings, completes, targets, missings]
