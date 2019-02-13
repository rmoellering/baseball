
from django.db import models

from .utils import get_logger


log = get_logger(__name__)


class AbstractStampedModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    date_updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        if hasattr(self, 'id'):
            return '<{0.__class__.__name__} #{0.id}>'.format(self)
        else:
            return '<{0.__class__.__name__}>'.format(self)


class AbstractEnumModel(AbstractStampedModel):

    # Override default AutoField for 'id' to IntegerField because we don't want auto-incrementing.
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)

    # objects = CachingManager()

    # placeholder for set of tuples representing all id/name pairs for this enum
    CHOICES = ()
    choices_dict = None

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    @classmethod
    def get_name(cls, _id):
        if not cls.choices_dict:
            try:
                cls.choices_dict = dict(cls.CHOICES)
            except ValueError:
                cls.choices_dict = {}
                for pk, name, description in cls.CHOICES:
                    cls.choices_dict[pk] = name

        return cls.choices_dict[_id]

    def get_dict(self):
        return dict(self.CHOICES)

    @classmethod
    def object_by_id(cls, _id):
        return cls(id=_id, name=cls.get_name(_id))
