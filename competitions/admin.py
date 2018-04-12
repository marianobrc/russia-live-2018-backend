from django.contrib import admin
from .models import Competition, CompetitionStage


class CompetitionAdmin(admin.ModelAdmin):
    pass


class CompetitionStageAdmin(admin.ModelAdmin):
    pass


admin.site.register(Competition, CompetitionAdmin)
admin.site.register(CompetitionStage, CompetitionStageAdmin)


