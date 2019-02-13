from bs4 import BeautifulSoup
from datetime import date
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
import os.path
import re
import requests
from time import sleep
import urllib.request

from common.utils import get_logger, Results
from data.models import Player

log = get_logger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):

        image_path = "./static/players/original/"
        player_url = "https://sports.yahoo.com/mlb/players/"

        #test = '<div class="IbBox Bgr(nr) Pos(r) Miw(228px) W(228px) H(228px) Bgp(50%,25px) Bgz(135%) Bdrs(50%) Mend(40px)" data-reactid="4" style="background-image:url(https://s.yimg.com/it/api/res/1.2/1LHCbQwKiPAtSJ8GmVWI4Q--~A/YXBwaWQ9eW5ld3M7dz0zMDA7aD0yMDA7cXVhbGl0eT0xMDA-/https://s.yimg.com/xe/i/us/sp/v/mlb_cutout/players_l/03142018/9333.png);background-color:#041e44;"><div class="D(ib) Pos(a) B(-5px) End(-5px) W(45px) H(45px)" data-reactid="5">'
        #url = "https://s.yimg.com/xe/i/us/sp/v/mlb_cutout/players_l/03142018/9333.png"

        # m = re.match('.*/(https.+/)(\d+\.png)', test)
        # if m:
        #     url = m.group(1)
        #     filename = m.group(2)
        #     url += filename
        # else:
        #     log.debug('no find')
        #     exit()
        #
        # log.info('Retriving {}...'.format(filename))
        # urllib.request.urlretrieve(url, "{}{}".format(image_path, filename))

        res = Results()

        for player in Player.objects.all():

            filename = "{}_{}_{}.png".format(player.yahoo_id, player.first_name.lower(), player.last_name.lower())
            full_path = image_path + filename
            full_path = full_path.replace(' ', '_')     # get rid of spaces

            if os.path.isfile(full_path):
                #log.debug('{} found'.format(full_path))
                res.increment('file found')
                continue

            log.info("Retrieving {}'s page...".format(player.name))
            tries = 0
            found = False
            while tries < 5:
                page = requests.get("{}{}".format(player_url, player.yahoo_id))
                if page.status_code != 200:
                    exit('({}) - {}'.format(page.status_code, url))
                soup = BeautifulSoup(page.content, 'html.parser')

                try:
                    blob = soup.find('div', class_="IbBox Bgr(nr) Pos(r) Miw(228px) W(228px) H(228px) Bgp(50%,25px) Bgz(135%) Bdrs(50%) Mend(40px)")
                    found = True
                    break
                except AttributeError:
                    pass

                log.warn("Bad request...")
                tries += 1
                if tries == 5:
                    break
                sleep(1)

            if not found:
                exit('Max retries hit')

            #log.debug(str(blob))
            # https://s.yimg.com/xe/i/us/sp/v/mlb_cutout/players_l/09182018/11000.1.png
#            m = re.match('.*/(https.+/)(\d+\.png)', str(blob))
            m = re.match('.*/(https.+/)([\d,\.]+png).*', str(blob))
            if m:
                url = m.group(1)
                filename = m.group(2)
                url += filename
            else:
                # silhouette@2x.png
                #m = re.match('.*/https.+/silhouette@2x.png', str(blob))
                m = re.match('.*silhouette@2x.png.*', str(blob))
                if m:
                    log.warn('silhouette'.format(filename))
                    res.increment('silhouette')
                    continue
                else:
                    log.error('image path not found in HTML'.format(filename))
                    log.info(str(blob))
                    res.increment('regex fail')
                    continue

            log.info('Retrieving {}...'.format(filename))
            try:
                urllib.request.urlretrieve(url, full_path)
                res.increment('retrieved')
            except Exception:
                log.error('URL fail: {}'.format(url))
                res.increment('retrieval fail')

        res.report(show_total=True)        

            # filename = "{}_{}_{}.png".format(player.yahoo_id, player.first_name.lower(), player.last_name.lower())
            # full_path = image_path + filename
            # full_path = full_path.replace(' ', '_')       # get rid of spaces
            #
            # if os.path.isfile(full_path):
            #     log.debug('{} found'.format(full_path))
            # else:
            #     log.debug('{} not found'.format(full_path))

        # one-time code to pretify the ugly html source
        # see prettify.py in /Pages
        #
        # fh = open("/Users/robmo/Code/Python/Baseball/pages/matt_barnes.html")
        # page = fh.read()
        # fh.close()
        # soup = BeautifulSoup(page, 'html.parser')
        #
        # fh = open("/Users/robmo/Code/Python/Baseball/pages/matt_barnes_2.html", "w")
        # fh.write(soup.prettify())
        # fh.close()
        # exit()
