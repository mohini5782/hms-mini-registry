from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Hospital, SepsisCase, UserProfile

User = get_user_model()


class CaseAccessTests(APITestCase):
    def setUp(self):
        self.hosp_a = Hospital.objects.create(name='Hospital A', region='East')
        self.hosp_b = Hospital.objects.create(name='Hospital B', region='West')

        self.alice = User.objects.create_user('alice', password='pw12345')
        UserProfile.objects.create(user=self.alice, hospital=self.hosp_a)

        now = timezone.now()
        self.case_a = SepsisCase.objects.create(hospital=self.hosp_a, arrival_time=now)
        self.case_b = SepsisCase.objects.create(hospital=self.hosp_b, arrival_time=now)

    def test_user_sees_only_own_hospital(self):
        self.client.force_authenticate(self.alice)
        res = self.client.get('/api/cases/')
        ids = [row['id'] for row in res.data['results']]
        self.assertEqual(res.status_code, 200)
        self.assertIn(self.case_a.id, ids)
        self.assertNotIn(self.case_b.id, ids)

    def test_anonymous_user_is_blocked(self):
        res = self.client.get('/api/cases/')
        self.assertIn(res.status_code, (401, 403))

    def test_user_without_profile_sees_nothing(self):
        stray = User.objects.create_user('stray', password='pw12345')
        self.client.force_authenticate(stray)
        res = self.client.get('/api/cases/')
        self.assertEqual(res.data['results'], [])


class CaseConstraintTests(APITestCase):
    def test_discharge_before_arrival_is_rejected(self):
        hosp = Hospital.objects.create(name='Hospital C', region='North')
        arrival = timezone.now()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SepsisCase.objects.create(
                    hospital=hosp,
                    arrival_time=arrival,
                    discharge_time=arrival - timedelta(days=1),
                )
