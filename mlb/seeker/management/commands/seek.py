from datetime import date
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from time import sleep

from common.utils import get_logger
from seeker.seeker import get_games

log = get_logger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):

        # 2018 started 3/29

        cur_date = date(2018, 9, 1)
        today = cur_date
        today = date(2018, 9, 11)
        while cur_date <= today:
            # all star game 7/17
            if cur_date.month != 7 or cur_date.day != 17:
                get_games(cur_date)
            cur_date += relativedelta(days=1)

        # import re
        #
        # name = '22 Jorge De La Rosa'
        # chunks = name.split(' ')
        #
        # m = re.match('(\d+)', chunks[0])
        # if m:
        #     number = m.group(1)
        #     chunks.pop(0)
        #     number = int(number)
        # else:
        #     number = None
        # print('number {}'.format(number))
        #
        # first_name = chunks[0]
        # last_name = chunks[-1]
        # middle_name = None
        #
        # if len(chunks) > 2:
        #     middle_name = chunks[1]
        #     for i in range(2, len(chunks) - 1):
        #         middle_name += ' {}'.format(chunks[i])
        #
        # print('first_name {}'.format(first_name))
        # print('middle_name {}'.format(middle_name))
        # print('last_name {}'.format(last_name))
        # exit()

        # from data.models import Player
        # for player in Player.objects.all():
        #
        #     # name = player.first_name
        #     # if player.middle_name:
        #     #     name += " " + player.middle_name
        #     # name += " " + player.last_name
        #     # player.name = name
        #
        #     if player.last_name == 'Jr.':
        #         player.suffix = 'Jr.'
        #         player.last_name = player.middle_name
        #         player.save()
        # exit()
        #