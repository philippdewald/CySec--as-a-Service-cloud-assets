import pprint as p
import scraping
import requests
import re

from colorama import Fore
from colorama import Style
from urllib.parse import urlparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4.element import Comment



# from https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text
def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True



def get_associated_websites(links, companyname, main_domain, keyword):
    """ Detect whether a website is associated with a company.

    Args:
        links (list of strings): list of links to be checked. 
        companyname (string): the name of the company we are looking for.
        main_domain (string): the website of the company.
        keyword (string): optional a keyword to specify the search.

    Outprints:
        associated and potentially associated websites of the company.
        
    """
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


"""
In case of 429, try:
https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
Category: Retry on failure
"""

companyname = input('Provide the companyname: ')
main_domain = input('Provide the company\'s classic domain: ')
keyword = None
keyword_option = input('Do you want to use an additional keyword? [y/n]: ')
if keyword_option == 'y' or keyword_option == 'yes':
    keyword = input('Enter keyword: ')


print(f'{Fore.CYAN}Checking Amazon websites{Style.RESET_ALL}')
if keyword:
    get_associated_websites(scraping.scraping("site:s3.amazonaws.com -filetype:pdf " + companyname + " " + keyword), companyname, main_domain, keyword)
else:
    get_associated_websites(scraping.scraping("site:s3.amazonaws.com -filetype:pdf " + companyname), companyname, main_domain, keyword)

print(f'{Fore.CYAN}Checking Azure websites{Style.RESET_ALL}')
if keyword:
    get_associated_websites(scraping.scraping("site:azurewebsites.net -filetype:pdf " + companyname + " " + keyword), companyname, main_domain, keyword)
else:
    get_associated_websites(scraping.scraping("site:azurewebsites.net -filetype:pdf " + companyname), companyname, main_domain, keyword)
