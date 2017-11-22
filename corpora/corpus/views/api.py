from django.utils.translation import ugettext_lazy as _
from corpus.models import QualityControl, Sentence, Recording, Source
from django.db.models import Count, Q, Sum, Case, When, Value, IntegerField
from people.helpers import get_person
from corpus.helpers import get_next_sentence
from rest_framework import viewsets, permissions, pagination
from corpus.serializers import QualityControlSerializer,\
                         SentenceSerializer, \
                         RecordingSerializer, \
                         ListenSerializer, \
                         SourceSerializer
from rest_framework import generics
from django.core.cache import cache
import random
import logging
logger = logging.getLogger('corpora')


class OneHundredResultPagination(pagination.PageNumberPagination):
    page_size = 100


class OneResultPagination(pagination.PageNumberPagination):
    page_size = 1


class TenResultPagination(pagination.PageNumberPagination):
    page_size = 10


class PutOnlyStaffReadPermission(permissions.BasePermission):
    """
    Model permission to only allow staff the ability to
    get and everyone the ability to post/put.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            self.message = _("Only staff can {0}.".format(
                permissions.SAFE_METHODS))
            return request.user.is_staff
        else:
            # Anyone can post
            if request.method in ['PUT', 'POST']:
                return True
            else:
                self.message = _("PONIES Method {0} not allowed.".format(
                    request.method))
                return request.user.is_staff


class QualityControlViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows qc to be viewed or edited.
    """
    queryset = QualityControl.objects.all()
    serializer_class = QualityControlSerializer
    permission_classes = (PutOnlyStaffReadPermission,)
    pagination_class = OneHundredResultPagination


class SourceViewSet(viewsets.ModelViewSet):
    """
    API enpoint that alows sources to be viewed or edited.
    """
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = OneHundredResultPagination


class SentenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows sentences to be viewed or edited.
    """
    queryset = Sentence.objects.all()
    serializer_class = SentenceSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = OneHundredResultPagination


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Model permission to only allow staff the ability to
    edit and post new sentences.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Only admins can edit sentences
        else:
            self.message = _("Only staff can post/put sentences.")
            return request.user.is_staff


class SentencesView(generics.ListCreateAPIView):
    """
    API endpoint that allows sentences to be viewed or edited.
    """

    queryset = Sentence.objects.all()
    serializer_class = SentenceSerializer
    pagination_class = OneHundredResultPagination
    permission_classes = (IsStaffOrReadOnly,)

    def get_queryset(self):
        # person = get_person(self.request)
        queryset = Sentence.objects.all()\
            .order_by('quality_control__approved', 'quality_control__updated')

        q = self.request.query_params.get('recording', 'False')
        if 'True' in q:
            sentence = get_next_sentence(self.request)
            if sentence:
                queryset = queryset.filter(pk=sentence.pk)
            else:
                return []
            return queryset

        else:

            query = self.request.query_params.get('quality_control__approved')
            if query is not None:
                queryset = queryset.annotate(sum_approved=Sum(
                    Case(
                        When(
                            quality_control__approved=True,
                            then=Value(1)),
                        When(
                            quality_control__approved=False,
                            then=Value(0)),
                        default=Value(0),
                        output_field=IntegerField())
                ))

                if eval(query) is True:

                    queryset = queryset.filter(sum_approved__gte=1).order_by('-sum_approved')
                    # queryset = queryset.filter(quality_control__isnull=False)

                # filter by approved = false
                elif eval(query) is False:
                    queryset = queryset.filter(sum_approved__lte=0).order_by('-sum_approved')
                else:
                    raise TypeError

        return queryset


class RecordingPermissions(permissions.BasePermission):
    """
    Model permission to only allow staff the ability to
    get recordings and everyone the ability to post
    recordings and only a person can delete their
    own recording.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            self.message = _("Only staff can read recording lists.")
            return request.user.is_staff
        else:
            # Anyone can post a recording
            if request.method in ['POST', 'PUT']:
                return True
        self.message = _("Reading recording lists not allowed.")
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            self.message = _("Only staff can read recordings.")
            if request.user.is_staff:
                person = get_person(request)
                cache.set('{0}:{0}:listen'.format(person.uuid, obj.id), True, 15)
                return True
        else:
            if request.method in ['PUT']:
                if request.user.is_staff:
                    return True
                person = get_person(request)
                if person is not None:
                    self.message = _("You're not allowed to edit this recording.")
                    return obj.person == person
        self.message = _("Reading recording is not allowed.")
        return False


class RecordingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recordings to be viewed or edited.
    """
    queryset = Recording.objects.all()
    serializer_class = RecordingSerializer
    permission_classes = (RecordingPermissions,)
    pagination_class = TenResultPagination

    def get_queryset(self):
        queryset = Recording.objects.all().order_by('-updated')
        sort_by = self.request.query_params.get('sort_by', '')

        person = get_person(self.request)
        if 'listen' in sort_by.lower():
            queryset = queryset\
                .exclude(quality_control__person=person)
            # .annotate(num_qc=Count('quality_control'))\
            # .order_by('num_qc')

            if len(queryset) > 1:
                i = random.randint(0, len(queryset)-1)
                return [queryset[i]]
            else:
                return queryset

        return queryset


class ListenPermissions(permissions.BasePermission):
    """
    Model permission to only allow anyone to get a recording.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            self.message = _("{0} not allowed with this API\
                             endpoint.".format(request.method))
            return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:

            # We can create a short lived token here to allow someone to access
            # the file URL. We will need to store in the cache framework.
            person = get_person(request)
            key = '{0}:{0}:listen'.format(person.uuid, obj.id)
            cache.set(key, True, 15)
            logger.debug('  CACHE KEY: {0}'.format(key))
            return True
        else:
            self.message = _("{0} not allowed with this API\
                             endpoint.".format(request.method))
            return False


class ListenViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows a single recording to be viewed.
    This api obfuscates extra recording information and only provides the
    recording file link and the id.
    """
    queryset = Recording.objects.all()
    pagination_class = OneResultPagination
    serializer_class = ListenSerializer
    permission_classes = (ListenPermissions,)

    def get_queryset(self):
        person = get_person(self.request)
        queryset = Recording.objects.exclude(quality_control__person=person)
        sort_by = self.request.query_params.get('sort_by', '')

        # Let's just get a random recording.
        '''
        queryset = queryset\
            .annotate(num_qc=Count('quality_control'))\
            .order_by('num_qc')
        '''

        if 'random' in sort_by.lower():
            if len(queryset) > 1:
                i = random.randint(0, len(queryset)-1)
                return [queryset[i]]

        return queryset
