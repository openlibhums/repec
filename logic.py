"""
ReDIF (Research Documents Information Format) generation logic.

Spec: http://openlib.org/acmes/root/docu/redif_1.html
"""

import re
from html import unescape

from django.utils import timezone

from submission.models import Article, STAGE_PUBLISHED


def strip_html(value):
    """Remove HTML tags and decode HTML entities from a string."""
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_field(name, value):
    """
    Return a ReDIF field line (or lines for multi-line values).

    Continuation lines must be indented with at least one space per spec.
    Returns an empty string when value is falsy so callers can filter.
    """
    if not value:
        return ""
    value = str(value).strip()
    if not value:
        return ""
    lines = value.splitlines()
    result = f"{name}: {lines[0]}"
    for line in lines[1:]:
        result += f"\n {line}"
    return result


def join_fields(fields):
    """Join a list of field strings, dropping empty ones, with a trailing newline."""
    return "\n".join(f for f in fields if f) + "\n"


def build_article_handle(settings, article):
    """
    Construct a REPEC handle for a journal article.

    Preferred format (Appendix C of spec):
        RePEC:{archive}:{series}:v:{volume}:y:{year}:i:{issue}:p:{start}-{end}

    Falls back to article PK when volume/issue/page data are missing.
    """
    parts = [f"RePEC:{settings.archive_code}:{settings.series_code}"]

    issue = article.issue

    if issue and issue.volume:
        parts.append(f"v:{issue.volume}")

    year = None
    if article.date_published:
        year = article.date_published.year
    elif issue and issue.date:
        year = issue.date.year
    if year:
        parts.append(f"y:{year}")

    if issue and issue.issue:
        parts.append(f"i:{issue.issue}")

    if article.first_page and article.last_page:
        parts.append(f"p:{article.first_page}-{article.last_page}")
    else:
        parts.append(str(article.pk))

    return ":".join(parts)


def build_archive_rdf(settings, request):
    """Return ReDIF-Archive 1.0 content as a string."""
    journal = settings.journal
    base_url = journal.site_url(path="/plugins/repec/")

    fields = [
        "Template-Type: ReDIF-Archive 1.0",
        format_field("Handle", f"RePEC:{settings.archive_code}"),
        format_field("Name", journal.name),
        format_field("URL", base_url),
        format_field("Maintainer-Email", settings.maintainer_email),
        format_field("Maintainer-Name", settings.maintainer_name),
        format_field("Homepage", journal.site_url()),
    ]
    return join_fields(fields)


def build_series_rdf(settings, request):
    """Return ReDIF-Series 1.0 content as a string."""
    journal = settings.journal

    description = ""
    if hasattr(journal, "description") and journal.description:
        description = strip_html(journal.description)

    fields = [
        "Template-Type: ReDIF-Series 1.0",
        format_field("Name", journal.name),
        format_field(
            "Handle",
            f"RePEC:{settings.archive_code}:{settings.series_code}",
        ),
        "Type: ReDIF-Article",
        format_field("Maintainer-Email", settings.maintainer_email),
        format_field("Maintainer-Name", settings.maintainer_name),
        format_field("ISSN", journal.issn),
        format_field("Description", description),
    ]
    return join_fields(fields)


def build_article_rdf(settings, article, request):
    """Return ReDIF-Article 1.0 content for a single article."""
    fields = ["Template-Type: ReDIF-Article 1.0"]

    for author in article.frozenauthor_set.all().order_by("order"):
        last = author.last_name or ""
        first = author.first_name or ""
        if author.middle_name:
            first = f"{first} {author.middle_name}"
        if last and first:
            author_name = f"{last}, {first}"
        else:
            author_name = author.full_name()

        fields.append(format_field("Author-Name", author_name))

        email = author.frozen_email
        if not email and author.author:
            email = author.author.email
        fields.append(format_field("Author-Email", email))
        fields.append(format_field("Author-Workplace-Name", author.institution))

    fields.append(format_field("Title", strip_html(article.title)))
    fields.append(format_field("Abstract", strip_html(article.abstract)))

    journal = article.journal
    fields.append(format_field("Journal", journal.name))

    issue = article.issue
    if issue:
        fields.append(format_field("Volume", issue.volume))
        fields.append(format_field("Issue", issue.issue))

    if article.date_published:
        fields.append(format_field("Year", article.date_published.year))
        fields.append(format_field("Month", article.date_published.month))
    elif issue and issue.date:
        fields.append(format_field("Year", issue.date.year))

    if article.first_page and article.last_page:
        fields.append(format_field("Pages", f"{article.first_page}-{article.last_page}"))
    elif article.page_numbers:
        fields.append(format_field("Pages", article.page_numbers))

    doi = article.get_doi()
    fields.append(format_field("DOI", doi))

    keywords = article.keywords.values_list("word", flat=True)
    if keywords:
        fields.append(format_field("Keywords", "; ".join(keywords)))

    for galley in article.galley_set.filter(public=True).order_by("sequence"):
        url = galley.path()
        if not url:
            continue
        fields.append(format_field("File-URL", url))
        mime = ""
        if galley.file and galley.file.mime_type:
            mime = galley.file.mime_type
        elif galley.type == "pdf":
            mime = "application/pdf"
        elif galley.type == "html":
            mime = "text/html"
        elif galley.type == "xml":
            mime = "text/xml"
        fields.append(format_field("File-Format", mime))

    fields.append(format_field("Handle", build_article_handle(settings, article)))

    return join_fields(fields)


def get_repec_settings(journal):
    """
    Return the enabled JournalRepecSettings for a journal, or None.
    Returns None when journal is None or has no REPEC configuration.
    """
    if journal is None:
        return None

    from plugins.repec.models import JournalRepecSettings

    try:
        settings = journal.repec_settings
    except JournalRepecSettings.DoesNotExist:
        return None
    return settings if settings.enabled else None


def get_published_articles(journal):
    """Return published articles for a journal, newest first."""
    return Article.objects.filter(
        journal=journal,
        stage=STAGE_PUBLISHED,
        date_published__lte=timezone.now(),
    ).order_by("-date_published")
