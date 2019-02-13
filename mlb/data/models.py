from django.contrib.postgres.fields import JSONField
from django.db import models
import re

from .managers import TeamManager, PlayerManager
from common.models import AbstractStampedModel, AbstractEnumModel
from common.utils import get_logger

log = get_logger(__name__)


class GameStatus(AbstractEnumModel):
    FUTURE = 1
    IN_PROGRESS = 2
    DELAYED = 3
    POSTPONED = 4
    FINISHED = 5
    OTHER = 6

    CHOICES = (
        (FUTURE, 'Future'),
        (IN_PROGRESS, 'In Progress'),
        (DELAYED, 'Delayed'),
        (POSTPONED, 'Postponed'),
        (FINISHED, 'Finished'),
        (OTHER, 'Other')
    )


class Park(AbstractStampedModel):
    name = models.CharField(max_length=50)
    city = models.CharField(max_length=25)
    state = models.CharField(max_length=2)


class Team(AbstractStampedModel):
    abbr = models.CharField(max_length=3)
    name = models.CharField(max_length=50, db_index=True)
    city = models.CharField(max_length=25)
    state = models.CharField(max_length=3)
    logo_sm = models.CharField(max_length=100)
    logo_lg = models.CharField(max_length=100)
    park = models.ForeignKey(Park, on_delete=models.CASCADE, null=True)
    league = models.CharField(max_length=1)
    division = models.CharField(max_length=1)

    objects = TeamManager()

    def fetch_logo_sm(self):
        log.info('Getting {} small logo...'.format(self.name))

    @property
    def full_name(self):
        return '{} {}'.format(self.city, self.name)

    @property
    def yahoo_name(self):
        return '{}-{}'.format(
            self.city.lower().replace(' ', '-').replace('.', ''),
            self.name.lower().replace(' ', '-')
        )


class Player(AbstractStampedModel):
    yahoo_id = models.IntegerField(unique=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default='')
    first_name = models.CharField(max_length=25)
    middle_name = models.CharField(max_length=25, null=True)
    last_name = models.CharField(max_length=25)
    suffix = models.CharField(max_length=5, null=True)
    dob = models.DateField(null=True)
    number = models.IntegerField(null=True)

    objects = PlayerManager()

    @property
    def p_name(self):
        p_name = format(self.first_name[0])
        if self.middle_name:
            p_name = '{} {}'.format(p_name, self.middle_name)
        p_name = '{} {}'.format(p_name, self.last_name)
        if self.suffix:
            p_name = '{} {}'.format(p_name, self.suffix)
            p_name = p_name.replace('.', '')
        return p_name


class Game(AbstractStampedModel):
    yahoo_id = models.IntegerField(unique=True)
    park = models.ForeignKey(Park, on_delete=models.CASCADE, null=True)
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_team')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_team')
    start = models.DateField(db_index=True, null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    status = models.ForeignKey(GameStatus, on_delete=models.CASCADE)
    progress = models.CharField(max_length=6, null=True)
    home_pitcher = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='home_pitcher', null=True)
    away_pitcher = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='away_pitcher', null=True)
    home_runs = models.IntegerField(default=0)
    away_runs = models.IntegerField(default=0)
    home_hits = models.IntegerField(default=0)
    away_hits = models.IntegerField(default=0)
    home_errors = models.IntegerField(default=0)
    away_errors = models.IntegerField(default=0)
    innings = models.IntegerField(default=0)
    inning_data = JSONField()

    def set_status(self, yahoo_status):
        if yahoo_status == 'Upcoming':
            self.status = GameStatus.object_by_id(GameStatus.FUTURE)
        elif yahoo_status == 'Live':
            self.status = GameStatus.object_by_id(GameStatus.IN_PROGRESS)
        elif yahoo_status == 'Finished':
            self.status = GameStatus.object_by_id(GameStatus.FINISHED)
        else:
            raise ValueError('Unrecognized yahoo status: {}'.format(yahoo_status))

    def extract_yahoo_id(self, source):
        # data-tst="GameItem-mlb.g.380815116"
        # url: /mlb/milwaukee-brewers-chicago-cubs-380815116/
        # {away first}-{away last}-{home first}-{away last}-{id}
        m = re.match('GameItem-mlb.g.([0-9]+)', source)
        if m:
            self.yahoo_id = m.group(1)
        else:
            log.warn('Could not find yahoo game id')


class BatterGame(AbstractStampedModel):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    at_bats = models.IntegerField(default=0)
    runs = models.IntegerField(default=0)
    hits = models.IntegerField(default=0)
    runs_batted_in = models.IntegerField(default=0)
    home_runs = models.IntegerField(default=0)
    stolen_bases = models.IntegerField(default=0)
    walks = models.IntegerField(default=0)
    strikeouts = models.IntegerField(default=0)
    left_on_base = models.IntegerField(default=0)


class PitcherGame(AbstractStampedModel):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    spot = models.IntegerField(default=0)           # can't use 'order'
    innings = models.DecimalField(default=0, max_digits=3, decimal_places=1)
    whole_innings = models.IntegerField(default=0)
    outs = models.IntegerField(default=0)
    hits = models.IntegerField(default=0)
    runs = models.IntegerField(default=0)
    earned_runs = models.IntegerField(default=0)
    walks = models.IntegerField(default=0)
    strikeouts = models.IntegerField(default=0)
    home_runs = models.IntegerField(default=0)
    pitches = models.IntegerField(default=0)
    strikes = models.IntegerField(default=0)
    ground_balls = models.IntegerField(default=0)
    fly_balls = models.IntegerField(default=0)
    batters = models.IntegerField(default=0)
    win = models.BooleanField(default=False)
    loss = models.BooleanField(default=False)
    hold = models.BooleanField(default=False)
    sv = models.BooleanField(default=False)         # can't overload 'save'
    blown = models.BooleanField(default=False)

    @property
    def balls(self):
        return self.pitches - self.strikes
