from django.http import Http404
from django.test import RequestFactory, TestCase
from django.utils import timezone

from journal.models import Journal
from submission import models as sm_models
from utils.testing import helpers

from plugins.repec import logic, plugin_settings
from plugins.repec.models import JournalRepecSettings
from plugins.repec.views import archive_rdf, article_rdf, papers_index, series_rdf


def _make_settings(journal, **kwargs):
    defaults = {
        "archive_code": "tst",
        "series_code": "tstjnl",
        "maintainer_email": "repec@example.com",
        "maintainer_name": "Test Maintainer",
        "enabled": True,
    }
    defaults.update(kwargs)
    return JournalRepecSettings.objects.create(journal=journal, **defaults)


def _make_published_article(journal, **kwargs):
    defaults = {
        "stage": sm_models.STAGE_PUBLISHED,
        "date_published": timezone.now(),
        "title": "Productivity Spillovers in the Test Economy",
        "abstract": "This paper examines test effects.",
        "first_page": 1,
        "last_page": 10,
    }
    defaults.update(kwargs)
    return helpers.create_article(journal, **defaults)


class ArticleHandleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal, _ = helpers.create_journals()
        plugin_settings.install()
        cls.repec = _make_settings(cls.journal)

    def test_handle_with_full_metadata(self):
        article = _make_published_article(self.journal)
        issue = helpers.create_issue(self.journal, vol=3, number="2")
        issue.articles.add(article)
        article.primary_issue = issue
        article.save()

        handle = logic.build_article_handle(self.repec, article)

        self.assertIn("RePEC:tst:tstjnl", handle)
        self.assertIn("v:3", handle)
        self.assertIn("i:2", handle)
        self.assertIn("p:1-10", handle)

    def test_handle_falls_back_to_pk_without_pages(self):
        article = _make_published_article(
            self.journal, first_page=None, last_page=None
        )
        handle = logic.build_article_handle(self.repec, article)
        self.assertTrue(
            handle.endswith(f":{article.pk}"),
            f"Expected handle to end with pk, got: {handle}",
        )

    def test_handle_includes_year(self):
        article = _make_published_article(self.journal)
        handle = logic.build_article_handle(self.repec, article)
        self.assertIn(f"y:{timezone.now().year}", handle)


class BuildArchiveRdfTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal, _ = helpers.create_journals()
        plugin_settings.install()
        cls.repec = _make_settings(cls.journal)

    def test_contains_required_fields(self):
        request = RequestFactory().get("/")
        request.journal = self.journal
        content = logic.build_archive_rdf(self.repec, request)

        self.assertIn("Template-Type: ReDIF-Archive 1.0", content)
        self.assertIn("Handle: RePEC:tst", content)
        self.assertIn("Maintainer-Email: repec@example.com", content)
        self.assertIn("Name:", content)
        self.assertIn("URL:", content)


class BuildSeriesRdfTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal, _ = helpers.create_journals()
        plugin_settings.install()
        cls.repec = _make_settings(cls.journal)

    def test_contains_required_fields(self):
        request = RequestFactory().get("/")
        request.journal = self.journal
        content = logic.build_series_rdf(self.repec, request)

        self.assertIn("Template-Type: ReDIF-Series 1.0", content)
        self.assertIn("Handle: RePEC:tst:tstjnl", content)
        self.assertIn("Maintainer-Email: repec@example.com", content)
        self.assertIn("Type: ReDIF-Article", content)


class BuildArticleRdfTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal, _ = helpers.create_journals()
        plugin_settings.install()
        cls.repec = _make_settings(cls.journal)

    def test_contains_required_fields(self):
        article = _make_published_article(self.journal, with_author=True)
        request = RequestFactory().get("/")
        request.journal = self.journal
        content = logic.build_article_rdf(self.repec, article, request)

        self.assertIn("Template-Type: ReDIF-Article 1.0", content)
        self.assertIn("Title:", content)
        self.assertIn("Handle:", content)
        self.assertIn("Author-Name:", content)

    def test_html_stripped_from_title(self):
        article = _make_published_article(self.journal, title="<em>Clean</em> Title")
        request = RequestFactory().get("/")
        request.journal = self.journal
        content = logic.build_article_rdf(self.repec, article, request)

        self.assertIn("Title: Clean Title", content)
        self.assertNotIn("<em>", content)

    def test_html_stripped_from_abstract(self):
        article = _make_published_article(self.journal, abstract="<p>Key finding.</p>")
        request = RequestFactory().get("/")
        request.journal = self.journal
        content = logic.build_article_rdf(self.repec, article, request)

        self.assertIn("Abstract: Key finding.", content)
        self.assertNotIn("<p>", content)

    def test_pages_included_when_present(self):
        article = _make_published_article(self.journal, first_page=5, last_page=20)
        request = RequestFactory().get("/")
        request.journal = self.journal
        content = logic.build_article_rdf(self.repec, article, request)

        self.assertIn("Pages: 5-20", content)


class GetRepecSettingsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal, _ = helpers.create_journals()
        plugin_settings.install()

    def test_returns_none_for_none_journal(self):
        self.assertIsNone(logic.get_repec_settings(None))

    def test_returns_none_when_not_configured(self):
        self.assertIsNone(logic.get_repec_settings(self.journal))

    def test_returns_none_when_disabled(self):
        repec = _make_settings(self.journal, enabled=False)
        try:
            self.assertIsNone(logic.get_repec_settings(self.journal))
        finally:
            repec.delete()

    def test_returns_settings_when_enabled(self):
        repec = _make_settings(self.journal)
        try:
            self.assertIsNotNone(logic.get_repec_settings(self.journal))
        finally:
            repec.delete()


class GetPublishedArticlesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal, _ = helpers.create_journals()

    def test_returns_only_published(self):
        published = _make_published_article(self.journal)
        draft = helpers.create_article(self.journal, stage=sm_models.STAGE_UNASSIGNED)

        qs = logic.get_published_articles(self.journal)
        pks = list(qs.values_list("pk", flat=True))

        self.assertIn(published.pk, pks)
        self.assertNotIn(draft.pk, pks)

    def test_excludes_future_dated_articles(self):
        future = _make_published_article(
            self.journal,
            date_published=timezone.now() + timezone.timedelta(days=30),
        )
        qs = logic.get_published_articles(self.journal)
        self.assertNotIn(future.pk, list(qs.values_list("pk", flat=True)))


class RepecViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal, _ = helpers.create_journals()
        plugin_settings.install()
        cls.repec = _make_settings(cls.journal)
        cls.article = _make_published_article(cls.journal, with_author=True)

    def _request(self, journal=None):
        request = RequestFactory().get("/plugins/repec/archive.rdf")
        request.journal = journal or self.journal
        return request

    def test_archive_rdf_returns_200(self):
        response = archive_rdf(self._request())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ReDIF-Archive 1.0", response.content)

    def test_series_rdf_returns_200(self):
        response = series_rdf(self._request())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ReDIF-Series 1.0", response.content)

    def test_papers_index_lists_article(self):
        response = papers_index(self._request())
        self.assertEqual(response.status_code, 200)
        self.assertIn(str(self.article.pk).encode(), response.content)

    def test_article_rdf_returns_200(self):
        response = article_rdf(self._request(), article_id=self.article.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ReDIF-Article 1.0", response.content)

    def test_article_rdf_404_for_unpublished(self):
        draft = helpers.create_article(self.journal, stage=sm_models.STAGE_UNASSIGNED)
        with self.assertRaises(Http404):
            article_rdf(self._request(), article_id=draft.pk)

    def test_disabled_settings_returns_404(self):
        self.repec.enabled = False
        self.repec.save()
        try:
            with self.assertRaises(Http404):
                archive_rdf(self._request())
        finally:
            self.repec.enabled = True
            self.repec.save()

    def test_unconfigured_journal_raises_404(self):
        unconfigured = Journal.objects.exclude(pk=self.journal.pk).first()
        if unconfigured is None:
            return
        with self.assertRaises(Http404):
            archive_rdf(self._request(journal=unconfigured))
