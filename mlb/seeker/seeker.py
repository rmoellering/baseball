from bs4 import BeautifulSoup
from datetime import date
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from io import BytesIO
import json
from lxml import html, etree
#from PIL import Image
import re
import requests
from time import sleep

from common.utils import get_logger
from data.models import Game, Team, Player, BatterGame, PitcherGame

log = get_logger(__name__)


def get_games(game_date, from_file=False, force_overwrite=False):

    # 2018 season started 3-29

    #from_file = True

    log.info("")
    log.info("----<>----<>----<>----<>----<>----<>----<>----<>----<>----<>----<>----<>----<>----<>----<>----<>----")

    if not game_date:
        game_date = timezone.now().date()

    log.info('<[ {} ]>'.format(game_date))

    sections = get_blob(game_date, from_file)

    for section in sections:
        # 1st div below
        title = section.find('div')
        game_type = title.text
        if game_type in ['Live', 'Upcoming', 'Finished']:
            #log.info(game_type)

            # < li class ="Bgc(bg-mod) Bgc(secondary):h Pos(r) D(ib) W(270px) Mend(20px) Mt(20px) Va(t)" data-tst="GameItem-mlb.g.380815116" data-reactid="18" >

            kwargs = {"data-tst": re.compile("GameItem-mlb.g")}
            games = 0
            for game in section.find_all(name='li', **kwargs):

                cur_game = Game()

                cur_game.start = game_date
                cur_game.set_status(game_type)
                cur_game.extract_yahoo_id(game['data-tst'])

                # ** temporary **
                try:
                    old_game = Game.objects.get(yahoo_id=cur_game.yahoo_id)
                    log.info('Found dup game {}, deleting...'.format(old_game.yahoo_id))
                    old_game.delete()
                except ObjectDoesNotExist:
                    pass

                # capture progress for live games
                if game_type == 'Live':
                    cur_game.progress = game.find(name='span').text

                ul = game.find(name='ul')
                lis = ul.find_all(name='li')

                # away info
                divs = [div for div in lis[0].children]
                cur_game.away_team = Team.objects.get_or_create(divs)

                if game_type != 'Upcoming':
                    cur_game.away_runs = divs[2].find('span').text

                # home info
                divs = [div for div in lis[1].children]
                cur_game.home_team = Team.objects.get_or_create(divs)

                if game_type != 'Upcoming':
                    cur_game.home_runs = divs[2].find('span').text

                log.info("{} {} @ {} {}".format(
                    cur_game.away_team.full_name, cur_game.away_runs,
                    cur_game.home_team.full_name, cur_game.home_runs))

                games += 1

                # we need to go deeper!

                blob = get_blob2(cur_game, from_file)
                table = blob.find('table')
                rows = table.find_all('tr')
                inning_labels = rows[0].find_all('th')
                away_innings = rows[1].find_all('td')
                home_innings = rows[2].find_all('td')
                last_inning = None
                inning = None

                inning_data = {}
                for inning in range(1, len(away_innings) - 1):

                    # marks beginning of RHE area
                    if 'Pstart(20px)!' in away_innings[inning]['class']:
                        # TODO: handle extra innings, missing data
                        if int(last_inning) > 12:
                            log.warn('Extras ({})'.format(last_inning))
                        inning = int(inning)
                        break

                    away = away_innings[inning].text if away_innings[inning].text in ['X', '-'] else \
                        int(away_innings[inning].text)
                    home = home_innings[inning].text if home_innings[inning].text in ['X', '-'] else \
                        int(home_innings[inning].text)
                    inning_data[inning] = [away, home]
                    last_inning = inning_labels[inning].text

                cur_game.inning_data = inning_data
                cur_game.innings = int(last_inning)

                # R H E
                cur_game.away_runs = away_innings[inning].text
                cur_game.away_hits = away_innings[inning + 1].text
                cur_game.away_errors = away_innings[inning + 2].text
                cur_game.home_runs = home_innings[inning].text
                cur_game.home_hits = home_innings[inning + 1].text
                cur_game.home_errors = home_innings[inning + 2].text
                cur_game.save()

                # log.info('Away {} {} {}'.format(cur_game.away_runs, cur_game.away_hits, cur_game.away_errors))
                # log.info('Home {} {} {}'.format(cur_game.home_runs, cur_game.home_hits, cur_game.home_errors))


                # batters

                #< div class ="player-stats" data-reactid="339" >
                stats = blob.find('div', class_='player-stats')
                tables = stats.find_all('table')

                parse_batters(data=tables[0], team=cur_game.away_team, game=cur_game)
                parse_batters(data=tables[1], team=cur_game.home_team, game=cur_game)

                # pitchers

                pitches_strikes = None
                ground_fly = None
                batters_faced = None
                dds = stats.find_all('dd', _class='')
                for dd in dds:
                    span = dd.find('span')
                    if span:
                        if span.text == 'Pitches-strikes':
                            pitches_strikes = dd.text
                        if span.text == 'Ground balls-fly balls':
                            ground_fly = dd.text
                        if span.text == 'Batters faced':
                            batters_faced = dd.text
                    else:
                        log.info('No SPAN')

                parse_pitchers(data=tables[2], team=cur_game.away_team, game=cur_game,
                               pitches_strikes=pitches_strikes, ground_fly=ground_fly, batters_faced=batters_faced)
                parse_pitchers(data=tables[3], team=cur_game.home_team, game=cur_game,
                               pitches_strikes=pitches_strikes, ground_fly=ground_fly, batters_faced=batters_faced)

                log.info('Created game {}'.format(cur_game.yahoo_id))


