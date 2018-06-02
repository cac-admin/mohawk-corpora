from django.utils.translation import ugettext_lazy as _
from transcription.models import Transcription
from transcription.serializers import TranscriptionSerializer

from rest_framework import viewsets, permissions, pagination

from people.helpers import get_person
from django.core.cache import cache

import logging
logger = logging.getLogger('corpora')


class TranscriptionPermissions(permissions.BasePermission):
    """
    Model permission to only allow staff the ability to
    get transcriptions and everyone the ability to post
    audio for transcriptions and only a person can access
    their own transcriptions..
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            self.message = _("Only staff can read transcription lists.")
            return request.user.is_staff
        else:
            # Anyone can post a transcription
            if request.method in ['POST', 'PUT']:
                return True
        self.message = _("Reading transcription lists not allowed.")
        return False

    def has_object_permission(self, request, view, obj):
        person = get_person(request)

        if request.method in permissions.SAFE_METHODS:
            self.message = _("Only staff can read transcriptions.")
            if request.user.is_staff:
                person = get_person(request)
                cache.set(
                    '{0}:{0}:listen'.format(person.uuid, obj.id), True, 15)
                return True
            elif person is not None:
                # Allow people to get their own transcriptions.
                return person == obj.person
        else:
            if request.method in ['PUT']:
                if request.user.is_staff:
                    return True
                if person is not None:
                    self.message = _(
                        "You're not allowed to edit this transcription.")
                    return obj.person == person
        self.message = _("Reading recording is not allowed.")
        return False


class TranscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows transcriptions to be viewed or edited.

    This api provides acces to a audio_file_url field. This allows the retrival
    of an audio file in the m4a container with the aac audio codec. To retrieve
    an audio file in the wave format at 16kHz and 16bits, append the query
    ?format=wav to the url given by the audio_file_url field.
    """
    queryset = Transcription.objects.all()
    serializer_class = TranscriptionSerializer
    # permission_classes = (RecordingPermissions,)
    # pagination_class = TenResultPagination
