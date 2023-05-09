from django.db import models


class BaseAbstract(models.Model):
    @classmethod
    def fields(cls):
        return [i.name for i in cls._meta.fields]

    @classmethod
    def int_field(cls, fi):
        return isinstance(getattr(cls, fi).field, (models.IntegerField, models.PositiveIntegerField,
                                                   models.BigIntegerField, models.SmallIntegerField,
                                                   models.PositiveSmallIntegerField))

    class Meta:
        abstract = True
