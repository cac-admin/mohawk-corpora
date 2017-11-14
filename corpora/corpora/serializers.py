from django.contrib.auth.models import User, Group
from rest_framework import serializers


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('name')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    # groups = GroupSerializer(many=True)

    class Meta:
        model = User
        fields = ('email', 'pk')
