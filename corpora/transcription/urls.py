from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url, include

from transcription.views.views import \
    TranscribeView, AudioFileTranscriptionView, AudioFileTranscriptionListView

urlpatterns = [


    url(
        _(r'^transcriptions/(?P<pk>[0-9]+)'),
        AudioFileTranscriptionView.as_view(),
        name='file_transcribe'),

    url(
        _(r'^transcriptions/'),
        AudioFileTranscriptionListView.as_view(),
        name='transcription_list'),


    url(_(r'^transcribe/'), TranscribeView.as_view(), name='transcribe'),

]
