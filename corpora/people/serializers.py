from people.models import \
    Person, Tribe, Demographic, KnownLanguage

from corpora.serializers import UserSerializer
from rest_framework import serializers
from dal import autocomplete

from django.core.exceptions import ObjectDoesNotExist

import logging
logger = logging.getLogger('corpora')


class TribeSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for Tribe model. Note that we only intend to use this serializer
    as READ-ONLY because we prescribe what Tribes are available in the
    database. We've added a custom validate_name validator because we're
    unable to PUT/POST a demographic objects because this seriliaxer
    attempts to create an object with the name that already exists. I
    think the proper implementation would be to modify the create and
    update methods on this serializer.
    """

    name = serializers.CharField(max_length=200)

    def validate_name(self, value):
        return value

    class Meta:
        model = Tribe
        fields = ('name', 'id')


class DemographicSerializer(serializers.ModelSerializer):
    tribe = TribeSerializer(many=True, partial=True, required=False)

    def validate_tribe(self, value):
        logger.debug(value)
        return value

    class Meta:
        model = Demographic
        fields = ('age', 'gender', 'tribe', 'id')


class KnownLanguageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = KnownLanguage
        fields = ('language', 'level_of_proficiency', 'active', 'dialect', 'id')


class PersonSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer(partial=True, required=False)
    demographic = DemographicSerializer(partial=True, required=False)
    known_languages = KnownLanguageSerializer(many=True, required=False, partial=True)

    class Meta:
        model = Person
        fields = ('full_name', 'uuid', 'user',
                  'demographic', 'known_languages', 'id',
                  'profile_email')

    def update(self, instance, validated_data):
        instance.full_name = validated_data['full_name']
        # instance.uuid = validated_data['uuid']

        demographic = validated_data['demographic']

        demo, created = Demographic.objects.get_or_create(person=instance)

        try:
            demo.gender = demographic['gender']
        except KeyError:
            demo.gender = None

        try:
            demo.age = demographic['age']
        except KeyError:
            demo.age = None

        if 'user' in validated_data.keys():
            instance.user.email = validated_data['user']['email']
            instance.user.save()
        elif validated_data['profile_email']:
            instance.profile_email = validated_data['profile_email']

        logger.debug(demographic)
        # remove all current relations
        for tribe in demo.tribe.all():
            demo.tribe.remove(tribe)

        for tribe in demographic['tribe']:
            logger.debug(tribe)
            t = Tribe.objects.get(name=tribe['name'])
            demo.tribe.add(t)

        validated_languages = validated_data['known_languages']
        # logger.debug(validated_languages)
        # logger.debug(validated_data)
        for vl in validated_languages:
            logger.debug(vl)
            try:
                kl = KnownLanguage.objects.get(
                    person=instance,
                    language=vl['language']
                )

                kl.level_of_proficiency = vl['level_of_proficiency']
                # kl.accent = vl['accent']
                kl.dialect = vl['dialect']

            except ObjectDoesNotExist:
                kl = KnownLanguage.objects.create(
                    person=instance,
                    level_of_proficiency=vl['level_of_proficiency'],
                    dialect=vl['dialect'],
                    # accent=vl['accent'],
                    language=vl['language']
                )
            kl.save()

        instance.demographic = demo
        instance.save()
        instance.demographic.save()

        return instance
