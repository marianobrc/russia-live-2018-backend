from django.contrib import admin
from .models import PushToken


class PushTokenAdmin(admin.ModelAdmin):
    pass


admin.site.register(PushToken, PushTokenAdmin)
