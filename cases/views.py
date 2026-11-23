from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import SepsisCase
from .serializers import SepsisCaseSerializer


class CaseListView(generics.ListAPIView):
    serializer_class = SepsisCaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SepsisCase.objects.select_related('hospital').order_by('-arrival_time')
        user = self.request.user

        if not user.is_staff:
            if not hasattr(user, 'profile'):
                return qs.none()
            qs = qs.filter(hospital=user.profile.hospital)

        if self.request.query_params.get('hypotension') == 'true':
            qs = qs.filter(hypotension=True)
        return qs
