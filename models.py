from django.db import models


class JournalRepecSettings(models.Model):
    journal = models.OneToOneField(
        "journal.Journal",
        on_delete=models.CASCADE,
        related_name="repec_settings",
    )
    archive_code = models.CharField(
        max_length=20,
        help_text=(
            "Two- or three-letter archive code assigned by REPEC "
            "(e.g. 'sur'). Contact repec@repec.org to obtain one."
        ),
    )
    series_code = models.CharField(
        max_length=20,
        help_text=(
            "Six-character series code that uniquely identifies this "
            "journal within the archive (e.g. 'surrec')."
        ),
    )
    maintainer_email = models.EmailField(
        help_text="Contact address REPEC will use to report errors.",
    )
    maintainer_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional name of the archive maintainer.",
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Uncheck to stop exposing ReDIF endpoints for this journal.",
    )

    class Meta:
        verbose_name = "Journal REPEC Settings"
        verbose_name_plural = "Journal REPEC Settings"

    def __str__(self):
        return f"REPEC – {self.journal}"
