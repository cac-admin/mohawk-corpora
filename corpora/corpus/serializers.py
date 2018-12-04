from .models import QualityControl, Sentence, Recording, Source, Text
from rest_framework import serializers
from people.helpers import get_person
from rest_framework.response import Response
from django.utils.timezone import localtime

from django.core.files.base import ContentFile

from django.conf import settings
from boto.s3.connection import S3Connection

from corpus.aggregate import build_qualitycontrol_stat_dict

from six import text_type
import base64
import uuid
import logging

logger = logging.getLogger('corpora')


class SetPersonFromTokenWhenSelf(object):
    def run_validation(self, data):
        d2 = None
        if 'person' in data.keys():
            if data['person'] == 'self':
                d2 = data.copy()
                person = get_person(self.context['request'])
                if person is not None:
                    d2['person'] = person.id
                else:
                    d2['person'] = None
        if d2 is None:
            d2 = data
        return super(SetPersonFromTokenWhenSelf, self).run_validation(d2)


class QualityControlHyperLinkedRelatedField(
        serializers.HyperlinkedRelatedField):

    def to_representation(self, value):
        self.view_name = 'api:{0}-detail'.format(
            value.__class__.__name__.lower()
            )
        return super(
            QualityControlHyperLinkedRelatedField,
            self
            ).to_representation(value)


# class ContentTypeStringRelatedField(serializers.StringRelatedField):
#     def to_representation(self, value):
#         return value.model

#     def to_internal_value(self, value):
#         model = ContentType.objects.get(model='sentence')
#         return model.id


class QualityControlSerializer(
        SetPersonFromTokenWhenSelf, serializers.ModelSerializer):
    content_object = QualityControlHyperLinkedRelatedField(
        read_only=True,
        view_name='api:sentence-detail'
        )
    # person = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = QualityControl
        fields = ('id', 'good', 'bad', 'approved', 'approved_by', 'object_id',
                  'content_type', 'content_object', 'updated', 'person',
                  'delete', 'follow_up', 'noise', 'star',
                  'machine', 'source', 'notes')

    # def run_validation(self, data):
    #     if 'person' in data.keys():
    #         if data['person'] == 'self':
    #             d2 = data.copy()
    #             person = get_person(self.context['request'])
    #             d2['person'] = person.id
    #     return super(QualityControlSerializer, self).run_validation(d2)


class QualityControRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        serializer = QualityControlSerializer(value, context=self.parent.context)
        return serializer.data


class ListenQualityControRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        serializer = QualityControlSerializer(value, context=self.parent.context)
        person = get_person(self.parent.context['request'])
        data = serializer.data
        return data
        if person is data['person']:
            return serializer.data
        else:
            return None


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ('author',
                  'id',
                  'description',
                  'source_name',
                  'source_type',
                  'url',
                  'source_url',
                  'added_by',)
        read_only_fields = ('added_by',)
        extra_kwargs = {
            'url': {'view_name': 'api:source-detail'}
        }


class SentenceSerializer(serializers.HyperlinkedModelSerializer):
    quality_control = QualityControRelatedField(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Sentence
        fields = ('id', 'text', 'language', 'quality_control', 'updated', 'source')
        extra_kwargs = {
            'source': {'view_name': 'api:source-detail'}
        }


class SentenceSerializerNotNested(serializers.HyperlinkedModelSerializer):
    quality_control = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )

    class Meta:
        model = Sentence
        fields = ('id', 'text', 'language', 'quality_control', 'updated', 'source')
        extra_kwargs = {
            'source': {'view_name': 'api:source-detail'}
        }


class ReadSentenceSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Sentence
        fields = ('id', 'text', 'language',)


class RecordingSerializerPost(
        SetPersonFromTokenWhenSelf, serializers.ModelSerializer):
    class Meta:
        model = Recording
        fields = (
            'sentence_text', 'user_agent', 'audio_file',
            'person', 'id', 'sentence')

    def create(self, validated_data):
        # This sets a person even when you don't say person=self
        try:
            person = validated_data['person']
            if person is None:
                raise KeyError
        except KeyError:
            person = get_person(self.context['request'])
            if person is not None:
                validated_data['person'] = person

        recording = \
            super(RecordingSerializerPost, self).create(validated_data)

        # result = transcribe_audio(recording, validated_data['audio_file'])

        return recording
        # serializer = self.get_serializer(recording)
        # data = serializer.data
        # return Response(data)


