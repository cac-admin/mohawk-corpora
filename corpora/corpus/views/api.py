from django.utils.translation import ugettext_lazy as _
from corpus.models import QualityControl, Sentence, Recording
from django.db.models import Count, Q, Sum, Case, When, Value, IntegerField
from people.helpers import get_person
from rest_framework import viewsets, permissions, pagination
from corpus.serializers import QualityControlSerializer,\
                         SentenceSerializer, \
                         RecordingSerializer
from rest_framework import generics


class PutOnlyStaffReadPermission(permissions.BasePermission):
    """
    Model permission to only allow staff the ability to
    get and everyone the ability to post/put.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            self.message = _("Only staff can {0}.".format(permissions.SAFE_METHODS))
            return request.user.is_staff
        else:
            # Anyone can post
            if request.method in ['PUT', 'POST']:
                return True
            else:
                self.message = _("PONIES Method {0} not allowed.".format(request.method))
                return request.user.is_staff


class QualityControlViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows qc to be viewed or edited.
    """
    queryset = QualityControl.objects.all()
    serializer_class = QualityControlSerializer
    permission_classes = (PutOnlyStaffReadPermission,)


class SentenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows sentences to be viewed or edited.
    """
    queryset = Sentence.objects.all()
    serializer_class = SentenceSerializer
    permission_classes = (permissions.IsAdminUser,)


class OneResultPagination(pagination.PageNumberPagination):
    page_size = 100


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
    serializer_class = SentenceSerializer
    pagination_class = OneResultPagination
    permission_classes = (IsStaffOrReadOnly,)

    def get_queryset(self):
        # person = get_person(self.request)
        queryset = Sentence.objects.all()\
            .order_by('quality_control__approved', 'quality_control__updated')

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
            return request.user.is_staff
        else:
            if request.method in ['PUT']:
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

    def get_queryset(self):
        queryset = Recording.objects.all().order_by('-updated')
        sort_by = self.request.query_params.get('sort_by', None)

        if sort_by is 'listen':
            queryset = queryset\
                .annotate(num_qc=Count('quality_control'))\
                .order_by('num_qc')

        return queryset
