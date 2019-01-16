from .assembly import Assembly
from .settings import LOGGING
import multiprocessing as mlp
import threading
import time


def thread_crawler(max_threads, seed_url, employer, *args):
    sleep_time = 3
    threads = []

    crawl = Assembly(seed_url, employer)
    LOGGING.info(u'Start the children threads!')
    while threads or crawl.url_queue:
        for thread in threads:
            if not thread.isAlive():
                LOGGING.info(u'Thread({}) is dead and removed from the pool!'.format(thread.ident))
                threads.remove(thread)  # remove the stopped thread
        while crawl.url_queue and len(threads) < max_threads:
            thread = threading.Thread(target=crawl, args=args)
            thread.setDaemon(True)  # the main thread can stop when receiving a Ctrl-C
            thread.start()
            LOGGING.info(u'The new thread({}) is created and put into the pool.'.format(thread.ident))
            threads.append(thread)
        time.sleep(sleep_time)
    LOGGING.info(u'All children threads end up!')


def multiprocess_crawler(max_processes, *args):
    num_cpus = mlp.cpu_count()
    if max_processes > num_cpus:
        LOGGING.info(u'Because max_processes is larger than num_cpus, max_processes = num_cpus')
        max_processes = num_cpus
    processes = []
    LOGGING.info(u'Starting {} processes.'.format(max_processes))
    for i in range(max_processes):
        process = mlp.Process(target=thread_crawler, args=args)
        process.start()
        processes.append(process)
        time.sleep(3)
    for process in processes:
        process.join()
    LOGGING.info(u'All children processes finish!')