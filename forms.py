from django import forms

from plugins.repec.models import JournalRepecSettings


class JournalRepecSettingsForm(forms.ModelForm):
    class Meta:
        model = JournalRepecSettings
        fields = [
            "archive_code",
            "series_code",
            "maintainer_email",
            "maintainer_name",
            "enabled",
        ]
