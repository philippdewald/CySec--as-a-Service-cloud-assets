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

		self.Azure = False
		self.AWS = False
		self.IP = []
		self.Office365 = False
		self.Zoom = False
		self.Dropbox = False

		self.crypto_cert = None
		self.cert_issuer = None

		self.found_urls = []


	def checkForCloudService(self, data):
		for item in data:
			if "azure" in str(item) or "core.windows.net" in str(item) or "azurewebsites.net" in str(item):
				self.Azure = True
			if "aws" in str(item) or "s3-website" in str(item):
				self.AWS = True
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
		for link in soup.findAll('a'):
			found_url = link.get('href')
			#print(found_url)

			if found_url is None or len(found_url) == 0:
				continue

			if not found_url.startswith('http'):
				found_url = urljoin(url, found_url)

			if found_url not in self.found_urls:
				self.found_urls.append(found_url)
		self.checkForCloudService(self.found_urls)

	def checkAutonmousSystem(self):
		# done via querying https://hackertarget.com since there is no handy python library
		# 50 free queries per day
		response = r.get(f'https://api.hackertarget.com/aslookup/?q={self.IP}')
		response_text = response.text.split('"')
		ASN = response_text[3]
		ASName = response_text[7]

		AzureASN = ['8068', '8069', '8070', '8071', '8072', '8073', '8074', '8075']
		AWSASN = ['7224', '14618', '16509', '17493', '10124', '9059']

		if ASN in AzureASN:
			self.Azure = True
		if ASN in AWSASN:
			self.AWS = True

		# alternatively we could check for keywords like Microsoft or Amazon in ASName, 
		# but the program would state that e.g. amazon.com runs on the cloud. Is this really the case?

	

	#def detectInHTML(self): maybe cloudbrute as inspiration


	def run(self):
		self.getIP()
		self.getNameservers()
		self.checkFurtherDNSEntries()
		#check certificate only if one exists:
		if 'https' in r.get('http://' + self.domain).url:
			self.get_certificate()
			self.get_issuer()
		self.detectURLs()
		self.checkAutonmousSystem()


if __name__ == "__main__":
	Detector("ais-security.de").run()
