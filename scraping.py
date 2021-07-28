import requests
import urllib
import pandas as pd 
from requests_html import HTML
from requests_html import HTMLSession

import pprint as p
import time

def get_source(url):
    """Return the source code for the provided URL. 

    Args: 
        url (string): URL of the page to scrape.

    Returns:
        response (object): HTTP response object from requests_html. 
    """

    try:
        session = HTMLSession()
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
                      'https://maps.google.')
    bing_domains = ('https://www.bing.',
    				'https://www.bingplaces.',
    				'https://bingplaces.',
    				'http://help.bing.',
    				'http://go.microsoft.',
    				'https://go.microsoft.')

    for url in links_from_google[:]:
        if url.startswith(google_domains):
            links_from_google.remove(url)

    for url in links_from_bing[:]:
    	if url.startswith(bing_domains):
    		links_from_bing.remove(url)

    p.pprint(links_from_google)
    p.pprint(links_from_bing)


"""
In case of 429, try:
https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
Category: Retry on failure
"""


data = "beck bücher"


print('Amazon websites:')
scrape("site:s3.amazonaws.com " + data)
print('Azure websites:')
scrape("site:azurewebsites.net " + data)
