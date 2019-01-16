# -*- encoding: utf-8 -*-
"""
by Ken Yu
@ Tue Jul 18 18:43:49 2017

This module is used to confirm the AJAX dynamic HTML and render them by web-kit.
"""
from urllib.parse import urlparse
from urllib.error import URLError
from .get_static import Throttle, html_getter
from ..cacher import MongoCache
from ..extractor.extract_image import get_faces_number
from ..cleaner import CleanMenu
from ..settings import (LOGGING, AJAX_PATTERN, MENU_AJAX_MAX_VALUE,
                        PROFILE_AJAX_MIN_VALUE, SECONDARY_ANCHOR,
                        PAGE_LOAD_TIMEOUT, CHROME_DRIVER)
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from time import time
from string import ascii_lowercase, ascii_uppercase


def is_profile_ajax(html, last_access):
    """
	Determinate whether the profile web-page is AJAX HTML.
	:param html: HTML string.
	:param last_access: the URL last accessed.
	:return: boolean.
	"""
    cleaned = CleanMenu(html)
    tree = cleaned.root

    def exist_image():
        img_tags = tree.cssselect('img')
        if not img_tags:  # if there are no images, then return 0.5
            print(u'image: 0.5')
            return 0.5

        faces = []
        for img_tag in img_tags:
            image_link = img_tag.get('src', '')
            this_parsed = urlparse(image_link)
            if not this_parsed.netloc or not this_parsed.scheme and this_parsed.path:
                last_parsed = urlparse(last_access)
                image_link = last_parsed.scheme + '://' + last_parsed.netloc + this_parsed.path
            result = html_getter(image_link)
            image_bytes = result['html']
            if image_bytes:
                faces.append(get_faces_number(image_bytes))

        one_face = any([face == 1. for face in faces])
        if not one_face:  # if there is no no-face image, return 0.4
            print(u'There is no one-face!')
            print(u'image: 0.5')
            return 0.4

        if len(faces) > 3 and one_face:
            print(u'image: 0.3')
            return 0.3

        print(u'image: 0.1')
        return 0.1

    def exist_email():
        a_tags = tree.cssselect('a')  # there is no email address.
        if not any([a_tag.get('href', '').startswith('mailto') for a_tag in a_tags]):
            print(u'Email: 0.5')
            return 0.5

        print(u'Email: 0.1')
        return 0.1

    def exist_h():
        h123_tags = tree.cssselect('h1,h2,h3')
        h456_tags = tree.cssselect('h4,h5,h6')
        if not h123_tags and not h456_tags:
            print(u'Header: 0.4')
            return 0.4
        if not h123_tags and h456_tags:
            print(u'Header: 0.35')
            return 0.35
        if h123_tags and not h456_tags:
            print(u'Header: 0.3')
            return 0.3
        print(u'Header: 0.1')
        return 0.1

    def exist_p():
        p_tags = tree.cssselect('p')
        if not p_tags:
            print(u'Paragraph: 0.4')
            return 0.4
        paragraph = ' '.join([p_tag.text_content().strip() for p_tag in p_tags])
        if len(paragraph) <= 10:
            print(u'Paragraph: 0.3')
            return 0.3
        print(u'Paragraph: 0.1')
        return 0.1

    probability = exist_email() + exist_image() + exist_h() + exist_p()
    if probability > PROFILE_AJAX_MIN_VALUE or AJAX_PATTERN.search(html):
        LOGGING.info(u'The profile web-page is an AJAX HTML: {}'.format(probability))
        return True
    return False


def is_menu_ajax(html):
    """
	determinate whether the menu web-page is AJAX HTML.
	:param html: HTML string.
	:return: boolean.
	"""
    cleaned = CleanMenu(html)
    tree = cleaned.root
    anchor_key = SECONDARY_ANCHOR
    a_tags = filter(lambda x: not anchor_key.search(x.text_content()), tree.cssselect('a'))
    len_a_tags = len(a_tags)
    if len_a_tags < MENU_AJAX_MAX_VALUE or AJAX_PATTERN.search(html):
        LOGGING.info(u'The menu web-page is an AJAX HTML')
        return True
    return False


