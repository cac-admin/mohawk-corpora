from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url, include

from transcription.views.views import \
    TranscribeView, AudioFileTranscriptionView, \
    AudioFileTranscriptionListView, DashboardView, \
    ReviewView, TranscribeView2

urlpatterns = [

    url(
        _(r'^dashboard/'),
        DashboardView.as_view(),
        name='dashboard'),

    url(
        _(r'^transcriptions/(?P<pk>[0-9]+)'),
        AudioFileTranscriptionView.as_view(),
        name='file_transcribe'),

    url(
        _(r'^transcriptions/'),
        AudioFileTranscriptionListView.as_view(),
        name='transcription_list'),


    url(
        _(r'^speak/'),
        TranscribeView.as_view(),
        name='speak'),


    url(
        _(r'^speak2/'),
        TranscribeView2.as_view(),
        name='speak2'),


    url(
        _(r'^review/'),
        ReviewView.as_view(),
        name='review'),

]
