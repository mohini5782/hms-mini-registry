import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from cases.models import Hospital, SepsisCase, UserProfile

HOSPITALS = [
    ('Lakeside General', 'East'),
    ('Riverbend Medical', 'West'),
    ('Northfield Hospital', 'North'),
]


class Command(BaseCommand):
    help = 'Create fake hospitals, two users and sepsis cases'

    def add_arguments(self, parser):
        parser.add_argument('--cases', type=int, default=600)

    def handle(self, *args, **opts):
        User = get_user_model()
        hospitals = []
        for name, region in HOSPITALS:
            h, _ = Hospital.objects.get_or_create(name=name, defaults={'region': region})
            hospitals.append(h)

        for username, hosp in [('alice', hospitals[0]), ('bob', hospitals[1])]:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password('testpass123')
                user.save()
            UserProfile.objects.get_or_create(user=user, defaults={'hospital': hosp})

        now = timezone.now()
        rows = []
        for _ in range(opts['cases']):
            arrival = now - timedelta(days=random.randint(1, 120), hours=random.randint(0, 23))
            abx = None
            if random.random() < 0.9:
                abx = arrival + timedelta(minutes=random.randint(20, 400))
            rows.append(SepsisCase(
                hospital=random.choice(hospitals),
                arrival_time=arrival,
                first_antibiotic_time=abx,
                hypotension=random.random() < 0.4,
                discharge_time=arrival + timedelta(days=random.randint(2, 14)),
            ))
        SepsisCase.objects.bulk_create(rows)
        self.stdout.write(f'Created {len(rows)} cases')
