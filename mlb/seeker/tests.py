from datetime import date
from django.test.testcases import TestCase

from common.utils import get_logger

log = get_logger(__name__)


class SeekerTests(TestCase):

    @staticmethod
    def test_seek():
        from seeker.seeker import get_games
        print('test_seek')
        get_games(date(2018, 8, 12))
