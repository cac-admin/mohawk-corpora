from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url, include

from transcription.views.views import TranscribeView

urlpatterns = [

    url(_(r'^transcribe/'), TranscribeView.as_view(), name='transcribe'),

]
