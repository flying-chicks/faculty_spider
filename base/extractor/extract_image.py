from face_recognition import load_image_file, face_locations
from io import BytesIO
import re
from string import punctuation, whitespace
from urllib.parse import urlparse


def get_faces_number(image_bytes):
    """
    detect the number of faces on a image based on a trained CNN classifier.
    :image_bytes: :image_bytes: hex image bytes.
    :returns: the number of faces in the image.
    """
    image_arr = load_image_file(BytesIO(image_bytes))
    return len(face_locations(image_arr))


def get_image_score(pattern, image_tag, image_bytes):
    """
    :param pattern: regular expression.
    :param image_tag: image tag element <img>
    :param image_bytes: hex image bytes.
    :return: score <int> of very image in a html.
    """
    url = image_tag.get('src')

    def by_anchor_text():
        parent_tag = image_tag.getparent()
        if isinstance(parent_tag.text, (str, bytes)) and pattern.search(parent_tag.text):
            return 3
        grandparent_tag = parent_tag.getparent()
        if isinstance(grandparent_tag.text, (str, bytes)) and pattern.search(grandparent_tag.text):
            return 2
        return 0

    def by_url():
        if pattern.search(url):
            return 4
        return 1

    def by_format():
        pattern_c = re.compile('jpg|jpeg', flags=re.IGNORECASE)
        if pattern_c.search(url):
            return 2
        return 1

    def by_faces():
        n_faces = get_faces_number(image_bytes)
        if n_faces is 0:
            return 0
        elif n_faces is 1:
            return 4
        else:
            return 1

    return by_anchor_text() + by_url() + by_format() + by_faces()


def get_best_image(last_accessed, keywords, image_tags, download, url_filter):
    """
    :param last_accessed: the url last accessed.
    :param keywords: 
    :param image_tags: a image tag element.
    :param download: a safe downloader.
    :param url_filter: a url filter.
    :return: better image url and image hex bytes.
    """
    max_score = 0
    best_image_url = None
    best_image_bytes = None
    pattern_a = re.compile('[{}]'.format(re.escape(punctuation + whitespace)))
    pattern_b = re.compile('|'.join([words for words in pattern_a.split(keywords) if words]), flags=re.I)

    for img_tag in image_tags:
        img_url = url_filter(last_accessed, img_tag, True)
        if not img_url:
            continue

        parsed = urlparse(img_url)
        if any([parsed.netloc.__contains__(i) for i in ["google", "facebook", "twitter", "instagram"]]):
            continue

        image_bytes = download(img_url)['html']
        if not image_bytes:
            continue

        relevance_score = get_image_score(pattern_b, img_tag, image_bytes)
        if max_score < relevance_score:
            max_score = relevance_score
            best_image_url = img_url
            best_image_bytes = image_bytes

    if get_faces_number(best_image_bytes) is 0:
        best_image_bytes = None

    return best_image_url, best_image_bytes


def safe_image_save(filename, image_url, image_bytes):
    """
    :param filename: image name without image format.
    :param image_url: image url.
    :param image_bytes: hex image bytes.
    """
    if not image_bytes or not image_url:
        return None

    filename = re.sub('[:\0/]', '', filename)

    format_regexp = re.compile('jpeg|jpg|png|gif|ico|icns|bmp', re.I)
    image_formats = format_regexp.findall(image_url)
    image_format = image_formats[0] if image_formats else 'jpeg'

    with open(filename + '.' + image_format, 'wb') as fw:
        fw.write(image_bytes)
