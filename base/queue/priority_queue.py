from .mongo_queue import MongoQueue
from pymongo.errors import DuplicateKeyError
from datetime import datetime


PRIMARY_URL, SECONDARY_URL, TERTIARY_URL = range(3)


class MongoPriorityQueue(MongoQueue):
    """
    docstring for MongoPriorityQueue
    """

    def __init__(self, client=None, timeout=300):
        MongoQueue.__init__(self, client, timeout)

    def priority_push(self, url, anchor_text, level):
        try:
            self.db.crawl_queue.insert(
                {'_id': url, 'anchor_text': anchor_text, 'level': level, 'status': self.OUTSTANDING})
        except DuplicateKeyError:
            pass

    def push_redirect(self, actual_url):
        """
        push the unique url into the queue.
        """
        try:
            self.db.crawl_queue.insert({'_id': actual_url, 'status': self.COMPLETE})
        except DuplicateKeyError:
            # the url has already been in the queue and the url will be not pushed into queue.
            pass

    def pop(self):
        def find(level):
            record = self.db.crawl_queue.find_and_modify(
                query={'status': self.OUTSTANDING, 'level': level},
                update={'$set': {'status': self.PROCESSING, 'timestamp': datetime.now()}})
            return record

        primary_level_record = find(PRIMARY_URL)
        if primary_level_record:
            return primary_level_record['_id'], primary_level_record['anchor_text'], PRIMARY_URL

        secondary_level_record = find(SECONDARY_URL)
        if secondary_level_record:
            return secondary_level_record['_id'], secondary_level_record['anchor_text'], SECONDARY_URL

        tertiary_level_record = find(TERTIARY_URL)
        if tertiary_level_record:
            return tertiary_level_record['_id'], tertiary_level_record['anchor_text'], TERTIARY_URL

        self.repair()
        raise KeyError()