class Base64FieldMixin(object):

    def _decode(self, data):
        if isinstance(data, text_type) and data.startswith('data:'):
            # base64 encoded file - decode
            format, datastr = data.split(';base64,')    # format ~= data:image/X,
            ext = format.split('/')[-1]    # guess file extension
            if ext[:3] == 'svg':
                ext = 'svg'
            data = ContentFile(
                base64.b64decode(datastr),
                name='{}.{}'.format(uuid.uuid4(), ext)
            )

            logger.debug("Data as string?")
            logger.debug(data[0:10])

        elif isinstance(data, text_type) and data.startswith('http'):
            logger.debug("FAIL")
            raise SkipField()

        elif isinstance(data, text_type):
            logger.debug('WTF - last resort')
            data = ContentFile(
                base64.b64decode(data),
                name='{}.{}'.format(uuid.uuid4(), 'm4a')
            )

        return data

    def to_internal_value(self, data):
        try:
            logger.debug("Data as send to to_internal_value")
            logger.debug(data[0:10])
        except:
            pass

        data = self._decode(data)

        try:
            logger.debug("Data as decoded")
            logger.debug(data[0:10])
        except:
            pass

        return super(Base64FieldMixin, self).to_internal_value(data)


class Base64FileField(Base64FieldMixin, serializers.FileField):
    pass


class RecordingSerializerPostBase64(
        SetPersonFromTokenWhenSelf, serializers.ModelSerializer):
    audio_file = Base64FileField()

    class Meta:
        model = Recording
        fields = (
            'sentence_text', 'user_agent', 'audio_file',
            'person', 'id', 'sentence')


class RecordingSerializer(serializers.ModelSerializer):
    sentence = SentenceSerializerNotNested(
        many=False,
        read_only=True
    )
    person = serializers.PrimaryKeyRelatedField(
        many=False,
        read_only=True
    )
    quality_control = QualityControRelatedField(
        many=True,
        read_only=True,
    )
    audio_file_url = serializers.CharField(source='get_recording_file_url',
                                           read_only=True)
    created = serializers.DateTimeField(
        format="%d-%m-%y %H:%M %Z",
        read_only=True)

    updated = serializers.SerializerMethodField()
    quality_control_aggregate = serializers.SerializerMethodField()
    transcription = serializers.SerializerMethodField()

    class Meta:
        model = Recording
        fields = ('person', 'sentence', 'audio_file_url', 'quality_control',
                  'id', 'sentence_text', 'user_agent', 'created', 'updated',
                  'audio_file_md5', 'audio_file_wav_md5',
                  'quality_control_aggregate', 'transcription',)

    def get_updated(self, obj):
        qc = obj.quality_control.all().order_by('-updated').first()
        if qc is not None:
            if qc.updated > obj.updated:
                return localtime(qc.updated)
        return localtime(obj.updated)

    def get_quality_control_aggregate(self, obj):
        return build_qualitycontrol_stat_dict(obj.quality_control.all())

    def get_transcription(self, obj):
        try:
            t = obj.transcription_set.first()
            return t.text
        except:
            pass
        return None


class ListenSerializer(serializers.ModelSerializer):
    sentence = ReadSentenceSerializer(
        many=False,
        read_only=True
    )
    # quality_control = QualityControRelatedField(
    #     many=True,
    #     read_only=True,
    # )
    audio_file_url = serializers.CharField(source='get_recording_file_url',
                                           read_only=True)

    class Meta:
        model = Recording
        fields = (
            'sentence', 'audio_file_url', 'id', 'sentence_text',
            # 'quality_control'
            )


class TextSerializer(serializers.ModelSerializer):
    source = SourceSerializer(partial=True, required=False)
    original_file = serializers.SerializerMethodField()
    cleaned_file = serializers.SerializerMethodField()

    class Meta:
        model = Text
        fields = (
            'id',
            'primary_language', 'secondary_language', 'dialect',
            'copyright', 'description', 'notes',
            'config',
            'original_file', 'original_file_md5',
            'cleaned_file', 'cleaned_file_md5',
            'source', 'updated',
        )

    def get_redirect_url(self, **kwargs):
        if settings.ENVIRONMENT_TYPE == 'local':
            return kwargs['filepath']
        s3 = S3Connection(settings.AWS_ACCESS_KEY_ID_S3,
                          settings.AWS_SECRET_ACCESS_KEY_S3,
                          is_secure=True)
        # Create a URL valid for 60 seconds.
        return s3.generate_url(60, 'GET',
                               bucket=settings.AWS_STORAGE_BUCKET_NAME,
                               key=kwargs['filepath'])

    def get_original_file(self, obj):
        user = self.context['request'].user
        if user.is_staff:
            return self.get_redirect_url(filepath=obj.original_file.name)
        else:
            return obj.original_file.name

    def get_cleaned_file(self, obj):
        user = self.context['request'].user
        if user.is_staff:
            return self.get_redirect_url(filepath=obj.original_file.name)
        else:
            return obj.cleaned_file.name
