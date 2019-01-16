from .settings import AVOID_ANCHOR, SECONDARY_ANCHOR, TERTIARY_ANCHOR
from .queue.priority_queue import PRIMARY_URL, SECONDARY_URL, TERTIARY_URL
from .extractor.object_recognition import is_org, is_person


def is_turn_page(anchor_text):
    """
    sure the turn-page button.
    :param anchor_text: the anchor text of the url accessed.
    :return: boolean.
    """
    len_anchor_text = len(anchor_text)

    if anchor_text.isalpha() and len_anchor_text is 1:
        return True

    if anchor_text.isdigit() and 1 <= len_anchor_text <= 2:
        return True

    return False


class URLScheduler(object):
    def __init__(self, url_filter, url_queue):
        self.url_filter = url_filter
        self.url_queue = url_queue

    def __call__(self, last_url, last_anchor_text, last_url_level, tree):
        """
        :param last_url: the url last accessed.
        :param last_anchor_text: the anchor text of last url.
        :param last_url_level: level of last url.
        :param tree: dom tree
        """
        elements = tree.cssselect('body a:link')
        for element in elements:
            url = self.url_filter(last_url, element)
            if url is None:
                continue
            this_anchor_text = element.text_content().strip()

            if AVOID_ANCHOR.search(this_anchor_text):
                continue

            last_and_this_anchor_text = last_anchor_text + '`' + this_anchor_text

            if last_url_level == TERTIARY_URL:
                # retrieve "college|school|department..." url

                if TERTIARY_ANCHOR.search(this_anchor_text) or is_org(this_anchor_text) \
                        or is_turn_page(this_anchor_text):
                    self.url_queue.priority_push(url, last_and_this_anchor_text, TERTIARY_URL)
                    continue

                # likely to get faculty profiles list if the anchor text contains 'people' or 'faculty'.
                if SECONDARY_ANCHOR.search(this_anchor_text):
                    self.url_queue.priority_push(url, last_and_this_anchor_text, SECONDARY_URL)

            # the menu web page
            if last_url_level == SECONDARY_URL:

                # the anchor text is organization
                if TERTIARY_ANCHOR.search(this_anchor_text) or is_org(this_anchor_text):
                    if SECONDARY_ANCHOR.search(url):
                        self.url_queue.priority_push(url, last_and_this_anchor_text, SECONDARY_URL)
                    else:
                        self.url_queue.priority_push(url, last_and_this_anchor_text, TERTIARY_URL)
                    continue

                # if anchor text is digital, turn the page.
                if SECONDARY_ANCHOR.search(this_anchor_text) or is_turn_page(this_anchor_text):
                    self.url_queue.priority_push(url, last_and_this_anchor_text, SECONDARY_URL)
                    continue

                if is_person(this_anchor_text):
                    self.url_queue.priority_push(url, last_and_this_anchor_text, PRIMARY_URL)
