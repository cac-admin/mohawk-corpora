# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import translation
from django.conf import settings
from django.urls import reverse, resolve
from django.utils.translation import ugettext as _
from django.urls import reverse
from django.views.generic.base import TemplateView
from django.core.exceptions import ObjectDoesNotExist

from people.helpers import get_current_language,\
    get_num_supported_languages,\
    get_or_create_person,\
    get_unknown_languages,\
    set_current_language_for_person,\
    set_language_cookie

from corpus.helpers import get_next_sentence, get_sentences

from people.models import Person, KnownLanguage, Demographic
from people.serializers import PersonSerializer
from corpus.models import Recording, Sentence

from django.forms import inlineformset_factory
from people.forms import \
    KnownLanguageFormWithPerson,\
    DemographicForm,\
    PersonForm


from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.views import APIView


import logging
logger = logging.getLogger('corpora')
# sudo cat /webapp/logs/django.log


class ProfileDetail(APIView, TemplateView):
    template_name = "people/profile_detail.html"
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request, *args, **kwargs):
        person = get_or_create_person(self.request)
        demographic, created = Demographic.objects.get_or_create(person=person)
        if created:
            demographic.save()

        return super(ProfileDetail, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProfileDetail, self).get_context_data(**kwargs)

        person = get_or_create_person(self.request)
        serializer = PersonSerializer(person)
        context['person'] = person
        context['serializer'] = serializer

        context['demographic_form'] = DemographicForm(instance=person.demographic)
        context['person_form'] = PersonForm(instance=person)

        return context


def profile(request):

    if request.user.is_authenticated():
        sentence = get_next_sentence(request)
        current_language = get_current_language(request)
        person = Person.objects.get(user=request.user)
        known_languages = KnownLanguage.objects.filter(person=person)
        unknown_languages = get_unknown_languages(person)

        if not current_language:
            if len(known_languages) == 0:
                url = reverse('people:choose_language') + '?next=people:profile'
                return redirect(url)
            elif len(known_languages) >= 1:
                set_current_language_for_person(person, known_languages[0].language)
                current_language = known_languages[0].language
            else:
                logger.error('PROFILE VIEW: We need to handle this situation - NO CURRENT LANGUAGE but len know languages is YUGE')
                raise Http404("Something went wrong. We're working on this...")


        recordings = Recording.objects\
            .filter(
                person__user=request.user,
                sentence__language=current_language)\
            .order_by('-updated')

        sentences = get_sentences(request, recordings)
        known_languages = [i.language for i in known_languages]

        return render(request, 'people/profile.html',
            {'request': request,
             'user': request.user,
             'sentence': sentence,
             'current_language': current_language,
             'person': person,
             'recordings': recordings,
             'sentences': sentences,
             'known_languages': known_languages
             })
    else:
        # We should enable someone to provide recordings without loging in - and we can show their recordings - user coockies to track
        # BUt for now we'll redirect to login
        return redirect(reverse('account_login'))


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
    
    KnownLanguageFormset = inlineformset_factory(Person, KnownLanguage, form=KnownLanguageFormWithPerson, fields=('language','level_of_proficiency','person'), max_num=get_num_supported_languages(), extra= extra )
    # formset  = KnownLanguageFormset(form_kwargs={'person':person})
    # KnownLanguageFormsetWithPerson = inlineformset_factory(Person, KnownLanguage, form=form,  fields=('language','level_of_proficiency','person'), max_num=get_num_supported_languages(), extra=known_languages+1)
    
    if request.method == 'POST':
        formset = KnownLanguageFormset(request.POST, request.FILES, instance=person, form_kwargs={'person':person})
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
                    response  = redirect(reverse('people:choose_language'))

                response = set_language_cookie(response, current_language)

                return response


        else:
            if next_page:
                return redirect(reverse(next_page))
            else:
                return redirect(reverse('people:choose_language'))
            # formset = KnownLanguageFormsetWithPerson(instance=person)    
            
    else:

        formset = KnownLanguageFormset(instance=person, form_kwargs={'person':person})

        # for form in formset:
    response = render(request, 'people/choose_language.html', {'formset':formset, 'known_languages':known_languages, 'unknown_languages':unknown})

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

    if request.method=='POST':

        if request.POST.get('language','') != '':
            user_language = request.POST.get('language','')
            person = get_or_create_person(request)
            set_current_language_for_person(person, user_language)
            translation.activate(user_language)
            request.session[translation.LANGUAGE_SESSION_KEY] = user_language

            response = redirect(reverse(url)) #render(request,  'people/set_language.html')
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
