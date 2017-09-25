from django.utils.translation import ugettext_lazy as _
from corpus.models import QualityControl, Sentence, Recording
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
            if request.method in ['PUT']:
                return True
            else:
                self.message = _("POST not allowed.")
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
        queryset = Sentence.objects.all()\
            .order_by('quality_control__approved', 'quality_control__updated')
        qc = self.request.query_params.get('quality_control__approved', None)
        if qc is not None:
            queryset = queryset.filter(quality_control__approved=qc)
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
    queryset = Recording.objects.all().order_by('-updated')
    serializer_class = RecordingSerializer
    permission_classes = (RecordingPermissions,)
