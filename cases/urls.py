from django.urls import path

from .views import CaseListView

urlpatterns = [
    path('cases/', CaseListView.as_view(), name='case-list'),
]
