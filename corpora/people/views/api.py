from django.utils.translation import ugettext_lazy as _
from people.models import Person, Tribe, Demographic, KnownLanguage
from people.helpers import get_person
from rest_framework import viewsets, permissions
from people.serializers import PersonSerializer,\
                         TribeSerializer, \
                         DemographicSerializer,\
                         KnownLanguageSerializer


class StaffOnlyPermissions(permissions.BasePermission):
    """
    Model permission to only allow staff to view/edit model & objects.
    """

    def has_permission(self, request, view):
        return request.user.is_staff and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff and request.user.is_authenticated


class PersonInfoPermissions(permissions.BasePermission):
    """
    Only an authenticated person can edit his/her own info. This
    involved all info including related models; therefore this persmission
    must work accross all the related hyperlink viewsets.
    """

    def has_permission(self, request, view):
        if request.user.is_staff and request.user.is_authenticated:
            self.message = _("Only staff can view this information.")
            return True

        self.message = _("You're not allowed to view this information.")
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff and request.user.is_authenticated:
            # Authenticated staff have full access
            return True
        else:
            person = get_person(request)
            if person == obj.person:
                # Only a person can view/edit his/her own data
                if request.method in permissions.SAFE_METHODS:
                    # No authentication needed to view data
                    return True
                elif request.method in ['POST', 'PUT']:
                    # Authentication needed to edit data
                    self.message = _("You must sign in to edit your info.")
                    return request.user.is_authenticated
            else:
                self.message_("You're not allowed to view this information.")
                return False
        return False


class PersonViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Person to be viewed or edited.
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = (PersonInfoPermissions,)


class TribeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows sentences to be viewed or edited.
    """

    queryset = Tribe.objects.all()
    serializer_class = TribeSerializer
    permission_classes = (PersonInfoPermissions,)


class DemographicViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recordings to be viewed or edited.
    """
    queryset = Demographic.objects.all()
    serializer_class = DemographicSerializer
    permission_classes = (PersonInfoPermissions,)


class KnownLanguageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recordings to be viewed or edited.
    """
    queryset = KnownLanguage.objects.all()
    serializer_class = KnownLanguageSerializer
    permission_classes = (PersonInfoPermissions,)
