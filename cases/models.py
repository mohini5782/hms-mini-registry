from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Hospital(models.Model):
    name = models.CharField(max_length=120, unique=True)
    region = models.CharField(max_length=60)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile'
    )
    hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.user.username} @ {self.hospital.name}'


class SepsisCase(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT, related_name='cases')
    source_response_id = models.IntegerField(null=True, blank=True, unique=True)
    arrival_time = models.DateTimeField()
    first_antibiotic_time = models.DateTimeField(null=True, blank=True)
    hypotension = models.BooleanField(default=False)
    abx_within_3h = models.BooleanField(default=False)
    discharge_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(discharge_time__isnull=True) | Q(discharge_time__gte=F('arrival_time')),
                name='discharge_not_before_arrival',
            ),
        ]

    def __str__(self):
        return f'Case {self.pk} ({self.hospital.name})'
