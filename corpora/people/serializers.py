from .models import Person, Tribe, Demographic, KnownLanguage
from rest_framework import serializers


class PersonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Person
        fields = ('user', 'full_name')


class TribeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tribe
        fields = ('name')


class DemographicSerializer(serializers.ModelSerializer):
    person = serializers.PrimaryKeyRelatedField(
        many=False,
        read_only=True
    )

    class Meta:
        model = Demographic
        fields = ('person', 'birthday', 'sex')


class KnownLanguageSerializer(serializers.HyperlinkedModelSerializer):
    person = serializers.PrimaryKeyRelatedField(
        many=False,
        read_only=True
    )

    class Meta:
        model = KnownLanguage
        fields = ('language', 'level_of_proficiency', 'person', 'active')
