from people.models import Person, Tribe, Demographic, KnownLanguage
from rest_framework import viewsets
from people.serializers import PersonSerializer,\
                         TribeSerializer, \
                         DemographicSerializer,\
                         KnownLanguageSerializer


class PersonViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows qc to be viewed or edited.
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class TribeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows sentences to be viewed or edited.
    """
    queryset = Tribe.objects.all()
    serializer_class = TribeSerializer


class DemographicViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recordings to be viewed or edited.
    """
    queryset = Demographic.objects.all()
    serializer_class = DemographicSerializer


class KnownLanguageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recordings to be viewed or edited.
    """
    queryset = KnownLanguage.objects.all()
    serializer_class = KnownLanguageSerializer
