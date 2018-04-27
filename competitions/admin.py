from django.contrib import admin
from .models import Competition, CompetitionStage, Standing


class CompetitionAdmin(admin.ModelAdmin):
    pass


class CompetitionStageAdmin(admin.ModelAdmin):
    pass


class StandingAdmin(admin.ModelAdmin):
    list_display = (
        'stage', 'sub_group', 'position', 'team',
        'played', 'won', 'drawn', 'lost', 'goal_difference', 'points',
    )


admin.site.register(Competition, CompetitionAdmin)
admin.site.register(CompetitionStage, CompetitionStageAdmin)
admin.site.register(Standing, StandingAdmin)

