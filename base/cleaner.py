# encoding: utf-8
"""
by Ken Yu
@ Tue Jul 18 18:43:49 2017
"""
import re
from .downloader.get_static import safe_from_string
from lxml.html import tostring
from string import punctuation, whitespace


class CleanMenu(object):
    regexps = {
        'replaceBrs': re.compile("(<br[^>]*>\s*){2,}", re.I),

        'replaceFonts': re.compile("<(/?)font[^>]*>", re.I),

        'unlikelyCandidates': re.compile("combx|comment|community|disqus|extra|foot|header|menu|symbol|svg|"
                                         "remark|rss|shoutbox|sidebar|sponsor|ad-break|agegate|noscript|script|"
                                         "pagination|pager|popup|tweet|twitter|facebook|logo|banner|copyright", re.I),

        'okMaybeItsACandidate': re.compile("and|article|body|column|main|shadow|content", re.I),

        'dropComments': re.compile('<!--[\w\W]*?-->')
    }

    def __init__(self, html):
        # fix the wrong embedded tags
        html = self.regexps['replaceBrs'].sub("</p><p>", html)
        html = self.regexps['replaceFonts'].sub("<\g<1>span>", html)
        html = self.regexps['dropComments'].sub("", html)
        self.html = html
        self.root = safe_from_string(html)
        self.drop_noise_elements(self.root)
        self.cleaned_html = tostring(self.root, pretty_print=True)

    def __drop__(self, parent, pred):
        children = parent.getchildren()
        for child in children:
            if pred(child):
                parent.remove(child)
            else:
                self.__drop__(child, pred)

    def DropCondition(self, elem):
        # drop noise tags
        def drop_noise_tags(element):
            noise_tags = ("meta", "link", "script", "style", "form", "header", "nav",
                          "footer", "object", "textarea", "video")
            if element.tag in noise_tags:
                return 1

        # drop elements whose values of id/class are wrong.
        def drop_noise_values(element):
            unlikely_match_string = element.attrib.get('id', '') + ' ' + element.attrib.get('class', '')
            if element.tag != 'body' and not self.regexps['okMaybeItsACandidate'].search(unlikely_match_string) \
                    and self.regexps['unlikelyCandidates'].search(unlikely_match_string):
                return 1

        def drop_noise_images(element):
            caution_tags = ["ul", "ol", "table", "div"]
            if element.tag not in caution_tags:
                return 0
            children = element.getchildren()
            n_img_tags = 0
            for child in children:
                for descent in child.getchildren():
                    if descent.tag == 'img' or descent.attrib.get('style', '').__contains__('background-image'):
                        n_img_tags += 1
            if n_img_tags >= 2:
                return 1

        def drop_null_text(element):
            # drop null text elements.
            if element.tag in ["p", "span", "article"]:
                content = element.text_content()
                length = len(content)
                if length == 0:
                    return 1
                num_punctuation = 0
                for char in content:
                    if char in punctuation or char in whitespace:
                        num_punctuation += 1
                if length * 2. / 3. <= num_punctuation <= length:
                    return 1

        def drop_useless_href(element):
            # drop the useless href
            if element.tag == 'a' and element.attrib.get('href', '').startswith('#'):
                return 1

        result = (drop_noise_tags(elem) or drop_noise_values(elem) or drop_null_text(elem)
                  or drop_useless_href(elem) or drop_noise_images(elem))
        return result

    def drop_noise_elements(self, root):
        self.__drop__(root, self.DropCondition)


def clean_profile(tree):
    """
    Select the text of html.
    """
    results = tree.cssselect('body :not(script)')
    text = ' '.join([elem.text for elem in results if isinstance(elem.text, (str, bytes))])
    return text
