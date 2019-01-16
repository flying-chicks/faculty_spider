from urllib.parse import urlparse, urljoin
import re
from .settings import LOGGING


class URLFilter(object):
    def __init__(self, url_queue, access_limit, seed_domain):
        self.url_queue = url_queue
        self.access_limit = access_limit
        self.seed_domain = seed_domain

    def __call__(self, last_url, elem, is_image_url=False):
        """
          Select the absolute url.
          Control the url under the domain.
          :last_url: url accessed last.
          :elem: <lxml.html.Element>
          """

        if is_image_url:
            url = elem.get('src')
        else:
            url = elem.get('href')

        if url is None:
            return None

        this_parsed = urlparse(url)

        # remove urls those are email address.
        mail_pattern = re.compile('@|mailto', flags=re.I)
        if re.search(this_parsed.path) or mail_pattern.search(this_parsed.netloc):
            LOGGING.info(u'{} is email url. Skip it'.format(url))
            return None

        # remove urls whose format is not 'html' or 'htm'
        if is_image_url:
            pattern = re.compile('(?:jpeg|jpg|png|gif)', flags=re.I)
        else:
            pattern = re.compile('(?:html|htm|php|asp|net|jsp)', flags=re.I)

        if '.' in re.sub('\.{2,}', '', this_parsed.path) and not pattern.search(this_parsed.path):
            LOGGING.info(u'{} is not a html. Skip it!'.format(url))
            return None

        # every url must be a absolute url
        if this_parsed.path and not (this_parsed.netloc and this_parsed.scheme):
            LOGGING.info(u'{} is a relative url. Autocomplete it!'.format(url))
            url = urljoin(last_url, url)

        # skip the urls that contain news/events/facts/blog
        if re.search('news|events|facts|blog', url, flags=re.I):
            LOGGING.info(u'{} is news or events url. Skip it!'.format(url))
            return None

        # skip the urls that contain search/find.
        if re.search('(?<!re)search|find', url, flags=re.I):
            LOGGING.info(u'{} is aim at searching. Skip it!'.format(url))
            return None

        # every url must have a protocol and within the domain of seed url
        this_parsed = urlparse(url)
        if not is_image_url and not this_parsed.netloc.__contains__(self.seed_domain):
            LOGGING.info(u'{} exceeds the domain. Skip it!'.format(url))
            return None

        # remove urls those are trap.
        if elem.get('display') == 'none' or elem.get('visible') == 'hidden' or \
                re.search('display\s*?:\s*?none|visible\s*?:\s*?hidden', elem.get('style', ''), flags=re.I):
            LOGGING.info(u'{} is a honey pot. Skip it!'.format(url))
            return None

        # remove the urls whose path length is more than 10.
        if len(urlparse(url).path.split('/')) >= 10:
            return None

        # remove urls already existing in queue.
        if not is_image_url and url in self.url_queue:
            return None

        # remove the urls exceeding the max access.
        if not is_image_url and self.access_limit.exceed_max_access(url):
            LOGGING.info(u'{} exceeds the max access. Skip it!'.format(url))
            return None

        # put the urls into the queue.
        LOGGING.info(u'Putting {0} into the queue...'.format(url))
        return url
