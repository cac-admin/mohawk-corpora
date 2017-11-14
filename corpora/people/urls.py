# -*- coding: utf-8 -*-
from django.conf.urls import url, include
from people.views import views, autocomplete

urlpatterns = [
    url(r'^profile2', views.ProfileDetail.as_view(), name='profile2'),
    url(r'^profile', views.profile, name='profile'),
    url(r'^choose_language', views.choose_language, name='choose_language'),
    url(r'^set_language', views.set_language, name='set_language'),
    # url(r'^(?P<uuid>[\w-]+)', views.person, name='person'),
    url(r'^demographics', views.create_demographics, name='demographics'),
    url(r'^create_account', views.create_user, name='create_user'),

    # autocomplete
    url(
        r'^tribe-autocomplete/$',
        autocomplete.TribeAutocomplete.as_view(),
        name='tribe-autocomplete',
    ),
]
