import connexion
from flask import Flask, jsonify
import psycopg2
import requests
import sys
from time import sleep

from pinger import Pinger
from utils import get_logger, RepeatedTimer

log = get_logger(__name__)

def get_conn():
	return psycopg2.connect(
		host='localhost',
		dbname='mlb',
		user='robmo',
		password=''
	)

def search(body):
	conn = get_conn()
	cur = conn.cursor()
    
	name = body['name'].lower()

	sql = "SELECT yahoo_id, name FROM data_player WHERE LOWER(name) LIKE '%{}%';".format(name)
	print(sql)
	cur.execute(sql)

	resp = []
	for tpl in cur.fetchall():
		dct = {
			"id": tpl[0],
			"name": tpl[1]
		}
		resp.append(dct)

	cur.close()
	conn.close()
	return jsonify(cur.fetchall())


if __name__ == '__main__':

	monitor_port = 5000

	app_port = 5001
	if len(sys.argv) == 2:
		app_port = sys.argv[1]
	interval = 15
	log.info('PORT {} ARGS {}'.format(app_port, len(sys.argv)))
	log.info(sys.argv)

	pinger = Pinger(
		app_name='reporting',
		app_host='127.0.0.1', 
		app_port=app_port,
		monitor_host='127.0.0.1', 
		monitor_port=monitor_port,
		interval=interval
	)
	rt = RepeatedTimer(interval=interval, function=pinger.ping)

	try:
		# app = Flask(__name__)
		# app.run(host='127.0.0.1', port=5001)
		app = connexion.App(__name__, specification_dir='./openapi')
		app.add_api('swagger.yml')
		# NOTE: debug=True causes the restart
		app.run(host='127.0.0.1', port=app_port, debug=False)
	finally:
		pinger.shutdown()
		rt.stop()
