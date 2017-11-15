from people.models import Person, Tribe, Demographic, KnownLanguage
from corpora.serializers import UserSerializer
from rest_framework import serializers
from dal import autocomplete

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

        demographic = validated_data['demographic']

        demo, created = Demographic.objects.get_or_create(person=instance)

        try:
            demo.sex = demographic['sex']
        except KeyError:
            demo.sex = None

        try:
            demo.age = demographic['age']
        except KeyError:
            demo.age = None

        user = instance.user
        try:
            user.email = validated_data['user']['email']
            instance.user = user
            instance.user.save()
        except KeyError:
            pass

        logger.debug(demographic)
        # remove all current relations
        for tribe in demo.tribe.all():
            demo.tribe.remove(tribe)

        for tribe in demographic['tribe']:
            logger.debug(tribe)
            t = Tribe.objects.get(name=tribe['name'])
            demo.tribe.add(t)

        instance.demographic = demo
        instance.save()
        instance.demographic.save()

        return instance
