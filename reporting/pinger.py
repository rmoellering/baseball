import json
import requests
from requests.exceptions import ConnectionError
import threading
from utils import get_logger

class Pinger(object):
	import requests

	def __init__(self, app_name, app_host, app_port, monitor_host, monitor_port, interval=60):
		super(Pinger, self).__init__()

		self.APP_NAME = app_name
		self.APP_HOST = app_host
		self.APP_PORT = int(app_port)
		self.MONITOR_HOST = monitor_host
		self.MONITOR_PORT = int(monitor_port)
		self.INTERVAL = interval

		self.APP_ID = None
		self.HEADERS = {'content-type':'application/json'}

		self.log = get_logger(__name__)
		self.register()


	def get_url(self, path):
		return "http://{}:{}/{}".format(self.MONITOR_HOST, self.MONITOR_PORT, path)

	def register(self):

		# don't double-register
		if self.APP_ID:
			self.log.warn('App already registered with id [{}]'.format(self.APP_ID))
			return

		data = {
			'appName': self.APP_NAME, 
			'host': self.APP_HOST, 
			'port': self.APP_PORT,
			'interval': self.INTERVAL
		}

		url = self.get_url('register')
		try:
			r = requests.post(url=url, data=json.dumps(data), headers=self.HEADERS)
		except ConnectionError:
			self.log.error('Register failed.  Monitor not running on {}'.format(url))
			return

		if r.status_code == 200:
			self.log.info("Registration response: {}".format(r.json()))
			self.APP_ID = r.json()['id']
			self.log.info("Registered self [{}] with id [{}]".format(self.APP_NAME, self.APP_ID))
			return self.APP_ID
		else:
			self.log.error("Registration error: {} {}".format(r.status_code, r.reason))

	def ping(self):

		# if not yet registered, try to register
		if not self.APP_ID:
			self.log.error('Ping attempt with unregistered app.  Registering...')
			self.register()
			return

		data = {
			'id': self.APP_ID, 
		}

		url = self.get_url('ping')
		try:
			r = requests.post(url=url, data=json.dumps(data), headers=self.HEADERS)
		except ConnectionError:
			self.log.error('Ping failed.  Monitor not running on {}'.format(url))
			return

		if r.status_code == 200:
			pass
		elif r.status_code == 400:
			self.log.error('Monitor reported this app is unregistered.  Registering...')
			self.APP_ID = None
			self.register()
			self.log.info('New APP_ID {}'.format(self.APP_ID))
		else:			
			self.log.error("Ping error: {} {}".format(r.status_code, r.reason))

	def shutdown(self):

		# ignore if not yet registered
		if not self.APP_ID:
			self.log.error('Shutdown attempt with unregistered app.')
			return

		data = {
			'id': self.APP_ID, 
		}

		url = self.get_url('shutdown')
		try:
			r = requests.post(url=url, data=json.dumps(data), headers=self.HEADERS)
		except ConnectionError:
			self.log.error('Shutdown failed.  Monitor not running on {}'.format(url))
