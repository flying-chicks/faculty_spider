# -*- encoding: utf-8 -*-
"""
by Kennis Yu
@ Tue Jul 18 18:43:49 2017
"""

from urllib import robotparser
from urllib.parse import urlparse
from datetime import datetime
from random import choice
from time import sleep
from numpy import tile
import lxml.html
import requests
from ..cacher import MongoCache
from ..settings import ROBOT_FILE_CENSOR
from lxml.etree import XMLSyntaxError, ParserError
from numpy.random import normal
from requests.exceptions import ConnectionError, Timeout, ProxyError


class SafeRobotFileParser(robotparser.RobotFileParser):
    def __init__(self, url=''):
        """
        a safe robot file parser.
        :param url: URL string.
        """
        robotparser.RobotFileParser.__init__(self, url)

    def safe_can_fetch(self, user_agent, url):
        try:
            return self.can_fetch(user_agent, url)
        except(KeyError, Exception) as e:
            print(e)
            return True

    def safe_read(self):
        try:
            self.read()
        except (IOError, IndexError, Exception) as e:
            print(e)
            return True


class AllowCrawl(object):
    def __init__(self):
        """
        docstring for AllowCrawl
        must obey Robots Exclusion Protocol and don't collect the URLs it disallows.
        """
        super(AllowCrawl, self).__init__()
        self.last_accessed = {}

    def __call__(self, url):
        parsed = urlparse(url)

        if parsed.scheme and parsed.netloc and isinstance(parsed.scheme, (str, bytes)) \
                and isinstance(parsed.netloc, (str, bytes)):
            protocol_domain = parsed.scheme + '://' + parsed.netloc
        else:
            return True

        if self.last_accessed.get(protocol_domain) is None:
            rp = SafeRobotFileParser()
            rp.set_url(protocol_domain + '/robots.txt')
            if rp.safe_read():
                return True
            self.last_accessed[protocol_domain] = rp
            return rp.safe_can_fetch('*', url)

        return self.last_accessed[protocol_domain].safe_can_fetch('*', url)


AMENDABLE_ERROR = 'Amendable Error'


def html_getter(url, post_data=None, ip=None, headers=None, timeout=15, retry=3):
    """
    :url: <str> where a html can be retained.
    :ip: <dict> proxy.
    :headers: <dict> request headers.
    :timeout: <int> maxsize second that valid html can be retained. default 15.
    :retry: <int> maxsize times that valid html can be accessed after exception. default 3.
    """
    if not isinstance(url, (str, bytes)) or not url:
        print(u'The URL is invalid!')
        return {'html': None, 'status_code': 'Invalid URL'}

    if ROBOT_FILE_CENSOR:
        # every URL must obey the robots.txt
        allow_crawler = AllowCrawl()
        if not allow_crawler(url):
            print(u'The URL is disallowed by robots.txt')
            return {'html': None, 'status_code': 'Disallowed'}

    try:
        print(u'Clawing {0}...'.format(url))
        if post_data:
            response = requests.post(url, data=post_data, proxies=ip, headers=headers, timeout=timeout)
        else:
            response = requests.get(url, proxies=ip, headers=headers, timeout=timeout)  # a door dog

        if 200 <= response.status_code < 300:
            print(u"Succeed to get the html!")
            if response.encoding:
                return {'html': safe_decode(response.content, response.apparent_encoding),
                        'status_code': response.status_code, 'actual_url': response.url}
            else:
                return {'html': response.content, 'status_code': response.status_code, 'actual_url': response.url}

        if 300 <= response.status_code < 500:
            print(u'Re-direct or 4XX User terminal errors!')
            return {'html': None, 'status_code': response.status_code, 'actual_url': response.url}

        if 500 <= response.status_code < 600:
            print(u'5XX HTTP errors!')
            if retry:
                # retry if the service error.
                print(u"Retry: {0}".format(retry))

                # Recursive results need to be recursively returned
                return html_getter(url, post_data, ip, headers, timeout, retry - 1)
            else:
                print(u"Failed to get the html!")
                return {'html': None, 'status_code': response.status_code, 'actual_url': response.url}

    except (Timeout, ProxyError, ConnectionError) as e:  # re-crawler of ConnectTimeout and ReadTimeout
        print(e)
        if retry:
            print(u"Retry: {0}".format(retry))
            return html_getter(url, post_data, ip, headers, timeout,
                               retry - 1)  # Recursive results need to be recursively returned
        else:
            print(u"Failed to get the html!")
            return {'html': None, 'status_code': AMENDABLE_ERROR}
    except Exception as e:
        print(e)
        return {'html': None, 'status_code': e}


def truncated_normal(mu, sigma):
    """
    :param mu: <float> the expect.
    :param sigma: <float> scope [mu-sigma, mu+sigma]
    :return: <float> a random number obey the truncated normal distribution.
    """
    while 1:
        result = normal(loc=mu, scale=sigma)
        if mu - sigma <= result <= mu + sigma:
            return result


