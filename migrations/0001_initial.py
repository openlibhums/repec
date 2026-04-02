from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("journal", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="JournalRepecSettings",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "journal",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="repec_settings",
                        to="journal.journal",
                    ),
                ),
                (
                    "archive_code",
                    models.CharField(
                        max_length=20,
                        help_text=(
                            "Two- or three-letter archive code assigned by REPEC "
                            "(e.g. 'sur'). Contact repec@repec.org to obtain one."
                        ),
                    ),
                ),
                (
                    "series_code",
                    models.CharField(
                        max_length=20,
                        help_text=(
                            "Six-character series code that uniquely identifies this "
                            "journal within the archive (e.g. 'surrec')."
                        ),
                    ),
                ),
                (
                    "maintainer_email",
                    models.EmailField(
                        help_text="Contact address REPEC will use to report errors.",
                    ),
                ),
                (
                    "maintainer_name",
                    models.CharField(
                        blank=True,
                        max_length=200,
                        help_text="Optional name of the archive maintainer.",
                    ),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck to stop exposing ReDIF endpoints for this journal.",
                    ),
                ),
            ],
            options={
                "verbose_name": "Journal REPEC Settings",
                "verbose_name_plural": "Journal REPEC Settings",
            },
        ),
    ]
