import requests
import urllib
import pandas as pd 
from requests_html import HTML
from requests_html import HTMLSession

import pprint as p
import time
from bs4 import BeautifulSoup

from colorama import Fore
from colorama import Style


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

def scrape(query):

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

    get_associated_websites(list(dict.fromkeys(links_from_google + links_from_bing)))


def get_associated_websites(links):
    associated_websites = []
    potential_associated_websites = []
    for link in links:
        if link.endswith('.pdf'):
            continue

        # handle websites that can't be reached
        try:
            html = requests.get(link).text
        except:
            continue

        soup = BeautifulSoup(html, 'html.parser')

        # look for links
        for item in soup.findAll('a'):
            href = item.get('href')
            if href is None or len(href) == 0:
                continue

            # see if there is a link to the main website
            if main_domain in href:
                if link not in associated_websites:
                    associated_websites.append(link)
                continue

            # see if the keyword is in linked urls
            if keyword in href:
                if link not in associated_websites and link not in potential_associated_websites:
                    potential_associated_websites.append(link)

        # look for website content
        #TODO
        # see if we get some information out of copyright text, terms of service, privacy policy text



    if associated_websites:
        print(f'{Fore.RED}We\'ve got them! Their associated websites are as follows:{Style.RESET_ALL}')
        p.pprint(associated_websites)

    if potential_associated_websites:
        print(f'{Fore.YELLOW}Potentially associated websites are as follows:{Style.RESET_ALL}')
        p.pprint(potential_associated_websites)

    if not associated_websites and not potential_associated_websites:
        print('Nothing detected here.') 


"""
In case of 429, try:
https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
Category: Retry on failure
"""

global keyword
keyword = input('Provide a companyname / keyword: ')
global main_domain
main_domain = input('Provide the company\'s classic domain: ')


print(f'{Fore.CYAN}Checking Amazon websites{Style.RESET_ALL}')
scrape("site:s3.amazonaws.com -filetype:pdf " + keyword)
print(f'{Fore.CYAN}Checking Azure websites{Style.RESET_ALL}')
scrape("site:azurewebsites.net -filetype:pdf " + keyword)
