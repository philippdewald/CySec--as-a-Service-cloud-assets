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

       Send header and sleep in order to prevent from a 429 status code.

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
    company_information_fields = ['privacy', 'policy', 'contact', 'copyright', 'imprint',  
                                  'terms', 'conditions', 'support']

    for link in links:
        if link.endswith('.pdf'):
            continue

        domain = urlparse(link).netloc

        # handle websites that can't be reached
        try:
            html = requests.get(link).text
        except:
            continue

        soup = BeautifulSoup(html, 'html.parser')

        #print(f'{Fore.RED}Current Link is: {link}{Style.RESET_ALL}')

        found_hrefs = []
        for item in soup.findAll('a'):  # every iteration is a href of link
            href = item.get('href')

            if href is None or len(href) == 0:
                continue

            # only look into new href's
            if href not in found_hrefs:
                found_hrefs.append(href)

                # 1. see if there is a link to the main website
                if main_domain in href:
                    if link not in associated_websites:
                        associated_websites.append(link)
                    continue

                # 2. see if the companyname is in linked urls
                if companyname in href:
                    if link not in associated_websites and link not in potential_associated_websites:
                        potential_associated_websites.append(link)
                
                # 3. see if we get some information out of copyright text, terms of service, privacy policy text, ...
                if any(key in href for key in company_information_fields):
                    # visit href and see if companyname is included
                    # if yes, add it to associated_websites, it not, delete it when it appears in 
                    # associated_websites or potential_associated_websites and continue with next link

                    # make abolute links
                    if not href.startswith('http'):
                        url = requests.get('http://' + domain).url
                        href = urljoin(url, href)
                        if domain not in href:
                            continue

                    try:
                        text = requests.get(href).text
                    except:
                        continue

                    company_information_soup = BeautifulSoup(text, 'html.parser')
                    texts = company_information_soup.findAll(text=True)
                    visible_texts = filter(tag_visible, texts)

                    companyname_regex = re.compile(companyname, re.MULTILINE | re.IGNORECASE)
                    if re.search(companyname_regex, u" ".join(t.strip() for t in visible_texts)):
                        #print('Get the champagne out ' + href, link)                                   # for debugging
                        if link not in associated_websites:
                            associated_websites.append(link)
                        break
                    else:
                        #print('We dont want wrong sites: ' + href, link)                               # for debugging
                        if link in potential_associated_websites:
                            potential_associated_websites.remove(link)
                        if link in associated_websites:
                            associated_websites.remove(link)
                            potential_associated_websites.append(link)      # necessary? probably not, but maybe there was a mistake so save it here
                        break 
        # look for website content
        #TODO

    if associated_websites:
        print(f'{Fore.RED}We\'ve got them! Their associated websites are as follows:{Style.RESET_ALL}')
        p.pprint(associated_websites)

    if potential_associated_websites:
        print(f'{Fore.YELLOW}Potentially associated websites are as follows:{Style.RESET_ALL}')
        p.pprint(potential_associated_websites)

    if not associated_websites and not potential_associated_websites:
        print('Nothing detected here.')


# from https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text
def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

"""
In case of 429, try:
https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
Category: Retry on failure
"""

global companyname
companyname = input('Provide the companyname: ')
global main_domain
main_domain = input('Provide the company\'s classic domain: ')

global keyword
keyword = None
keyword_option = input('Do you want to use an additional keyword? [y/n]: ')
if keyword_option == 'y' or keyword_option == 'yes':
    keyword = input('Enter keyword: ')


print(f'{Fore.CYAN}Checking Amazon websites{Style.RESET_ALL}')
if keyword:
    scrape("site:s3.amazonaws.com -filetype:pdf " + companyname + " " + keyword)
else:
    scrape("site:s3.amazonaws.com -filetype:pdf " + companyname)

print(f'{Fore.CYAN}Checking Azure websites{Style.RESET_ALL}')
if keyword:
    scrape("site:azurewebsites.net -filetype:pdf " + companyname + " " + keyword)
else:
    scrape("site:azurewebsites.net -filetype:pdf " + companyname)
