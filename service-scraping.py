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
                      'https://translate.google.',
                      'https://podcasts.google.')
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
    links = list(dict.fromkeys(links_from_google + links_from_bing))



#def check_for_correct_links(links):
    associated_services = []
    potential_associated_services = []

    for link in links:
        if companyname in urlparse(link).netloc:
            if link not in associated_services:
                associated_services.append(link)
        else:
            if link not in associated_services and link not in potential_associated_services:
                potential_associated_services.append(link)

    #check for DNS entries 
    
    return (associated_services, potential_associated_services)



global companyname
companyname = input('Provide the companyname: ')
global main_domain
main_domain = input('Provide the company\'s classic domain: ')

global keyword
keyword = None
keyword_option = input('Do you want to use an additional keyword? [y/n]: ')
if keyword_option == 'y' or keyword_option == 'yes':
    keyword = input('Enter keyword: ')


    
""" Azure """
print(f'{Fore.CYAN}Checking for Azure services{Style.RESET_ALL}')
if keyword:
    output_azure = service_scraping("site:core.windows.net " + companyname + " " + keyword)
    associated_azure = output_azure[0]
    potentential_associated_azure = output_azure[1]
else:
    output_azure = service_scraping("site:core.windows.net " + companyname)
    associated_azure = output_azure[0]
    potentential_associated_azure = output_azure[1]

if associated_azure:
    print(f'{Fore.RED}We\'ve got them! Their associated services are as follows:{Style.RESET_ALL}')
    p.pprint(associated_azure)
if potentential_associated_azure:
    print(f'{Fore.YELLOW}Potentially associated services are as follows:{Style.RESET_ALL}')
    p.pprint(potentential_associated_azure)
if not associated_azure and not potentential_associated_azure:
    print('Nothing detected here.')


""" AWS """
print(f'{Fore.CYAN}Checking for AWS services{Style.RESET_ALL}')
if keyword:
    aws_one = service_scraping("site:http://s3.amazonaws.com/*/ " + companyname + " " + keyword)
    aws_two = service_scraping("site:http://*.s3.amazonaws.com/ " + companyname + " " + keyword)
    associated_aws = list(dict.fromkeys(aws_one[0] + aws_two[0]))
    potentential_associated_aws = list(dict.fromkeys(aws_one[1] + aws_two[1]))
else:
    aws_one = service_scraping("site:http://s3.amazonaws.com/*/ " + companyname)
    aws_two = service_scraping("site:http://*.s3.amazonaws.com " + companyname)
    associated_aws = list(dict.fromkeys(aws_one[0] + aws_two[0]))
    potentential_associated_aws = list(dict.fromkeys(aws_one[1] + aws_two[1]))

if associated_aws:
    print(f'{Fore.RED}We\'ve got them! Their associated services are as follows:{Style.RESET_ALL}')
    p.pprint(associated_aws)
if potentential_associated_aws:
    print(f'{Fore.YELLOW}Potentially associated services are as follows:{Style.RESET_ALL}')
    p.pprint(potentential_associated_aws)
if not associated_aws and not potentential_associated_aws:
    print('Nothing detected here.')


""" GCP """
print(f'{Fore.CYAN}Checking for Google Cloud Platform services{Style.RESET_ALL}')
if keyword:
    output_gcp = service_scraping("site:*.storage.googleapis.com " + companyname + " " + keyword)
    associated_gcp = output_gcp[0]
    potentential_associated_gcp = output_gcp[1]
else:
    output_gcp = service_scraping("site:*.storage.googleapis.com " + companyname)
    associated_gcp = output_gcp[0]
    potentential_associated_gcp = output_gcp[1]

if associated_gcp:
    print(f'{Fore.RED}We\'ve got them! Their associated services are as follows:{Style.RESET_ALL}')
    p.pprint(associated_gcp)
if potentential_associated_gcp:
    print(f'{Fore.YELLOW}Potentially associated services are as follows:{Style.RESET_ALL}')
    p.pprint(potentential_associated_gcp)
if not associated_gcp and not potentential_associated_gcp:
    print('Nothing detected here.')

"""
output = {**part_one, **part_two}
for key, value in output.items():
    if key in part_one and key in part_two:
        if (key, value) not in output.items():
            output[key] = [value, part_one[key]]
for key, value in part_two.items():

p.pprint(output)

output = list(dict.fromkeys(part_one + part_two))
p.pprint(output)
"""
