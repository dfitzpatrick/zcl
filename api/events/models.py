import typing
from datetime import datetime

from dateutil import rrule
from django.db import models

RECURRANCE_CHOICES = (
    (rrule.YEARLY, "Yearly"),
    (rrule.MONTHLY, "Monthly"),
    (rrule.WEEKLY, "Weekly"),
    (rrule.DAILY, "Daily"),
)

class EventSchedule(models.Model):
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    start_date = models.DateTimeField(default=datetime.now())
    end_date = models.DateTimeField(default=datetime.now())

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    frequency = models.IntegerField(choices=RECURRANCE_CHOICES, default=rrule.WEEKLY)

    @property
    def event_dates(self) -> typing.List[datetime]:
        return list(
            rrule.rrule(
                freq=self.frequency,
                dtstart=self.start_date,
                until=self.end_date
            )
        )

