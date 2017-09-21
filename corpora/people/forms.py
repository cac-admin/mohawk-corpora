# -*- coding: utf-8 -*-
from django import forms
from .models import KnownLanguage, Person, Demographic

# from django.conf.settings import LANGUAGES

# form = modelform_factory(KnownLanguage, fields = ('language', 'level_or_proficiency'), initial = 'set person somehow, max_num = len(available_languages)')

import logging
logger = logging.getLogger('corpora')


class KnownLanguageFormWithPerson(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        person = kwargs.pop('person', None)
        super(KnownLanguageFormWithPerson, self).__init__(*args, **kwargs)


        # obj = self.fields['language']

        # choices = self.fields['language'].choices
        # current_language_value = self.fields['language'].initial


        # logger.debug(current_language_value)

        # known_languages = [i.language for i in KnownLanguage.objects.filter(person=person)]
        # alter_choices = []
        # for i in range(len(choices)):
        #     if choices[i][0] not in known_languages:
        #         alter_choices.append(choices[i])
        #     # elif 
        # self.fields['language'].choices = alter_choices
        # 

class DemographicForm(forms.ModelForm):
    # date_of_birth = DateField(input_formats=settings.DATE_INPUT_FORMATS)

    class Meta:
        model = Demographic
        fields = ('birthday', 'sex')
