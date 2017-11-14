from people.models import Person, Tribe, Demographic, KnownLanguage
from corpora.serializers import UserSerializer
from rest_framework import serializers
from dal import autocomplete

import logging
logger = logging.getLogger('corpora')


class TribeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tribe
        fields = ('name', 'id')


class DemographicSerializer(serializers.ModelSerializer):
    tribe = TribeSerializer(
        many=True,
        )

    class Meta:
        model = Demographic
        fields = ('age', 'sex', 'tribe', 'id')


class KnownLanguageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = KnownLanguage
        fields = ('language', 'level_of_proficiency', 'active', 'accent', 'dialect', 'id')


class PersonSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer(partial=True, required=False)
    demographic = DemographicSerializer(partial=True, required=False)
    known_languages = KnownLanguageSerializer(many=True, read_only=True)

    class Meta:
        model = Person
        fields = ('full_name', 'uuid', 'user', 'demographic', 'known_languages', 'id')

    def update(self, instance, validated_data):
        instance.full_name = validated_data['full_name']
        # instance.uuid = validated_data['uuid']

        logger.debug(instance)
        logger.debug(validated_data)

        demographic = validated_data['demographic']

        demo = Demographic.objects.get(person=instance)

        demo.sex = demographic['sex']
        demo.age = demographic['age']

        user = instance.user
        user.email = validated_data['user']['email']

        # for tribe in demographic['tribe']:
        #     t = Tribe.objects.get(pk=tribe['pk'])
        #     demo.tribe.add(t)

        instance.demographic = demo
        instance.user = user

        instance.save()
        instance.user.save()
        instance.demographic.save()

        return instance
