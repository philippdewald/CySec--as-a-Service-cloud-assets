import requests as r
import dns.resolver
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import re

from OpenSSL import SSL
from cryptography import x509
from cryptography.x509.oid import NameOID
import idna
from socket import socket

from colorama import Fore
from colorama import Style

logging.basicConfig(format='', level=logging.INFO)

class Detector:

	def __init__(self, domain):
		self.domain = domain

		self.Azure = False
		self.AWS = False
		self.IP = []
		self.Office365 = False
		self.Zoom = False
		self.Dropbox = False

		self.crypto_cert = None
		self.cert_issuer = None

		self.found_urls = []

		self.AzureASN = ['8068', '8069', '8070', '8071', '8072', '8073', '8074', '8075']
		self.AWSASN = ['7224', '14618', '16509', '17493', '10124', '9059']

		self.Azure_use_case = []
		self.AWS_use_case = []
		self.Azure_links = []
		self.AWS_links = []


	def checkForCloudService(self, data, use_case):

		AzureKeywords = ['azure', 'Azure', 'core.windows.net', 'azurewebsites.net', '1drv.com', 'onedrive.live']
		AWSKeywords = ['awsdns', 's3-website', 'EC2', 'ECS', 'amazonaws'] # don't set 'S3' as casefold!

		for item in data:
			# don't go for 'Microsoft'!
			if any(azurekeyword.casefold() in str(item).casefold() for azurekeyword in AzureKeywords):
				self.Azure = True
				if 'http' in str(item):
					self.Azure_links.append(str(item))
				self.Azure_use_case.append(use_case)

			# don't go for 'Amazon'!
			if any(awskeyword.casefold() in str(item).casefold() for awskeyword in AWSKeywords) or 'S3' in str(item):	
				self.AWS = True
				if 'http' in str(item):
					self.AWS_links.append(str(item))
				self.AWS_use_case.append(use_case)
			if "MS=ms".casefold() in str(item).casefold() or "outlook" in str(item):
				self.Office365 = True
			if "ZOOM_verify".casefold() in str(item).casefold():
				self.Zoom = True
			if "dropbox".casefold() in str(item).casefold():
				self.Dropbox = True


	def getIP(self):
		for ip in dns.resolver.resolve(self.domain):
			self.IP = ip

	def getNameservers(self):
		nameservers = []
		try:
			for nameserver in dns.resolver.resolve(self.domain,'NS'):
				nameservers.append(nameserver)
			print(nameservers)
			self.checkForCloudService(nameservers, 'nameserver')
		except:
			pass

	def checkFurtherDNSEntries(self):
		txt_records = []
		try:
			for txt in dns.resolver.resolve(self.domain,'TXT'):
				txt_records.append(txt)
			self.checkForCloudService(txt_records, 'TXT records')
		except:
			pass	

		try:
			mx_records = []
			for mx in dns.resolver.resolve(self.domain,'MX'):
				mx_records.append(mx)
			self.checkForCloudService(mx_records, 'MX records')
		except:
			pass


	#inspired by https://gist.github.com/gdamjan/55a8b9eec6cf7b771f92021d93b87b2c --------------
	# sometimes it doesn't do what it should... TODO fix this

	def get_certificate(self):
		try:
		    hostname_idna = idna.encode(self.domain)
		    sock = socket()

		    sock.settimeout(10)
		    sock.connect((self.domain, 443))
		    sock.settimeout(None)
		    ctx = SSL.Context(SSL.SSLv23_METHOD) # most compatible
		    ctx.check_hostname = False
		    ctx.verify_mode = SSL.VERIFY_NONE

		    sock_ssl = SSL.Connection(ctx, sock)
		    sock_ssl.set_connect_state()
		    sock_ssl.set_tlsext_host_name(hostname_idna)
		    sock_ssl.do_handshake()
		    cert = sock_ssl.get_peer_certificate()
		    self.crypto_cert = cert.to_cryptography()
		    sock_ssl.close()
		    sock.close()

		    self.get_issuer()

		except:
			pass

	def get_issuer(self):
	    try:
	        names = self.crypto_cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
	        self.cert_issuer = names[0].value
	        if "Amazon" in self.cert_issuer: 
	        	self.AWS = True
	        	self.AWS_use_case.append('website certificate')
	        if "Microsoft" in self.cert_issuer: 
	        	self.Azure = True
	        	self.Azure_use_case.append('website certificate')
	    except x509.ExtensionNotFound:
	        return #None	    

	# ------------------------------------------------------------------------------------------

	def detectURLs(self):
		#check if website is http or https and set url accordingly:
		url = r.get('http://' + self.domain).url	
		html = r.get(url).text
		soup = BeautifulSoup(html, 'html.parser')
		for link in soup.findAll('a'):
			found_url = link.get('href')

			if found_url is None or len(found_url) == 0:
				continue

			if not found_url.startswith('http'):
				found_url = urljoin(url, found_url)

			if found_url not in self.found_urls:
				self.found_urls.append(found_url)

		AzureWebsites = ['core.windows.net', 'azurewebsites.net', 'azurestaticapps', 'onedrive.live.com', '1drv.com']
		AWSWebsites = ['s3-website', 'amazonaws']

		for item in self.found_urls:
			if any(azurewebsite in str(item) for azurewebsite in AzureWebsites):
				self.Azure = True
				self.Azure_links.append(str(item))
				self.Azure_use_case.append('linked website from cloud provider')

			if any(awswebsite in str(item) for awswebsite in AWSWebsites):
				self.AWS = True
				self.AWS_links.append(str(item))
				self.AWS_use_case.append('linked website from cloud provider')

		#self.checkForCloudService(self.found_urls, 'linked website from cloud provider')

	def detectInSourceCode(self):
		pass

	def checkAutonmousSystem(self):
		# done via querying https://hackertarget.com since there is no handy python library
		# 50 free queries per day
		try:
			response = r.get(f'https://api.hackertarget.com/aslookup/?q={self.IP}')
			response_text = response.text.split('"')
			ASN = response_text[3]
			ASName = response_text[7]

			if ASN in self.AzureASN:
				self.Azure = True
				self.Azure_use_case.append('Autonomous System')
			if ASN in self.AWSASN:
				self.AWS = True
				self.AWS_use_case.append('Autonomous System')
		except IndexError:
			print('Autonomous System Detection API has reached its todays limit')

	def flAWS_cloud(self):
		# implementation of some useful tools from http://flaws.cloud/
		# no detection, but gaining insights
		if self.AWS:
			try:
				nslookup = os.popen('nslookup ' + str(self.IP) + ' 8.8.8.8').read()

				region = nslookup.split('s3-website-',1)[1].split('.amazonaws.com',1)[0]
				bucket_list = os.popen('aws s3 ls s3://' + self.domain + '/ --no-sign-request --region ' + region).read()
			except:
				pass

	def checkServer(self):
		try:
			url = r.get('http://' + self.domain).url
			server = r.get(url).headers['Server']
			self.checkForCloudService([server], 'name of the server')
		except:
			return



	def run(self):
		logging.info(f'{Fore.YELLOW}Checking: {self.domain}{Style.RESET_ALL}')
		self.getIP()
		self.checkForCloudService([self.domain], 'domain name')
		self.getNameservers()
		self.checkFurtherDNSEntries()
		# check certificate only if one exists:
		if 'https' in r.get('http://' + self.domain).url:
			self.get_certificate()
		self.detectURLs()
		self.checkAutonmousSystem()
		self.flAWS_cloud()
		self.checkServer()

		self.Azure_use_case = list(dict.fromkeys(self.Azure_use_case))
		self.AWS_use_case = list(dict.fromkeys(self.AWS_use_case))

		no_output = True

		if self.Azure: logging.info(f'{Fore.RED}Detected:{Style.RESET_ALL} Microsoft Azure: identified via {", ".join(self.Azure_use_case)}'); no_output = False
		if self.Azure_links: logging.info(f'{Fore.CYAN}Azure links:{Style.RESET_ALL} {", ".join(self.Azure_links)}'); no_output = False

		if self.AWS: logging.info(f'{Fore.RED}Detected:{Style.RESET_ALL} Amazon Web Services: identified via {", ".join(self.AWS_use_case)}'); no_output = False
		if self.AWS_links: logging.info(f'{Fore.CYAN}AWS links:{Style.RESET_ALL} {", ".join(self.AWS_links)}'); no_output = False
		
		if self.Office365: logging.info(f'{Fore.RED}Detected:{Style.RESET_ALL} Office365'); no_output = False
		if self.Zoom: logging.info(f'{Fore.RED}Detected:{Style.RESET_ALL} Zoom'); no_output = False
		if self.Dropbox: logging.info(f'{Fore.RED}Detected:{Style.RESET_ALL} Dropbox'); no_output = False

		if no_output: logging.info(f'{Fore.YELLOW}Nothing detected{Style.RESET_ALL}')

if __name__ == "__main__":
	domain = input('Provide a domain to check: ')
	if 'http' in domain:
		logging.info(f'{Fore.RED}Please don\'t give http / https{Style.RESET_ALL}')
		domain = input('Provide a domain to check: ')
	Detector(domain).run()
