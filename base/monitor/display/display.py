# encoding: utf-8
"""
display the information on web.
"""

from flask import Flask, render_template
from ..intrinsic_status import IntrinsicStatus
from ..crawl_status import CrawlStatus
from base.settings import SLAVES, USER_NAME, UPDATE_INTERVAL
from json import dumps

CRAWL_STATUS = CrawlStatus()
APP = Flask(__name__)


@APP.route('/')
def index():
    print('Please open "http://127.0.0.1:5000/" on web-browser.')
    print('Update the information every 5 seconds.')
    return render_template('index.html', update_interval=str(UPDATE_INTERVAL * 1000))


@APP.route('/status_per_mac')
def write_mac_info():
    results = []
    for (i, slave) in enumerate(SLAVES):
        get_slave_info = IntrinsicStatus(slave, USER_NAME)
        slave_info = get_slave_info()
        status_per_mac = CRAWL_STATUS.status_per_mac(slave)
        slave_info['alive'] = slave_info['alive'] and status_per_mac['alive']
        slave_info['complete'] = status_per_mac['complete']
        slave_info['accumulate'] = status_per_mac['accumulate']
        slave_info['id'] = i
        slave_info['slave'] = slave
        results.append(slave_info)
    return dumps(results)


@APP.route('/total_status')
def write_db_info():
    return dumps(CRAWL_STATUS.total_status())