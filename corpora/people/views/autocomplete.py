from dal import autocomplete

from people.models import Tribe


class TribeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !

        qs = Tribe.objects.all().order_by('name')

        # TO DO: use somethign like solr and index while ignoring diacritics
        if self.q:
            qs = qs.filter(name__icontains=self.q).order_by('name')

        return qs
