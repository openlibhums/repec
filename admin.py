from django.contrib import admin

from plugins.repec.models import JournalRepecSettings


@admin.register(JournalRepecSettings)
class JournalRepecSettingsAdmin(admin.ModelAdmin):
    list_display = ("journal", "archive_code", "series_code", "maintainer_email", "enabled")
    list_filter = ("enabled",)
    raw_id_fields = ("journal",)
