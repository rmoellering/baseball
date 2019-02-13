import connexion
from flask import Flask, jsonify, render_template
from random import randint
import sqlite3

from utils import get_logger, get_human_time_diff

log = get_logger(__name__)
host = '127.0.0.1'
port = 5000
app_id = None

def get_conn():
	return sqlite3.connect('database.db')

def startup():

	# TODO: find a way to wrap this and similar methods in something that opens, provides, and closes the connection and cursor for it

	conn = get_conn()
	c = conn.cursor()

	# delete tables if they exist
	log.info('Deleting old tables...')
	tables = ['ids', 'apps', 'events', 'messages']
	for table in tables:
		try:
			c.execute("DROP TABLE {};".format(table))
		except sqlite3.OperationalError:
			print('{} cannot be dropped'.format(table))
			pass
	conn.commit()

	# TODO: indexes, constraints, FKs

	# create tables
	log.info('Creating tables...')
	# TODO: status instead of is_active, mebbe both tho
	c.execute("CREATE TABLE apps (id TEXT, app_name TEXT, is_active BOOLEAN, host TEXT, port INT, registered DATETIME, interval INT, pings INT, last_ping DATETIME)")
	# TODO: store pings in here?
	c.execute("CREATE TABLE events (sender TEXT, recipient TEXT, event TEXT, sent TIMESTAMP, response TEXT)")
	conn.commit()

	# register self
	log.info('Registering self...')
	app_id = get_unique_app_id()
	c.execute("INSERT INTO apps (id, app_name, is_active, host, port, registered, pings, last_ping) " + \
		"VALUES ('{}', 'monitor', TRUE, '{}', {}, datetime('now'), 1, datetime('now'));".format(app_id, host, port))
	c.execute("INSERT INTO events (sender, recipient, event, sent) VALUES ('{}', '{}', 'register', datetime('now'));".format(app_id, app_id))
	conn.commit()

	c.close()
	conn.close()
	log.info('Startup successful')

def register(body):

	# TODO: change id to 6-byte hex
	# TODO: better controls to make sure the app is unique

	log.info('Received registration request for app: {}'.format(body['appName']))

	conn = get_conn()
	c = conn.cursor()

	id = get_unique_app_id()
	c.execute(
		"INSERT INTO apps (id, app_name, is_active, host, port, " +\
			"registered, interval, pings, last_ping) " + \
		"VALUES ('{}', '{}', TRUE, '{}', {}, datetime('now'), {}, 1, datetime('now'));".format(id, body['appName'], body['host'], body['port'], body['interval'])
		)
	c.execute("INSERT INTO events (sender, recipient, event, sent) VALUES ('{}', '{}', 'register', datetime('now'));".format(id, app_id))
	conn.commit()

	c.close()
	conn.close()

	log.info('Registered app {} with id {}'.format(body['appName'], id))
	return jsonify({'appName': body['appName'], 'id': id})

def get_unique_app_id():

	conn = get_conn()
	c = conn.cursor()

	unique = False
	while not unique:
		id  = get_random_id()

		c.execute("SELECT id FROM apps where id = '{}';".format(id))
		if not c.fetchone():
			unique = True

	c.close()
	conn.close()

	return id

def get_random_id():
	'''
	6 chars A-Z,0-9, e.g. KXW09F
	'''

	id = ''
	for i in range(0,6):
		j = randint(0,35)
		if j < 10:
			id += str(j)
		else:
			id += chr(j + 55)
	return id

def ping(body):
	id = body['id']
	log.info('Received ping for app: {}'.format(id))

	conn = get_conn()
	c = conn.cursor()

	# register if app doesn't exist

	c.execute("SELECT id FROM apps WHERE id = '{}';".format(id))
	if c.fetchone():
		c.execute("UPDATE apps SET is_active = TRUE, last_ping = datetime('now'), pings = pings + 1 WHERE id = '{}';".format(body['id']))
		conn.commit()
	else:
		log.error('App {} not registered'.format(id))
		response = jsonify({'statusCode': 400, 'messsage': 'App not registered'})
		response.status_code = 400
		return response

	c.close()
	conn.close()

def shutdown(body):
	id = body['id']
	log.info('Received shutdown for app: {}'.format(id))

	# TODO: cache and warn if id doesn't exist

	conn = get_conn()
	c = conn.cursor()

	c.execute("UPDATE apps SET is_active = FALSE, last_ping = datetime('now'), pings = pings + 1 WHERE id = '{}';".format(id))
	c.execute("INSERT INTO events (sender, recipient, event, sent) VALUES ('{}', {}, 'shutdown', datetime('now'));".format(id, app_id))
	conn.commit()

	c.close()
	conn.close()

def summary():
	# TODO: could set 'late' here

	conn = get_conn()
	c = conn.cursor()

	c.execute("SELECT datetime('now');")
	now = c.fetchone()[0]

	c.execute("SELECT id, app_name, CASE WHEN is_active THEN 'active' ELSE 'shutdown' END AS status, host, port, " + \
		"registered, interval, pings, last_ping FROM apps ORDER BY registered;")
	apps = list(c.fetchall())		# list of tuples
	name_index = 1
	registered_index = 5
	interval_index = 6
	pings_index = 7
	last_ping_index = 8

	# calculate and append time alive for each tuple
	for i in range(0, len(apps)):
		apps[i] = list(apps[i])
		start = apps[i][registered_index]
		# monitor app doesn't ping
		#end = apps[i][last_ping_index] if apps[i][name_index] != 'monitor' else now
		apps[i].append(get_human_time_diff(start=start, end=now))
		apps[i][interval_index] = get_human_time_diff(seconds=apps[i][interval_index])
		if apps[i][name_index] == 'monitor':
			apps[i][pings_index] = '-'
			apps[i][last_ping_index] = '-'
		else:
			apps[i][last_ping_index] = get_human_time_diff(start=apps[i][last_ping_index], end=now)

	c.close()
	conn.close()

	return render_template('summary.html', apps=apps)

if __name__ == '__main__':
	startup()
	app = connexion.App(__name__, specification_dir='./openapi')
	app.add_api('swagger.yml')
	# NOTE: debug=True causes the restart
	app.run(host='127.0.0.1', port=5000, debug=False)
