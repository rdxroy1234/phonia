#!/usr/bin/env python3

import os
import re
import json
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from lib.output import *
from lib.request import send
from config import *

from selenium import webdriver

browser = None

def closeBrowser():
    if browser is not None:
        browser.quit()

def search(req, stop):
    global browser

    if google_api_key and google_cx_id:
        return searchApi(req, stop)

    if browser is None:
        if os.environ.get('webdriverRemote'):
            browser = webdriver.Remote(os.environ.get('webdriverRemote'), webdriver.DesiredCapabilities.FIREFOX.copy())
        else:
            browser = webdriver.Firefox()

    try:
        REQ = urlencode({ 'q': req, 'num': stop, 'hl': 'en' })
        URL = 'https://www.google.com/search?tbs=li:1&{}&amp;gws_rd=ssl&amp;gl=us'.format(
            REQ)
        browser.get(URL)
        htmlBody = browser.find_element_by_css_selector("body").get_attribute('innerHTML')

        soup = BeautifulSoup(htmlBody, 'html5lib')

        while soup.find("div", id="recaptcha") is not None:
            warn('Google captcha detected.')
            token = ask('\033[1;77m'+'[>]'+'\033[0m'+' Complete the captcha and press ENTER: '+'\033[0m')
            htmlBody = browser.find_element_by_css_selector("body").get_attribute('innerHTML')
            soup = BeautifulSoup(htmlBody, 'html5lib')

        results = soup.find("div", id="search").find_all("div", class_="g")

        links = []

        for result in results:
            url = result.find("a").get('href')
            url = re.sub(r'(?:\/url\?q\=)', '', url)
            url = re.sub(r'(?:\/url\?url\=)', '', url)
            url = re.sub(r'(?:\&sa\=)(?:.*)', '', url)
            url = re.sub(r'(?:\&rct\=)(?:.*)', '', url)

            if re.match(r"^(?:\/search\?q\=)", url) is not None:
                url = 'https://google.com' + url

            if url is not None:
                links.append(url)

        return links
    except Exception as e:
        error('Request failed!')
        print(e)
        return []


def searchApi(req, stop):
    options = urlencode({ 'q': req, 'key': google_api_key, 'cx': google_cx_id, 'num': stop })
    r = send('GET', 'https://www.googleapis.com/customsearch/v1?%s' % (options))
    response = r.json()

    if 'error' in response:
        error('Error while fetching Google search API.')
        print(response['error'])
        askForExit()
        return []

    if 'items' not in response:
        return []

    results = response['items']

    links = []

    for result in results:
        if result['link'] is not None:
            links.append(result['link'])

    return links
