# -*- coding: utf-8 -*-
"""
This is a module that can intelligently retain information on university faculty.
1. single-thread model.
2. multi-thread model.
3. multi-thread + multi-process model.

By Kennis Yu
"""

from .downloader.get_dynamic import BrowserRender, is_profile_ajax, is_menu_ajax
from .downloader.get_static import safe_from_string, SafeDownload
from .extractor.extract_image import get_best_image, safe_image_save
from .cleaner import CleanMenu, clean_profile
from .filter import URLFilter
from .scheduler import URLScheduler
from .queue.priority_queue import PRIMARY_URL, SECONDARY_URL, TERTIARY_URL, MongoPriorityQueue
from .saver import InfoStore
from .utils.mongo_control import AccessLimit
from .utils.get_host_ip import get_host_ip
from .settings import LOGGING, DOMAIN_STRIP, IMAGES_PATH

from urllib.parse import urlparse
import re
from os.path import exists
from os import mkdir


class Assembly(object):
    """docstring for LinkCrawler"""

    def __init__(self, seed_url, employer):
        """
        :param employer: University or college name.
        :param seed_url: University or college home-page url.
        """
        seed_url_parsed = urlparse(seed_url)
        pattern = re.compile('\w*?\.?(\w+?)\.edu')
        if DOMAIN_STRIP and pattern.search(seed_url_parsed.netloc):
            seed_domain = pattern.findall(seed_url_parsed.netloc)[0]
        else:
            seed_domain = seed_url_parsed.netloc[seed_url_parsed.netloc.index('.') + 1:] \
                if seed_url_parsed.netloc.startswith(('www', 'web', 'www1')) else seed_url_parsed.netloc

        self.employer = employer
        self.url_queue = MongoPriorityQueue()  # initialize the url queue.
        self.url_queue.priority_push(seed_url, employer, TERTIARY_URL)  # put the seed_url into the queue.

        self.access_limit = AccessLimit()  # initialize the AccessLimit

        self.url_filter = URLFilter(self.url_queue, self.access_limit, seed_domain)

        self.url_scheduler = URLScheduler(self.url_filter, self.url_queue)

        self.browser = BrowserRender()  # initialize the browser.

        self.target_db = InfoStore(db='target_db', collection=self.employer)
        self.no_target_db = InfoStore(db='no_target_db', collection='no_target_col')

        self.image_path = IMAGES_PATH + '/' + self.employer
        if not exists(self.image_path):
            mkdir(self.image_path)

        self.host_ip = get_host_ip()

    def _process_profile(self, url, anchor_text, url_level, html, tree, downloader):
        """
        process profile webpages.
        :param url: url string.
        :param anchor_text: anchor text string.
        :param url_level: url level.
        :param html: html string.
        :param tree: DOM tree.
        :param downloader: faculty_spider.downloader.get_static.SafeDownload.
        """
        # if html is ajax, redownload it by browser.
        if is_profile_ajax(html, url):
            LOGGING.info(u'{} is an ajax profile web-page. Render it!'.format(url))
            result = self.browser.profile_getter(url)
            html = result['html'] if result['html'] is not None else html
            tree = safe_from_string(html)

        # extract the information from the DOM tree.
        LOGGING.info(u'{0} is a target and extracted info!'.format(url))
        anchor_text_list = anchor_text.split('`')
        name = anchor_text_list[-1] if anchor_text_list else ''
        LOGGING.info(u'name:{}'.format(name))

        # choose the best image, when where are many images in the profile web-pages.
        best_image_url, best_image_bytes = get_best_image(url, name, tree.cssselect("img"), downloader, self.url_filter)
        LOGGING.info(u'the better image url is {}'.format(best_image_url))
        if best_image_url and best_image_bytes and name:
            safe_image_save(self.image_path + '/' + name, best_image_url, best_image_bytes)

        # store the web-page into the database named 'target_db'
        self.target_db.save_target(url, html, clean_profile(tree), name, anchor_text, best_image_url)

        # update the max access in this domain.
        self.access_limit.update_max_access(url)

        # get and schedule the url from the HTML.
        self.url_scheduler(url, anchor_text, url_level, tree)

    def _process_menu(self, url, anchor_text, url_level, html):
        """
        process menu webpages.
        :param url: url string.
        :param anchor_text: anchor text string.
        :param url_level: url level.
        :param html: html string.
        """
        if not is_menu_ajax(html):
            # clean it by dropping the noisy elements.
            cleaned = CleanMenu(html)
            self._process_others(url, anchor_text, url_level, html, cleaned.root)
            return None

        LOGGING.info(u'{} is an ajax menu web-page. Render it!'.format(url))
        for result in self.browser.menu_getter(url):
            if result['html'] is None:
                continue

            cleaned = CleanMenu(result['html'])
            self.url_scheduler(url, anchor_text, url_level, cleaned.root)

    def _process_others(self, url, anchor_text, url_level, html, tree):
        """
        process other webpages except menu and profile webpages.
        :param url: url string.
        :param anchor_text: anchor text string.
        :param url_level: url level.
        :param html: html string.
        :param tree: DOM tree.
        """
        # store the web-page into the database named 'no_target_db'.
        self.no_target_db.save_not_target(url, html, clean_profile(tree))
        self.url_scheduler(url, anchor_text, url_level, tree)

    def __call__(self, *args, **kwargs):
        """
        :pred: function which tell whether the web-page is a target web.
        :kwargs: key words arguments of download.
        """
        download = SafeDownload(*args, **kwargs)
        url = url_level = anchor_text = ''

        while 1:
            try:
                # get a url from queue.
                url, anchor_text, url_level = self.url_queue.pop()
                LOGGING.info(u'Get {0} from the queue...'.format(url))
            except KeyError:  # exception raised means the empty of queue.
                break
            else:
                self.url_queue.complete(url, self.host_ip)
            finally:
                self.url_queue.close()

            # retrieve html, try again with new IP only when an error rises.
            result = download(url)

            # set the redirect url into COMPLETE.
            if result.get('actual_url') and result.get('actual_url') != url:
                if self.url_queue.is_complete(result.get('actual_url')):
                    continue
                self.url_queue.push_redirect(result.get('actual_url'))

            html = result['html']
            # check validation of html.
            if html is None:
                LOGGING.info(u'the html is None, then continue!')
                continue

            tree = safe_from_string(html)

            # if the HTML is a target, extract its information and save its content.
            if url_level == PRIMARY_URL:
                self._process_profile(url, anchor_text, url_level, html, tree, download)

            if url_level == SECONDARY_URL:
                self._process_menu(url, anchor_text, url_level, html)

            if url_level == TERTIARY_URL:
                self._process_others(url, anchor_text, url_level, html, tree)

        self.target_db.close()
        self.no_target_db.close()
        self.browser.quit()
        self.access_limit.close()
