import connexion
from utils import get_logger
from monitor import startup

log = get_logger(__name__)
startup()
app = connexion.App(__name__, specification_dir='./openapi')
# Read the swagger.yml file to configure the endpoints
app.add_api('swagger.yml')

if __name__ == '__main__':
	# NOTE: debug=True causes the restart
	app.run(host='127.0.0.1', port=5000, debug=False)