class Throttle(object):
    def __init__(self, delay=10.0):
        """
        sleep flexibly.
        :param delay: second
        """
        if delay < 5.0 or delay is None:
            delay = 5.0
        self.delay = truncated_normal(delay, 3.0)
        self.domains = {}

    def wait(self, url):
        domain = urlparse(url).netloc
        last_accessed = self.domains.get(domain)  # the time of URL last accessed.
        if last_accessed is not None:
            timedelta = datetime.now() - last_accessed
            wait_sec = round(self.delay - timedelta.total_seconds(), 2)
            if wait_sec > 0:
                print(u'sleep {} sec'.format(wait_sec))
                sleep(wait_sec)
        self.domains[domain] = datetime.now()


class SafeDownload(object):
    def __init__(self, proxy_pool=None, headers_pool=None, throttle=Throttle(10), cache=MongoCache()):
        """
        be able to:
        1. cache HTML retrieved.
        2. pair proxies and headers.
        3. sleep flexibly
        4. handle the ConnectionError, Timeout, and ProxyError arising from invalid proxy.
        :param proxy_pool: list or list-like of more than one dict.
        :param headers_pool: list or list-like of more than one dict.
        :param throttle:
        :param cache:
        """
        proxy_pool = [{}] if proxy_pool is None else proxy_pool
        headers_pool = [{}] if headers_pool is None else headers_pool
        proxy_pool_size = len(proxy_pool)
        headers_pool_size = len(headers_pool)
        if proxy_pool_size > headers_pool_size:
            times, remainder = divmod(proxy_pool_size, headers_pool_size)
            new_headers_pool = tile(headers_pool, times).tolist()
            new_headers_pool.extend(headers_pool[:remainder])
        else:
            new_headers_pool = headers_pool[:proxy_pool_size]
        self.headers_pool = new_headers_pool
        self.proxy_pool = proxy_pool
        self.proxy_pool_indices = range(proxy_pool_size)
        self.throttle = throttle
        self.cache = cache

    def cached(self, url, *args, **kwargs):
        """
        cache the html into a local repository.
        :param url: url string.
        :param args: arguments of html_getter.
        :param kwargs:
        :return: <dict>
        """
        result = None
        if self.cache:
            try:
                result = self.cache[url]  # the result not cached.
            except KeyError as e:
                print(e)
                pass
            else:
                if 500 <= result['status_code'] < 600:  # Service Error and need to re-download the html
                    print(u'Service Error and need to re-download the html!')
                    result = None
        if result is None:
            if self.throttle:
                self.throttle.wait(url)
            result = html_getter(url, *args, **kwargs)
            if self.cache and result['status_code'] != AMENDABLE_ERROR:
                self.cache[url] = result
                self.cache.close()
        return result

    def select_proxy_headers(self):
        """
        An ip is pair up with a headers, then selected randomly.
        :returns: proxy<dict>, headers<dict>
        """
        proxy_index = choice(self.proxy_pool_indices)
        headers_index = proxy_index
        proxy = self.proxy_pool[proxy_index]
        headers = self.headers_pool[headers_index]
        return proxy, headers

    def __call__(self, url, post_data=None):
        """
        retry to download html by several times.
        :param url: url string.
        :param post_data: post data.
        :return: result.
        """
        n_retry_proxy = 3  # times of retrying a new proxy after 'Amendable Error' rise
        n_trap = 3  # times of getting lost in invalid proxy pool.
        invalid_proxy_pool = []  # invalid proxy pool
        ip, headers = self.select_proxy_headers()
        result = self.cached(url, post_data, ip, headers)

        # if 'Amendable Error' rises, retry a new ip to retrive the HTML
        while result['status_code'] == AMENDABLE_ERROR and n_retry_proxy:

            print(u'{} is an invalid ip and put into the invalid ip pool!'.format(ip))

            # put invalid ip into invalid ip pool.
            invalid_proxy_pool.append(ip)

            # select a new ip from proxy pool.
            ip, headers = self.select_proxy_headers()

            # if the new ip in invalid ip set then continue.
            if ip in invalid_proxy_pool:
                n_trap = n_trap - 1
                if n_trap is 0:
                    break
                continue

            print(u'Retry {0}, new valid ip: {1}'.format(n_retry_proxy, ip))
            result = self.cached(url, post_data, ip, headers)

            n_retry_proxy = n_retry_proxy - 1

        if result['status_code'] == AMENDABLE_ERROR and (n_retry_proxy is 0 or n_trap is 0):
            print(u'Fail to retry new ip!')
        return result


def safe_from_string(html):
    """
    safely transform html into lxml.tree.
    """
    try:
        tree = lxml.html.fromstring(html)
    except ValueError as e:
        print(e)
        try:
            html = bytes(bytearray(html, encoding='utf-8'))
        except UnicodeEncodeError:
            html = bytes(bytearray(html, encoding='GB18030'))
        tree = lxml.html.fromstring(html)
    except (XMLSyntaxError, ParserError, ValueError) as e:
        print(e)
        tree = lxml.html.fromstring('None')
    return tree


def safe_decode(raw_s, encoding):
    try:
        return raw_s.decode(encoding)
    except UnicodeDecodeError:
        if encoding.lower() == 'utf-8':
            return safe_decode(raw_s, 'gb18030')
        if encoding.lower() == 'gb18030':
            return safe_decode(raw_s, 'utf-8')
