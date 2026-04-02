from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from security.decorators import editor_user_required

from plugins.repec import logic
from plugins.repec.forms import JournalRepecSettingsForm
from plugins.repec.models import JournalRepecSettings

_PLAIN_TEXT = "text/plain; charset=utf-8"


def _get_enabled_settings_or_404(request):
    settings = logic.get_repec_settings(request.journal)
    if settings is None:
        raise Http404
    return settings


def archive_rdf(request):
    """Serve the ReDIF-Archive 1.0 template."""
    settings = _get_enabled_settings_or_404(request)
    content = logic.build_archive_rdf(settings, request)
    return HttpResponse(content, content_type=_PLAIN_TEXT)


def series_rdf(request):
    """Serve the ReDIF-Series 1.0 template."""
    settings = _get_enabled_settings_or_404(request)
    content = logic.build_series_rdf(settings, request)
    return HttpResponse(content, content_type=_PLAIN_TEXT)


def papers_index(request):
    """
    Serve a plain-text index of article RDF URLs.

    REPEC crawlers use this listing to discover individual paper files.
    """
    settings = _get_enabled_settings_or_404(request)
    articles = logic.get_published_articles(request.journal)
    lines = [
        request.journal.site_url(path=f"/plugins/repec/papers/{a.pk}.rdf")
        for a in articles
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type=_PLAIN_TEXT)


def article_rdf(request, article_id):
    """Serve the ReDIF-Article 1.0 template for a single published article."""
    settings = _get_enabled_settings_or_404(request)
    articles = logic.get_published_articles(request.journal)
    article = get_object_or_404(articles, pk=article_id)
    content = logic.build_article_rdf(settings, article, request)
    return HttpResponse(content, content_type=_PLAIN_TEXT)


@editor_user_required
def repec_admin(request):
    """Settings page for configuring REPEC for the current journal."""
    try:
        instance = request.journal.repec_settings
    except JournalRepecSettings.DoesNotExist:
        instance = None

    form = JournalRepecSettingsForm(
        request.POST or None,
        instance=instance,
    )

    if request.method == "POST" and form.is_valid():
        settings = form.save(commit=False)
        settings.journal = request.journal
        settings.save()
        return redirect("repec_admin")

    archive_url = None
    series_url = None
    papers_url = None
    if instance and instance.enabled:
        archive_url = request.journal.site_url(path="/plugins/repec/archive.rdf")
        series_url = request.journal.site_url(path="/plugins/repec/series.rdf")
        papers_url = request.journal.site_url(path="/plugins/repec/papers/")

    return render(
        request,
        "repec/admin.html",
        {
            "form": form,
            "instance": instance,
            "archive_url": archive_url,
            "series_url": series_url,
            "papers_url": papers_url,
            "article_count": logic.get_published_articles(request.journal).count(),
        },
    )
