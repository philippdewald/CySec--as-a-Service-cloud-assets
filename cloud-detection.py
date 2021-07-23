import requests as r
import dns.resolver
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin


from OpenSSL import SSL
from cryptography import x509
from cryptography.x509.oid import NameOID
import idna
from socket import socket

logging.basicConfig(format='', level=logging.INFO)

class Detector:

	def __init__(self, domain):
		self.domain = domain

		self.azure = False
		self.aws = False
		self.IP = []
		self.Office365 = False
		self.Zoom = False
		self.Dropbox = False

		self.crypto_cert = None
		self.cert_issuer = None

		self.found_urls = []


	def checkForCloudService(self, data):
		for item in data:
			if "azure" in str(item):
				self.azure = True
			if "aws" in str(item):
				self.aws = True
			if "MS=ms" in str(item) or "outlook" in str(item):
				self.Office365 = True
			if "ZOOM_verify" in str(item):
				self.Zoom = True
			if "dropbox" in str(item):
				self.Dropbox = True

	def getIP(self):
		for ip in dns.resolver.resolve(self.domain):
			self.IP = ip

	def getNameservers(self):
		nameservers = []
		for nameserver in dns.resolver.resolve(self.domain,'NS'):
			nameservers.append(nameserver)
		self.checkForCloudService(nameservers)

	def checkFurtherDNSEntries(self):
		txt_records = []
		try:
			for txt in dns.resolver.resolve(self.domain,'TXT'):
				txt_records.append(txt)
			self.checkForCloudService(txt_records)
		except:
			pass	

		try:
			mx_records = []
			for mx in dns.resolver.resolve(self.domain,'MX'):
				mx_records.append(mx)
			self.checkForCloudService(mx_records)
		except:
			pass


	#inspired by https://gist.github.com/gdamjan/55a8b9eec6cf7b771f92021d93b87b2c --------------
	# sometimes it doesn't do what it should... TODO fix this

	def get_certificate(self):
	    hostname_idna = idna.encode(self.domain)
	    sock = socket()

	    sock.connect((self.domain, 443))
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

	def get_issuer(self):
	    try:
	        names = self.crypto_cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
	        self.cert_issuer = names[0].value
	    except x509.ExtensionNotFound:
	        return #None	    

	# ------------------------------------------------------------------------------------------

	def detectURLs(self):
		#check if website is http or https and set url accordingly:
		url = r.get('http://' + self.domain).url	
		#logging.info(f'Found: {url}')
		html = r.get(url).text
		soup = BeautifulSoup(html, 'html.parser')
		for link in soup.find_all('a'):
			found_url = link.get('href')
			if not found_url.startswith('http'):
				found_url = urljoin(url, found_url)

			if found_url not in self.found_urls:
				self.found_urls.append(found_url)
		self.checkForCloudService(self.found_urls)


	#def detectInHTML(self): maybe cloudbrute as inspiration
	#def checkAutonmousSystem(self)
	#def checkResponseHeader(self)


	def run(self):
		self.getIP()
		self.getNameservers()
		self.checkFurtherDNSEntries()
		#check certificate only if one exists:
		if 'https' in r.get('http://' + self.domain).url:
			self.get_certificate()
			self.get_issuer()
		self.detectURLs()


if __name__ == "__main__":
	Detector("ais-security.de").run()
