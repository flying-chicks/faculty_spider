# -*- encoding: utf-8 -*-
"""
by Ken Yu
@ Tue Jul 18 18:43:49 2017
"""
import re
from socket import gethostname
from datetime import datetime
from numpy import inf
import logging
import sys


# log that records info.
def init_log(log_path):
    """
    Wrap the logging.
    :param log_path: <string> log path
    :return: log
    """
    now = datetime.now()
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename=log_path + '{0}_{1}.log'.format(gethostname(),
                                                                 datetime.strftime(now, '%Y-%m-%d_%H.%M.%S')),
                        filemode='w')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    spider_log = logging.getLogger('spider log')
    spider_log.addHandler(console)
    return spider_log


PREFIX = sys.prefix

LOGGING = init_log(PREFIX + '/../logs/')

# module: ajax_render
# the min threshold that determinate whether the profile web-page is AJAX HTML.
PROFILE_AJAX_MIN_VALUE = 1.

# the max threshold that determinate whether the menu web-page is AJAX HTML.
MENU_AJAX_MAX_VALUE = 10.

# the chrome driver path
CHROME_DRIVER = PREFIX + '/selenium/webdriver/chrome/chromedriver_x86'

# the ajax key words
AJAX_PATTERN = re.compile('ajax.googleapis.com|google analytics', flags=re.I)

# page load timeout
PAGE_LOAD_TIMEOUT = 200

# module: main
# the images path
# IMAGES_PATH = '/home/images/'
IMAGES_PATH = PREFIX + '/../images/'

# key words in URL that should be avoided
AVOID_ANCHOR = re.compile("contact us|accessibility|feedback|visit|maps|athletics|giving|path|library|"
                          "academic calendar|student|facebook|twitter|instagram|snapchat|linkedin|social media|"
                          "news|award|honor|events|alumni|work at|copyright|(?:people|faculty) search|blackboard|"
                          "node|studying at|communit(?:y|ies)|admission (?:&|and) aid|financial aid|campus life|"
                          "video|learning at|(?:statistics|history) & facts|find|faculty resources|magazine|"
                          "faculty(?:access|affairs)|academic advising & support|about the spotlight|study abroad|"
                          "continuing studies|graduate school|undergraduate studies|provost|at a glance|"
                          "extended campus|faculty login|academic advising|academic eligibility|academic integrity|"
                          "academic policies|academic success center|exploratory studies|faculty (?:awards|honors)",
                          flags=re.I)

# key words in URL that are secondary level
SECONDARY_ANCHOR = re.compile("people|profile|faculty|fellow|lecturer|instructor|adjunct|emeriti",
                              flags=re.I)

# key words in URL that are tertiary level
TERTIARY_ANCHOR = re.compile(
                            # Organization
                            'about|academ(?:y|ic)|university|college|campus|school|department|section|'
                            'research|center|lab|science|certificate|stud(?:y|ies)|institut(?:ion|e)|'
                            'project|committee|program|fund|initiative|group|planning|seminar|system|'
                            'studio|development|club|forum|alliance|opportunit(?:y|ies)|engineering|'
                            'learning|teaching|ares|analysis|specialist|offering|organization|major|'
                            'disciplines|learn more|'
                        
                            # Generic subject
                            "[a-z]+?olog(?:y|ical)|[a-z]+?ics?|[a-z]+?ph(?:y|ical)|"
                        
                            # Medical Science
                            "psychiatry|disease|surgery|cancer|nutrition|medicine|"
                            "health|therapy|nurs(:?e|ing)|disabilit(?:y|ies)|"
                        
                            # Sociology
                            "law|media|entrepreneurship|bussiness|collection|religion|"
                            "collaborative|education|environment|population|management|"
                            "art|civilization|humanit(?:y|ies)|transportation|journalism|"
                            "government|literature|classic|language|history|music|architure|"
                            "social|affairs|writing|english|french|greek|italian|portuguese|"
                            "russian|spanish|conservatory|dance|drama|culture|market|german|"
                            "rhetoric|scandinavian|finance|investment|insurance|latin|chinese|"
                            "japanese|documentary|public administration|curriculum|"
                        
                            # agricultural
                            "agricultural|agronomy|forestry|food|"
                        
                            # Polytechnic
                            "comput(?:er|ation)|chemi(?:stry|cal)|electron|material|energy|"
                            "architecture|intelligence|tunnel|observatory|design|bub|"
                            "sanitation|tank|mems|astronomy|information|natural resources|"
                            "optometry|film",

                            flags=re.I)

# module: main
DOMAIN_STRIP = False

# mongodb host
# MONGO_HOST = '10.220.138.248'
MONGO_HOST = '10.220.138.99'

# module: mongo_control
# default max access
MAX_ACCESS = inf

# module: html_crawler
ROBOT_FILE_CENSOR = False

# max processes
MAX_PROCESSES = 2

# max threads
MAX_THREADS = 10

# seed url
SEED_URL = 'http://www.tcu.edu/'

# college, university or school name.
ORGANIZATION_NAME = 'texas_christian_university'


# a set including the ip of slaves.
SLAVES = {
    '10.220.138.109',
    '10.220.138.110'
}

# user's name used by SSH.
USER_NAME = 'worker'

# user's password used by SSH.
PKEY_PATH = '/home/worker/.ssh/id_rsa'

# update interval: n seconds
UPDATE_INTERVAL = 5

PACKAGE_HOME = PREFIX + '/../'