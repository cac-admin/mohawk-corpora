# -*- coding: utf-8 -*-
from django.conf.urls import url, include
from people.views import views, autocomplete, stats_views

urlpatterns = [
    url(r'^profile', views.ProfileDetail.as_view(), name='profile'),
    # url(r'^profile', views.profile, name='profile'),
    url(r'^choose_language', views.choose_language, name='choose_language'),
    url(r'^set_language', views.set_language, name='set_language'),
    # url(r'^(?P<uuid>[\w-]+)', views.person, name='person'),
    url(r'^demographics', views.create_demographics, name='demographics'),
    url(r'^create_account', views.create_user, name='create_user'),

    url(r'^recording_stats',
        stats_views.PersonRecordingStatsView.as_view(),
        name='person_stats'),

    url(r'^stats/$',
        stats_views.PeopleRecordingStatsView.as_view(),
        name='people_stats'),

    url(r'^emails/$',
        stats_views.PeopleEmailsView.as_view(),
        name='people_stats'),

    # autocomplete
    url(
        r'^tribe-autocomplete/$',
        autocomplete.TribeAutocomplete.as_view(),
        name='tribe-autocomplete',
    ),
    url(
        r'^groups-autocomplete/$',
        autocomplete.GroupAutocomplete.as_view(),
        name='groups-autocomplete',
    ),
]
