from rest_framework import serializers

from .models import SepsisCase


class SepsisCaseSerializer(serializers.ModelSerializer):
    hospital = serializers.CharField(source='hospital.name', read_only=True)

    class Meta:
        model = SepsisCase
        fields = [
            'id', 'hospital', 'arrival_time', 'first_antibiotic_time',
            'hypotension', 'discharge_time', 'abx_within_3h',
        ]
