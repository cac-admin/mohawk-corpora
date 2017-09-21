from corpus.models import QualityControl, Sentence, Recording
from rest_framework import viewsets, permissions, pagination
from corpus.serializers import QualityControlSerializer,\
                         SentenceSerializer, \
                         RecordingSerializer
from rest_framework import generics

from rest_framework import generics


class QualityControlViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows qc to be viewed or edited.
    """
    queryset = QualityControl.objects.all()
    serializer_class = QualityControlSerializer
    permission_classes = (permissions.AllowAny,)


class SentenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows sentences to be viewed or edited.
    """
    queryset = Sentence.objects.all()
    serializer_class = SentenceSerializer
    permission_classes = (permissions.AllowAny,)


class OneResultPagination(pagination.PageNumberPagination):
    page_size = 100


class SentencesView(generics.ListCreateAPIView):
    serializer_class = SentenceSerializer
    pagination_class = OneResultPagination
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = Sentence.objects.all()\
            .order_by('quality_control__approved', 'quality_control__updated')
        qc = self.request.query_params.get('quality_control__approved', None)
        if qc is not None:
            queryset = queryset.filter(quality_control__approved=qc)
        return queryset


class RecordingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recordings to be viewed or edited.
    """
    queryset = Recording.objects.all()
    serializer_class = RecordingSerializer
