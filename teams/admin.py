from django.contrib import admin
from .models import Team, Player


class TeamAdmin(admin.ModelAdmin):
    list_display = ('competition', 'country', 'external_id',  'name', )


class PlayerAdmin(admin.ModelAdmin):
    list_filter = (
        'team',
    )


admin.site.register(Team, TeamAdmin)
admin.site.register(Player, PlayerAdmin)

