import requests
import urllib
import time
from urllib.parse import urlparse
from requests_html import HTMLSession


def get_source(url):
    """ Return the source code for the provided URL.
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



def scraping(query):
	""" Return the search results from Google and Bing for the provided query.
		Filter out the websites from the search engines.

	Args:
		query (string): the query to search for results.

	Returns:
		links (list): a list of the search results.

	"""

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
                    'https://help.bing.',
                    'http://go.microsoft.',
                    'https://go.microsoft.',
                    'http://www.microsofttranslator.')

	for url in links_from_google[:]:
		if url.startswith(google_domains):
			links_from_google.remove(url)

	for url in links_from_bing[:]:
		if url.startswith(bing_domains):
			links_from_bing.remove(url)

	links = sorted(list(dict.fromkeys(links_from_google + links_from_bing)))
	return links