def get_blob(game_date, from_file):

    base = 'https://sports.yahoo.com/mlb/scoreboard/?confId=&schedState=2&dateRange='

    url = base + '{}-{}-{}'.format(game_date.year, f'{game_date.month:02}', f'{game_date.day:02}')

    tries = 0
    found = False
    sections = None
    while tries < 5:
        if from_file:
            fh = open("../Pages/2018-08-15.html")
            page = fh.read()
            fh.close()
            soup = BeautifulSoup(page, 'html.parser')
        else:
            page = requests.get(url)
            if page.status_code != 200:
                exit('({}) - {}'.format(page.status_code, url))
            soup = BeautifulSoup(page.content, 'html.parser')

        try:
            blob = soup.find('div', id="scoreboard-group-2")
            sections = blob.find_all('div', class_="Mb(30px)")
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

    return sections


def get_blob2(game, from_file):

    base = 'https://sports.yahoo.com/mlb/'

    url = base + '{}-{}-{}/'.format(
        game.away_team.yahoo_name,
        game.home_team.yahoo_name,
        game.yahoo_id,
    )

    tries = 0
    found = False
    blob = None

    while tries < 5:
        if from_file:
            fh = open("../Pages/380819102.html")
            # fh = open("../Pages/380820121_extras.html")
            page = fh.read()
            fh.close()
            soup = BeautifulSoup(page, 'html.parser')
        else:
            page = requests.get(url)
            if page.status_code != 200:
                exit('({}) - {}'.format(page.status_code, url))
            soup = BeautifulSoup(page.content, 'html.parser')

        try:
            #blob = soup.find('div', id="YDC-Col1")
            blob = soup.find('div', id="Col1-0-Boxscore-Proxy")
            if blob:
                found = True
                break
            blob = soup.find('div', id="Main-0-Boxscore-Proxy")
            if blob:
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
        # fh = open("../pages/bad_req.html", "w")
        # fh.write(soup.prettify())
        # fh.close()
        exit('Max retries hit')

    return blob


def parse_batters(data, team, game):

    tbody = data.find('tbody')
    # AB R H RBI HR SB BB K LOB AVG
    for tr in tbody.find_all('tr'):
        batter = tr.find('th')
        if batter.text == 'Totals':
            return
        link = batter.find('a')
        name = link.text
        player = Player.objects.get_or_create(link=link['href'], name=name, team=team)

        # TODO: batting order, sub/PH

        stats = tr.find_all('td')
        BatterGame.objects.create(
            player=player,
            game=game,
            team=team,
            at_bats=int(stats[0].text),
            runs=int(stats[1].text),
            hits=int(stats[2].text),
            runs_batted_in=int(stats[3].text),
            home_runs=int(stats[4].text),
            stolen_bases=int(stats[5].text),
            walks=int(stats[6].text),
            strikeouts=int(stats[7].text),
            left_on_base=int(stats[8].text)
        )


