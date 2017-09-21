from django.conf.urls import url, include
from corpus.views import views
from corpus.views.views import SentenceListView

from corpus.views.views import SentenceListView

urlpatterns = [
    url(r'^record/', views.record, name='record'),
    url(r'^submit_recording/', views.submit_recording, name='submit_recording'),
    url(r'^failed_submit/', views.failed_submit, name='failed_submit'),
    url(r'^sentences/', SentenceListView.as_view(), name='sentence-list'),
]