def timer(fn):
    def wrapper(*args, **kwargs):
        start_time = time()
        result = fn(*args, **kwargs)
        end_time = time()
        elapsed_time = end_time - start_time
        LOGGING.info(u'Elapsed time:{:.2f}'.format(elapsed_time))
        return result

    return wrapper


class BrowserRender(object):
    """
	Render the AJAX dynamic HTML with the phantomjs engine.
	"""

    def __init__(self, proxy=None, user_agent=None, throttle=Throttle(10), cache=MongoCache()):
        """
		:param proxy: ip string like 'ip:port'.
		:param user_agent: user agent string.
		:param throttle: interval time.
		:param cache: cache the the web-page downloaded into a local repository.
		"""
        # initialize a browser and its corresponding configure.
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--headless")

        # proxy_ip must be valid.
        if proxy and isinstance(proxy, (bytes, str)):
            print(u'Proxy IP {}'.format(proxy))
            self.chrome_options.add_argument('--proxy-server={}'.format(proxy))

        default_user_agent = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/67.0.3396.99 Safari/537.36')

        # the user_agent must be valid.
        user_agent = user_agent if user_agent and isinstance(user_agent, (bytes, str)) else default_user_agent
        self.chrome_options.add_argument('--user-agent="{}"'.format(user_agent))

        self.browser = webdriver.Chrome(CHROME_DRIVER, chrome_options=self.chrome_options)

        self.timeout = PAGE_LOAD_TIMEOUT
        self.browser.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        self.throttle = throttle
        self.cache = cache

    def quit(self):
        try:
            self.browser.quit()
        except OSError:
            pass

    def restart(self):
        self.quit()
        self.browser = webdriver.Chrome(CHROME_DRIVER, chrome_options=self.chrome_options)
        self.browser.set_page_load_timeout(self.timeout)

    def html_getter(self, url):
        """
		Crawl the web-page by several times after TimeoutException.
		:param url: URL string.
		:return: <dict> like {'html':html,'status_code':'AJAX'}
		"""
        try:
            self.browser.get(url)
        except TimeoutException:
            print(u'Time out and Incomplete!')
            return {'html': self.browser.page_source, 'status_code': 'Incomplete',
                    'actual_url': self.browser.current_url}
        except (WebDriverException, URLError):
            print(u'Restart the browser...')
            self.restart()
            return {'html': None, 'status_code': 'Unamendable Error', 'actual_url': self.browser.current_url}
        else:
            print(u'Succeed to render the Ajax webpage.')
            return {'html': self.browser.page_source, 'status_code': 200, 'actual_url': self.browser.current_url}

    def click_letter_element(self, letters):
        results = []
        for letter in letters:
            try:
                elem = self.browser.find_element_by_link_text(letter)
            except NoSuchElementException:
                print(u'Cannot find the element: {}!'.format(letter))
                break
            else:
                try:
                    elem.click()
                except TimeoutException:
                    continue
                else:
                    results.append({'html': self.browser.page_source, 'status_code': 200,
                                    'actual_url': self.browser.current_url})
        return results

    def click_digit_element(self):
        page = 2
        results = []
        while 1:
            try:
                elem = self.browser.find_element_by_link_text(str(page))
            except NoSuchElementException:
                print(u'Cannot find the element: {}!'.format(page))
                break
            else:
                page += 1
                try:
                    elem.click()
                except TimeoutException:
                    continue
                else:
                    results.append({'html': self.browser.page_source, 'status_code': 200,
                                    'actual_url': self.browser.current_url})
        return results

    @timer
    def menu_getter(self, url):
        """
		:param url: URL string.
		:return: <list> [dict, dict, ...]
		"""
        results = []
        if self.throttle:
            self.throttle.wait(url)
        result = self.html_getter(url)
        results.append(result)
        if result['status_code'] != 'Unamendable Error':
            results.extend(self.click_letter_element(ascii_uppercase))
            results.extend(self.click_letter_element(ascii_lowercase))
            results.extend(self.click_digit_element())
        return results

    @timer
    def profile_getter(self, url):
        """
		:param url: URL string.
		:return: <dict> like {'html':html,'status_code':'AJAX'}
		"""
        if self.throttle:
            self.throttle.wait(url)
        result = self.html_getter(url)
        if self.cache:
            self.cache[url] = result
        return result
