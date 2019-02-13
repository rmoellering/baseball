from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Manager
import re

from common.utils import get_logger

log = get_logger(__name__)


class TeamManager(Manager):

    def get_or_create(self, divs):

        # extract logo URL from HTML
        logo = divs[0].find(name='img')

        # sometimes they do this!
        # style="background-image:url(https://s.yimg.com/xe/assets/logos/cv/api/default/20180410/nationals_wblrgr_70x70.png);"
        logo_sm = None
        try:
            m = re.match('.+url\((.+)\).+', logo['style'])
            if m:
                logo_sm = m.group(1)
        except KeyError:
            logo_sm = logo['src']

        # extract city and name from HTML
        # divs[1] will have an extra span in it if the game is live (svg bat logo)
        # city should always be 1st and team last
        spans = divs[1].find_all(name='span')
        city = spans[0].text
        name = spans[-1].text

        try:
            team = self.get(name=name)
            if logo_sm and not team.logo_sm:
                team.fetch_logo_sm()
                team.logo_sm = logo_sm
                team.save()
        except ObjectDoesNotExist:
            log.info("Couldn't find {}, creating new team.".format(name))

            team = self.create(
                name=name,
                city=city,
                logo_sm=logo_sm,
            )
            team.fetch_logo_sm()

        return team


class PlayerManager(Manager):

    def get_or_create(self, link, name, team):

        m = re.match('/mlb/players/(\d+)', link)
        if m:
            yahoo_id = m.group(1)
        else:
            raise ValueError("Couldn't find yahoo id in: {}".format(link))

        try:
            player = self.get(yahoo_id=yahoo_id)
            if player.team_id != team.id:
                log.info("New team for {}: {}".format(player.name, team.name))
                player.team = team
                player.save()
        except ObjectDoesNotExist:
            log.info("Couldn't find {}, creating new player.".format(yahoo_id))

            chunks = name.split(' ')

            m = re.match('(\d+)', chunks[0])
            if m:
                number = m.group(1)
                chunks.pop(0)
                name = name.replace('{} '.format(number), '')
                number = int(number)
                log.info('{} | {}'.format(number, name))
            else:
                number = None

            if chunks[-1] in ['Jr.', 'III']:
                suffix = chunks[-1]
                chunks.pop(-1)
            else:
                suffix = None

            first_name = chunks[0]
            last_name = chunks[-1]
            middle_name = None

            if len(chunks) > 2:
                middle_name = chunks[1]
                for i in range(2, len(chunks) - 1):
                    middle_name += ' {}'.format(chunks[i])

            # TODO: DOB
            player = self.create(
                yahoo_id=yahoo_id,
                team=team,
                name=name,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                suffix=suffix,
                number=number
            )
            log.debug('Created: {} | {} | {} | {} | {}|{}|{}|{}'.
                      format(player.yahoo_id, player.team.name, player.number, player.name,
                             player.first_name, player.middle_name, player.last_name, player.suffix))

        return player
