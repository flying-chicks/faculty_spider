from base.main import multiprocess_crawler
from base.settings import MAX_PROCESSES, MAX_THREADS, SEED_URL, ORGANIZATION_NAME
from base.utils.mongo_options import MongoHeadersPool


headers_pool = MongoHeadersPool().export_data(200)
proxy_pool = [{}]
multiprocess_crawler(MAX_PROCESSES, MAX_THREADS, SEED_URL, ORGANIZATION_NAME, proxy_pool, headers_pool)
