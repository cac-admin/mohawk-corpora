from people.models import \
    Person, Tribe, Demographic, KnownLanguage, Group
from django.contrib.auth.models import User

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
    groups = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False, queryset=Group.objects.all())

    class Meta:
        model = Person
        fields = ('full_name', 'username', 'uuid', 'user',
                  'demographic', 'known_languages', 'id',
                  'profile_email', 'groups', 'receive_weekly_updates',
                  'leaderboard')
        extra_kwargs = {"username": {"error_messages": {"required": "Give yourself a username"}}}
        validators = []

    def validate_username(self, validated_data):
        logger.debug('\n\n validating username!\n\n')
        person = self.instance
        current_user = person.user
        new_username = validated_data
        if new_username:
            if current_user is None:
                # Check if username already exists
                try:
                    user = User.objects.get(username=new_username)
                    raise serializers.ValidationError('Username already exists.')
                except ObjectDoesNotExist:
                    pass

            elif new_username != current_user.username:
                # Check user with uname doesn't already exist
                if User.objects.filter(username=new_username).exists():
                    # Raise validation error 
                    raise serializers.ValidationError('Username already exists.')
                else:
                    # Everything is ka pai
                    pass

        return validated_data

    def update(self, instance, validated_data):
        instance.full_name = validated_data['full_name']

        instance.receive_weekly_updates = \
            validated_data['receive_weekly_updates']
        instance.leaderboard = \
            validated_data['leaderboard']

        logger.debug('executing udpate on person model')
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
            new_username = validated_data['username']
            new_email = validated_data['user']['email']
            if instance.user:
                instance.user.username = new_username
                instance.user.email = new_email
                instance.user.save()
            else:
                user, created = User.objects.get_or_create(
                    username=new_username,
                    email=new_email)
                user.save()
                instance.user = user
        elif 'username' in validated_data.keys():
            new_username = validated_data['username']
            user, created = User.objects.get_or_create(
                    username=new_username)
            user.save()
            instance.user = user

        if 'profile_email' in validated_data.keys():
            instance.profile_email = validated_data['profile_email']
            if instance.user:
                if instance.user.email =='':
                    instance.user.email = instance.profile_email
                    instance.user.save()


        if 'username' in validated_data.keys():
            instance.username = validated_data['username']

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

        # TODO not sure if this is the correct approach?
        instance.groups.set(validated_data['groups'])

        return instance
