# -*- coding: utf-8 -*-
from django.conf.urls import url, include
from corpora.views import api as corpora_api
from corpus.views import api as corpus_api
from people.views import api as people_api
from rest_framework import routers
from rest_framework.authtoken import views

router = routers.DefaultRouter()
# router.register(r'groups', corpora_api.GroupViewSet)
# router.register(r'users', corpora_api.UserViewSet)

router.register(r'qualitycontrol', corpus_api.QualityControlViewSet)
router.register(r'sentences', corpus_api.SentenceViewSet)
router.register(r'recordings', corpus_api.RecordingViewSet)
router.register(r'listen', corpus_api.ListenViewSet)
router.register(r'sources', corpus_api.SourceViewSet)

# router.register(r'tribes', people_api.TribeViewSet)
# router.register(r'demographics', people_api.DemographicViewSet)
# router.register(r'persons', people_api.PersonViewSet)
# router.register(r'knownlangauges', people_api.KnownLanguageViewSet)

urlpatterns = [

    url(r'^api/sentences/$', corpus_api.SentencesView.as_view()),
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include(
        'rest_framework.urls',
        namespace='rest_framework')),

]

urlpatterns += [
    url(r'^api-token-auth/', views.obtain_auth_token),
]
