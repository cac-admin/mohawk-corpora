# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import translation
from django.conf import settings
from django.urls import reverse, resolve
from django.utils.translation import ugettext as _
from django.urls import reverse
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.core.exceptions import ObjectDoesNotExist

from django.db.models import Count

from people.helpers import get_current_language,\
    get_num_supported_languages,\
    get_or_create_person,\
    get_unknown_languages,\
    set_current_language_for_person,\
    set_language_cookie

from corpus.helpers import get_next_sentence, get_sentences

from people.models import Person, KnownLanguage, Demographic, Group
from people.serializers import PersonSerializer
from corpus.models import Recording, Sentence

from django.forms import inlineformset_factory
from people.forms import \
    KnownLanguageFormWithPerson,\
    DemographicForm,\
    PersonForm, GroupsForm

from corpora.mixins import SiteInfoMixin

from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.views import APIView


import logging
logger = logging.getLogger('corpora')
# sudo cat /webapp/logs/django.log


class ProfileDetail(SiteInfoMixin, APIView, TemplateView):
    template_name = "people/profile_detail.html"
    renderer_classes = [TemplateHTMLRenderer]
    x_title = _('Profile')
    x_description = _('Edit your profile to help us enhance our corpus.')

    def get(self, request, *args, **kwargs):
        person = get_or_create_person(self.request)
        demographic, created = Demographic.objects.get_or_create(person=person)
        if created:
            demographic.save()

        known_languages = KnownLanguage.objects.filter(person=person)

        if len(known_languages) == 0:
            url = reverse('people:choose_language') + '?next=people:profile'
            return redirect(url)
        elif len(known_languages) >= 1:
            set_current_language_for_person(
                person, known_languages[0].language)
            current_language = known_languages[0]

            if current_language.level_of_proficiency is None:
                url = reverse('people:choose_language') + '?next=people:profile'
                return redirect(url)

        num_recordings = Recording.objects.filter(person=person).count()

        if num_recordings == 0 and person.just_signed_up:
            url = reverse('corpus:record')  # onboard?
            return redirect(url)

        return super(ProfileDetail, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProfileDetail, self).get_context_data(**kwargs)

        person = get_or_create_person(self.request)
        serializer = PersonSerializer(person)
        context['person'] = person
        context['serializer'] = serializer

        context['demographic_form'] = DemographicForm(instance=person.demographic)
        email = None
        username = None

        if person.user:
            if person.user.email:
                email = person.user.email
            username = person.user.username
        else:
            if person.profile_email:
                email = person.profile_email
            else:
                email = ''
            if person.username:
                username = person.username
            else:
                username = ''

        context['person_form'] = PersonForm(
            instance=person,
            initial={'email': email, 'username': username})

        context['groups_form'] = GroupsForm(instance=person,
                                            request=self.request)

        known_languages = KnownLanguage.objects.filter(person=person).count()
        if known_languages > 0:
            extra = known_languages
        else:
            extra = 1

        KnownLanguageFormset = inlineformset_factory(
            Person,
            KnownLanguage,
            form=KnownLanguageFormWithPerson,
            fields=('language', 'level_of_proficiency', 'person', 'accent', 'dialect'),
            max_num=get_num_supported_languages(), extra=extra)

        kl_formset = KnownLanguageFormset(
            instance=person,
            form_kwargs={'person': person})

        context['known_language_form'] = kl_formset
        context['known_languages'] = known_languages
        context['show_stats'] = True

        return context


def person(request, uuid):
    # # from django.utils.translation import activate
    # # activate('mi')
    lang = get_current_language(request)
    sentence = get_next_sentence(request)

    logger.debug('Language Cookie Is: {0}'.format(lang))

    output = _('Today is %(month)s %(day)s.') % {'month': 10, 'day': 10}

    return render(request, 'people/person.html', {'language':lang, 'output':output, 'sentence': sentence})
    return render(request, 'people/person.html')


