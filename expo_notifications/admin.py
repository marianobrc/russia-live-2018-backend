from django.contrib import admin
from .models import PushToken


class PushTokenAdmin(admin.ModelAdmin):
    list_display = (
        'token', 'active',
    )


admin.site.register(PushToken, PushTokenAdmin)