def parse_pitchers(data, team, game, pitches_strikes, ground_fly, batters_faced):

    tbody = data.find('tbody')

    # IP H R ER BB K HR WHIP ERA
    spot = 1
    for tr in tbody.find_all('tr'):
        pitcher = tr.find('th')
        link = pitcher.find('a')
        name = link.text
        player = Player.objects.get_or_create(link=link['href'], name=name, team=team)

        stats = tr.find_all('td')
        innings = Decimal(stats[0].text)

        # TODO: pitching order, IBB, HBP
        # TODO: handle same last name for 2 or more pitchers in a game
        p_name = player.p_name

        subs = {
            'Felipe Vázquez': 'F Rivero',
            'Eduardo Rodriguez': 'E Rodríguez',
            'Yefrey Ramirez': 'Y Ramírez',
            'Yefry Ramírez': 'Y Ramirez',
            'Austin L. Adams': 'A Adams',
            'José Fernández': 'J Fernandez'
        }
        #'Oliver Pérez': 'O P??rez'

        found = False
        subbed = False
        while not found:
            m = re.match('.*{} (\d+)-(\d+).*'.format(p_name), pitches_strikes)
            if m:
                pitches = m.group(1)
                strikes = m.group(2)
                found = True
            else:
                if innings == Decimal(0):
                    pitches = 0
                    strikes = 0
                    found = True
                elif player.name in subs and not subbed:
                    log.warn('Swapping {} for {} based on {}'.format(subs[player.name], p_name, player.name))
                    p_name = subs[player.name]
                    subbed = True
                # TODO: haven't solved this one yet...  O P??rez
                elif player.name == 'Oliver Pérez' and game.start == date(2018, 8, 23):
                    pitches = 5
                    strikes = 4
                    found = True
                elif player.name == 'Jarlin García' and game.start == date(2018, 8, 23):
                    pitches = 39
                    strikes = 19
                    found = True
                else:
                    raise ValueError("Couldn't pitches-strikes for : [{} {}]\n{}".format(p_name, player.name, pitches_strikes))

        m = re.match('.*{} (\d+)-(\d+).*'.format(p_name), ground_fly)
        if m:
            ground_balls = m.group(1)
            fly_balls = m.group(2)
        else:
            if innings == Decimal(0):
                ground_balls = 0
                fly_balls = 0
            # see above
            elif player.name == 'Oliver Pérez' and game.start == date(2018, 8, 23):
                ground_balls = 0
                fly_balls = 1
            elif player.name == 'Jarlin García' and game.start == date(2018, 8, 23):
                ground_balls = 2
                fly_balls = 1
            else:
                raise ValueError("Couldn't ground-fly for : {}\n{}".format(p_name, ground_fly))

        # TODO: how can you have 0.2 IP and 0 batters faced?  pickoff?
        m = re.match('.*{} (\d+).*'.format(p_name), batters_faced)
        if m:
            batters = m.group(1)
        else:
            # TODO: < 1
            if innings in[Decimal(0), Decimal('0.1'), Decimal('0.2')]:
                batters = 0
            # see above
            elif player.name == 'Oliver Pérez' and game.start == date(2018, 8, 23):
                batters = 2
            elif player.name == 'Jarlin García' and game.start == date(2018, 8, 23):
                batters = 9
            else:
                raise ValueError("Couldn't batters for : {} (ip {})\n{}".format(player.p_name, innings, batters_faced))

        spans = pitcher.find_all('span')
        if len(spans) == 3:
            result = spans[1].text
            win = 'W' in result
            loss = 'L' in result
            hold = 'H' in result
            sv = 'SV' in result
            blown = 'BS' in result
        else:
            win = False
            loss = False
            hold = False
            sv = False
            blown = False

        PitcherGame.objects.create(
                player=player,
                game=game,
                team=team,
                spot=spot,
                innings=innings,
                whole_innings=innings - (innings % 1),
                outs=(innings % 1) * 10,
                hits=int(stats[1].text),
                runs=int(stats[2].text),
                earned_runs=int(stats[3].text),
                walks=int(stats[4].text),
                strikeouts=int(stats[5].text),
                home_runs=int(stats[6].text),
                pitches=pitches,
                strikes=strikes,
                ground_balls=ground_balls,
                fly_balls=fly_balls,
                batters=batters,
                win=win,
                loss=loss,
                hold=hold,
                sv=sv,
                blown=blown
            )
        spot += 1
