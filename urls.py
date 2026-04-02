from django.urls import re_path

from plugins.repec import views

urlpatterns = [
    re_path(r"^archive\.rdf$", views.archive_rdf, name="repec_archive"),
    re_path(r"^series\.rdf$", views.series_rdf, name="repec_series"),
    re_path(r"^papers/$", views.papers_index, name="repec_papers_index"),
    re_path(r"^papers/(?P<article_id>\d+)\.rdf$", views.article_rdf, name="repec_article"),
    re_path(r"^admin/$", views.repec_admin, name="repec_admin"),
]
