import requests as r
import dns.resolver

from OpenSSL import SSL
from cryptography import x509
from cryptography.x509.oid import NameOID
import idna
from socket import socket




class Detector(object):

	def __init__(self, domain):
		self.domain = domain
		self.azure = False
		self.aws = False
		self.IP = None
		self.Office365 = False
		self.Zoom = False
		self.Dropbox = False

		self.crypto_cert = None


	def getIP(self):
		for ip in dns.resolver.resolve(self.domain):
			self.IP = ip


	def getNameservers(self):
		for nameserver in dns.resolver.resolve(self.domain,'NS'):

			if "azure" in str(nameserver):
				self.azure = True

			if "aws" in str(nameserver):
				self.aws = True

	def checkFurtherDNSEntries(self):

		for txt in dns.resolver.resolve(self.domain,'TXT'):

			if "azure" in str(txt):
				self.azure = True
			if "aws" in str(txt):
				self.aws = True
			if "MS=ms" in str(txt):
				self.Office365 = True
			if "ZOOM_verify" in str(txt):
				self.Zoom = True
			if "dropbox" in str(txt):
				self.Dropbox = True

			#TODO: handle empty txt records

		for mx in dns.resolver.resolve(self.domain,'MX'):
			
			if "outlook" in str(mx):
				self.Office365 = True


	#inspired by https://gist.github.com/gdamjan/55a8b9eec6cf7b771f92021d93b87b2c

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
	        print(names[0].value)
	    except x509.ExtensionNotFound:
	        return None	    




myDetector = Detector("flaws.cloud")

myDetector.getIP()
myDetector.getNameservers()
myDetector.checkFurtherDNSEntries()
myDetector.checkFurtherDNSEntries()

myDetector.get_certificate()
myDetector.get_issuer()

#myDetector.checkCertificate()

