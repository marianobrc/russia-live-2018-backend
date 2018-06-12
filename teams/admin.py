from django.contrib import admin
from .models import Team, Player


class TeamAdmin(admin.ModelAdmin):
    list_display = ('competition', 'country', 'external_id',  'name', )


class PlayerAdmin(admin.ModelAdmin):
    list_display = ('common_name', 'external_id', 'first_name', 'last_name', 'position', )
    list_filter = (
        'team',
    )


admin.site.register(Team, TeamAdmin)
admin.site.register(Player, PlayerAdmin)

