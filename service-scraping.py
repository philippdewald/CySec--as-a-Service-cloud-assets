import requests
import urllib
from urllib.parse import urlparse
from urllib.parse import urljoin
import pandas as pd 
from requests_html import HTML
from requests_html import HTMLSession

import pprint as p
import time
from bs4 import BeautifulSoup
from bs4.element import Comment

from colorama import Fore
from colorama import Style

import re


def get_source(url):
    """Return the source code for the provided URL. 

    Args: 
        url (string): URL of the page to scrape.

    Returns:
        response (object): HTTP response object from requests_html. 
    """

    try:
        session = HTMLSession() #HTMLSession()
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14'
        header = {'User-Agent': user_agent, 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
        response = session.get(url, headers=header)
        time.sleep(.600)
        return response

    except requests.exceptions.RequestException as e:
        print(e)

def service_scraping(query):

    query = urllib.parse.quote_plus(query)
    google_response = get_source("https://www.google.de/search?q=" + query)
    bing_response = get_source("https://www.bing.com/search?q=" + query)

    links_from_google = list(google_response.html.absolute_links)
    links_from_bing = list(bing_response.html.absolute_links)
    google_domains = ('https://www.google.', 
                      'https://google.', 
                      'https://webcache.googleusercontent.', 
                      'http://webcache.googleusercontent.', 
                      'https://policies.google.',
                      'https://support.google.',
                      'https://maps.google.',
                      'https://translate.google.')
    bing_domains = ('https://www.bing.',
                    'https://www.bingplaces.',
                    'https://bingplaces.',
                    'http://help.bing.',
                    'http://go.microsoft.',
                    'https://go.microsoft.',
                    'http://www.microsofttranslator.')

    for url in links_from_google[:]:
        if url.startswith(google_domains):
            links_from_google.remove(url)

    for url in links_from_bing[:]:
        if url.startswith(bing_domains):
            links_from_bing.remove(url)

    #p.pprint(links_from_google)
    #p.pprint(links_from_bing)
    check_for_correct_links(list(dict.fromkeys(links_from_google + links_from_bing)))




def check_for_correct_links(links):
    associated_services = []
    potential_associated_services = []

    for link in links:
        if companyname in urlparse(link).netloc:
            if link not in associated_services:
                associated_services.append(link)
        else:
            if link not in associated_services and link not in potential_associated_services:
                potential_associated_services.append(link)


    if associated_services:
        print(f'{Fore.RED}We\'ve got them! Their associated services are as follows:{Style.RESET_ALL}')
        p.pprint(associated_services)

    if potential_associated_services:
        print(f'{Fore.YELLOW}Potentially associated services are as follows:{Style.RESET_ALL}')
        p.pprint(potential_associated_services)

    if not associated_services and not potential_associated_services:
        print('Nothing detected here.')





global companyname
companyname = input('Provide the companyname: ')
global main_domain
main_domain = input('Provide the company\'s classic domain: ')

global keyword
keyword = None
keyword_option = input('Do you want to use an additional keyword? [y/n]: ')
if keyword_option == 'y' or keyword_option == 'yes':
    keyword = input('Enter keyword: ')


    

print(f'{Fore.CYAN}Checking for Azure services{Style.RESET_ALL}')
if keyword:
    service_scraping("site:core.windows.net " + companyname + " " + keyword)
else:
    service_scraping("site:core.windows.net " + companyname)

