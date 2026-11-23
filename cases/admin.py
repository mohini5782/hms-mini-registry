from django.contrib import admin

from .models import Hospital, SepsisCase, UserProfile

admin.site.register(Hospital)
admin.site.register(UserProfile)
admin.site.register(SepsisCase)
