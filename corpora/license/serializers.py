from license.models import \
    AcceptLicense

from rest_framework import serializers

from license.models import License, AcceptLicense
from people.helpers import get_person
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

import logging
logger = logging.getLogger('corpora')


class AcceptLicenseSerializer(serializers.HyperlinkedModelSerializer):
    person = serializers.PrimaryKeyRelatedField(read_only=True)
    license = serializers.PrimaryKeyRelatedField(read_only=True, many=True)

    class Meta:
        model = AcceptLicense
        fields = ('person', 'license', 'pk')

    def create(self, validated_data):

        person = get_person(self.context['request'])

        try:
            current_license = License.objects\
                .get(sitelicense__site=settings.SITE_ID)
        except ObjectDoesNotExist:
            return None

        accept_license, created = \
            AcceptLicense.objects.get_or_create(person=person)

        accept_license.license.add(current_license)
        accept_license.save()
        return accept_license