def choose_language(request):
    person = get_or_create_person(request)
    if not person:
        return redirect(reverse('account_login'))

    current_language = get_current_language(request)
    if current_language:
        set_current_language_for_person(person, current_language)    

    next_page = request.GET.get('next',None)

    known_languages = KnownLanguage.objects.filter(person=person).count()
    if known_languages >0:
        extra = known_languages
    else:
        extra = 1

    unknown = get_unknown_languages(person)
    KnownLanguageFormset = inlineformset_factory(
        Person,
        KnownLanguage,
        form=KnownLanguageFormWithPerson,
        fields=('language', 'level_of_proficiency', 'person', 'accent', 'dialect'),
        max_num=get_num_supported_languages(), extra=extra,)
    # formset  = KnownLanguageFormset(form_kwargs={'person':person})
    # KnownLanguageFormsetWithPerson = inlineformset_factory(Person, KnownLanguage, form=form,  fields=('language','level_of_proficiency','person'), max_num=get_num_supported_languages(), extra=known_languages+1)

    formset = KnownLanguageFormset(
            instance=person,
            form_kwargs={'person': person, 'require_proficiency': True})

    if request.method == 'POST':

        # Upon first post to the person choosing their language
        # We can ensure that the user just signed up
        person.just_signed_up = False
        person.save()

        formset = KnownLanguageFormset(
                    request.POST, request.FILES,
                    instance=person,
                    form_kwargs={
                        'person': person,
                        'require_proficiency': True})
        if formset.has_changed():
            if formset.is_valid():
                instances = formset.save()

                current_language = get_current_language(request)
                if not current_language:
                    for instance in instances:
                        if instance.active:
                            current_language = obj.language
                if not current_language:
                    current_language = translation.get_language()

                try:
                    set_current_language_for_person(person, current_language)
                except:
                    logger.debug("We may be trying to set a language when knownlanguage doens't exist")              

                if next_page:
                    response = redirect(reverse(next_page))
                else:
                    response = redirect(reverse('people:choose_language'))

                response = set_language_cookie(response, current_language)

                return response

        else:
            if formset.is_valid():
                if next_page:
                    return redirect(reverse(next_page))
                # else:
                #     return redirect(reverse('people:choose_language'))
            # formset = KnownLanguageFormsetWithPerson(instance=person)

    response = render(
        request,
        'people/choose_language.html',
        {
            'known_language_form': formset,
            'known_languages': known_languages,
            'unknown_languages': unknown,
            'just_signup_track': person.just_signed_up,
        }
    )

    current_language = get_current_language(request)
    if current_language:
        set_current_language_for_person(person, current_language)
        response = set_language_cookie(response, current_language)
    else:
        logger.debug('no current language')
    return response


def set_language(request):
    logger.debug('SET LANGAUGE')

    url = '/'+'/'.join(request.META['HTTP_REFERER'].split('/')[3:])
    match = resolve(url)
    logger.debug('MATCH: {0}'.format(match))
    if match:
        url = '{0}:{1}'.format(match.namespace, match.url_name)
    else:
        url = 'people:choose_language'

    if request.method == 'POST':

        if request.POST.get('language', '') != '':
            user_language = request.POST.get('language', '')
            person = get_or_create_person(request)
            set_current_language_for_person(person, user_language)
            translation.activate(user_language)
            request.session[translation.LANGUAGE_SESSION_KEY] = user_language

            response = redirect(reverse(url))  # render(request,  'people/set_language.html')
            response = set_language_cookie(response, user_language)
            logger.debug('RESPONSE: {0}'.format(response))
            return response

    else:
        return redirect(reverse(url))


def create_demographics(request):
    """
    THIS VIEW SHOULD NO LONGER BE USED AS THE PROFILE VIEW HANDLES
    AJAX EDITING OF DEMOGRAPHIC DATA
    """
    person = get_or_create_person(request)

    if request.method == "POST":
        form = DemographicForm(request.POST)

        if form.is_valid():
            #  Chek if demographic data already there if so then replace.
            demographic = form.save(commit=False)
            instance, created = Demographic.objects.get_or_create(person=person)
            if created:
                demographic.person = person
                demographic.save()
            else:
                instance.sex = demographic.sex
                instance.age = demographic.age
                for tribe in instance.tribe.all():
                    instance.tribe.remove(tribe)
                demographic.pk = instance.pk

                for tribe in demographic.tribe.all():
                    instance.tribe.add(tribe)
                instance.save()

            return redirect(reverse('people:profile'))

    else:
        try:
            instance = Demographic.objects.get(person=person)
            if instance.sex is None or instance.age is None:
                form = DemographicForm(instance=instance)
            else:
                return redirect(reverse('people:profile'))
        except ObjectDoesNotExist:
            form = DemographicForm()

    return render(request, 'people/demographics.html', {'form': form})


def create_user(request):
    return render(request, 'people/create_account.html')


class Competition(SiteInfoMixin, ListView):
    model = Group
    template_name = 'people/competition/competition.html'
    paginate_by = 50
    context_object_name = 'groups'
    x_title = _('Competition')
    x_description = \
        _("Compete with groups and others to win amaing prizes.")

    def get_queryset(self):
        return Group.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = \
            super(Competition, self).get_context_data(**kwargs)

        # language = get_current_language(self.request)

        groups = Group.objects.all().order_by('name').annotate(
            size=Count('person'))
        qualified = groups.filter(size__gte=7)
        not_qualified = groups.exclude(size__gte=7)

        context['qualified'] = qualified
        context['not_qualified'] = not_qualified
        # for group in groups:

        return context
