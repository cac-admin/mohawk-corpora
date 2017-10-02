from django.conf.urls import url, include
from corpus.views import views
from corpus.views.views import SentenceListView, StatsView
from django.views.decorators.cache import cache_page

urlpatterns = [
    url(r'^record/', views.record, name='record'),
    url(r'^submit_recording/',
        views.submit_recording,
        name='submit_recording'),
    url(r'^failed_submit/', views.failed_submit, name='failed_submit'),
    url(r'^sentences/', SentenceListView.as_view(), name='sentence-list'),

    url(r'^stats/', cache_page(60*60*1)(StatsView.as_view()), name='stats'),

    url(r'^recording-file/(?P<pk>[\d]+)/$',
        views.RecordingFileView.as_view(),
        name='recording_file'),
]
