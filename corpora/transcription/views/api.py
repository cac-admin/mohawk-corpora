from django.utils.translation import ugettext_lazy as _
from transcription.models import \
    Transcription, TranscriptionSegment, AudioFileTranscription
from transcription.serializers import \
    TranscriptionSerializer,\
    TranscriptionSegmentSerializer,\
    AudioFileTranscriptionSerializer

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
            # TODO: Allow people to get a list of THEIR transcriptions.
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
                    '{0}:{0}:listen'.format(person.uuid, obj.recording.id), True, 15)
                return True
            elif person is not None:
                # Allow people to get their own transcriptions.
                return person == obj.recording.person
        else:
            if request.method in ['PUT']:
                if request.user.is_staff:
                    return True
                if person is not None:
                    self.message = _(
                        "You're not allowed to edit this transcription.")
                    return person == obj.recording.person
        self.message = _("Reading transcriptions is not allowed.")
        return False


class TranscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows transcriptions to be viewed or edited.

    This api provides acces to a audio_file_url field. This allows the retrival
    of an audio file in the m4a container with the aac audio codec. To retrieve
    an audio file in the wave format at 16kHz and 16bits, append the query
    ?format=wav to the url given by the audio_file_url field.
    """

    # TODO: Allow someone to get a list of ALL of their transcriptions.

    queryset = Transcription.objects.all()
    serializer_class = TranscriptionSerializer
    permission_classes = (TranscriptionPermissions,)
    # pagination_class = TenResultPagination


class TranscriptionSegmentPermissions(permissions.BasePermission):
    """
    API permissions for Transcription Segments model.
    Only staff get get entire lists from TS.
    Anyone can PUT a TS object - but only if they OWN the object?
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            # TODO: Allow people to get a list of THEIR transcriptions.
            self.message = _("Only staff can read transcription lists.")
            return request.user.is_staff
        else:
            # Anyone can post a transcription
            if request.method in ['PUT']:
                return True
        self.message = _("Reading transcription lists not allowed.")
        return False

    def has_object_permission(self, request, view, obj):
        person = get_person(request)

        if request.method in permissions.SAFE_METHODS:
            if request.user.is_staff:
                return True
            elif person is not None:
                # Allow people to get their own TS objects.
                return person == obj.recording.person
        else:
            if request.method in ['PUT']:
                if request.user.is_staff:
                    return True
                if person is not None:
                    return person == obj.recording.person
        return False


class TranscriptionSegmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transcription Segments to be viewed or edited.
    """

    queryset = TranscriptionSegment.objects.all()
    serializer_class = TranscriptionSegmentSerializer
    permission_classes = (TranscriptionSegmentPermissions,)
    # pagination_class = TenResultPagination


class AudioFileTranscriptionPermissions(permissions.BasePermission):
    """
    API permissions for Audio File Transcriptions model.
    """

    def has_permission(self, request, view):
        person = get_person(request)
        if request.method in permissions.SAFE_METHODS:

            if request.user.is_staff:
                return True
            elif person is not None:
                return request.user.is_authenticated
            return False
            # return request.user.is_staff
        else:
            # Anyone can post a transcription
            if request.method in ['POST', 'PUT', 'DELETE']:
                return request.user.is_authenticated

        return False

    def has_object_permission(self, request, view, obj):
        person = get_person(request)

        if request.method in permissions.SAFE_METHODS:
            if request.user.is_staff:
                return True
            elif person is not None:
                # Allow people to get their own TS objects.
                return person == obj.uploaded_by
        else:
            if request.method in ['PUT', 'DELETE']:
                if request.user.is_staff:
                    return True
                if person is not None:
                    return person == obj.uploaded_by
        return False


class AudioFileTranscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Audio File Transcriptions (AFT) to be viewed or edited.

    retrieve:
    Return an AFT object.

    list:
    Return a list of all AFT objects.

    create:
    Create an AFT.


    """

    queryset = AudioFileTranscription.objects.all()
    serializer_class = AudioFileTranscriptionSerializer
    permission_classes = (AudioFileTranscriptionPermissions,)

    def get_queryset(self):
        person = get_person(self.request)
        queryset = AudioFileTranscription.objects\
            .filter(uploaded_by=person)

        return queryset
