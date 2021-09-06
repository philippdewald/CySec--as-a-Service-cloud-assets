from urllib.parse import urlparse
from colorama import Fore
from colorama import Style

import pprint as p
import scraping


def filter_for_correct_links(links):
    """ Given the companyname, filter for associated and potentially associated links.

    Args: 
        links (list of strings): links to check.

    Returns:
        tupel of associated links and potentially associated links. 

    """

    associated_services = []
    potentially_associated_services = []

    for link in links:
        if companyname in urlparse(link).netloc:
            if link not in associated_services:
                associated_services.append(link)
        else:
            if link not in associated_services and link not in potentially_associated_services:
                potentially_associated_services.append(link)

    # TODO: check more details
    # maybe very_likely_associated_services with companyname in full domain? (Ikea example)

    sorted(associated_services)
    sorted(potentially_associated_services)
    
    return (associated_services, potentially_associated_services)



def servScrape(cloudprovider, companyname, keyword):
    """ Scrape for the cloud services of the company.

    Args:
        cloudprovider (string): the cloudprovider to check for.
        companyname (string): the name of the company we are looking for.
        keyword (string): optional a keyword to specify the search.

    Outprints:
        the found results of the search.
        
    """
    print(f'{Fore.CYAN}Checking for {cloudprovider} services{Style.RESET_ALL}')
    request = []

    if cloudprovider == 'Azure':
        request.append('site:core.windows.net')
    elif cloudprovider == 'AWS':
        request.append('site:http://s3.amazonaws.com/*/')
        request.append('site:http://*.s3.amazonaws.com/')
    elif cloudprovider == 'Google Cloud Platform':
        request.append('site:*.storage.googleapis.com')
    else:
        print(f'Cloudprovider {cloudprovider} not supported')

    associated_list = []
    potentially_associated_list = []

    for r in request:
        if keyword:
            output = filter_for_correct_links(scraping.scraping(r + ' ' + companyname + ' ' + keyword))
            associated_list.extend(output[0])
            potentially_associated_list.extend(output[1])
        else:
            output = filter_for_correct_links(scraping.scraping(r + ' ' + companyname))
            associated_list.extend(output[0])
            potentially_associated_list.extend(output[1])

    sorted(list(dict.fromkeys(associated_list)))
    sorted(list(dict.fromkeys(potentially_associated_list)))

    if associated_list:
        print(f'{Fore.RED}We\'ve got them! Their associated services are as follows:{Style.RESET_ALL}')
        p.pprint(sorted(associated_list))
    if potentially_associated_list:
        print(f'{Fore.YELLOW}Potentially associated services are as follows:{Style.RESET_ALL}')
        p.pprint(sorted(potentially_associated_list))
    if not associated_list and not potentially_associated_list:
        print('Nothing detected here.')



companyname = input('Provide the companyname: ')
keyword = None
keyword_option = input('Do you want to use an additional keyword? [y/n]: ')
if keyword_option == 'y' or keyword_option == 'yes':
    keyword = input('Enter keyword: ')

servScrape('Azure', companyname, keyword)
servScrape('AWS', companyname, keyword)
servScrape('Google Cloud Platform', companyname, keyword)
