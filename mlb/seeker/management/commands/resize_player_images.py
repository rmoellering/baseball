from django.core.management.base import BaseCommand
import os.path
from PIL import Image

from common.utils import get_logger

log = get_logger(__name__)


class Command(BaseCommand):
	def handle(self, *args, **options):

		image_path = "./static/players/original/"
		out_path = "./static/players/"
		player_url = "https://sports.yahoo.com/mlb/players/"

		cnt = 0
		for filename in os.listdir(image_path):
			if filename.endswith('png'):
				im = Image.open("{}{}".format(image_path, filename))
				if im.size != (3504, 2336):
					exit('{} {}'.format(filename, im.size))

				# (219, 146)
				#im = im.resize((438, 292))
				im = im.resize((219, 146))
				im.save('{}{}'.format(out_path, filename), "png")
				cnt += 1
				if cnt % 50 == 0:
					print(cnt)
