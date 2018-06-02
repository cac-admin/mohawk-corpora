from .models import QualityControl, Sentence, Recording, Source
from rest_framework import serializers
from people.helpers import get_person
from transcription.transcribe import transcribe_audio
from rest_framework.response import Response


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


class QualityControlSerializer(serializers.ModelSerializer):
    content_object = QualityControlHyperLinkedRelatedField(
        read_only=True,
        view_name='api:sentence-detail'
        )
    # content_type = ContentTypeStringRelatedField()

    # def create(self, validated_data):
    #     validated_data['content_type_id'] = validated_data['content_type']
    #     return QualityControl.objects.create(**validated_data)

    class Meta:
        model = QualityControl
        fields = ('id', 'good', 'bad', 'approved', 'approved_by', 'object_id',
                  'content_type', 'content_object', 'updated', 'person',
                  'delete', 'follow_up', 'noise', 'star')


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
                  'added_by',
                  'id',
                  'description',
                  'source_name',
                  'source_type',
                  'url',
                  'source_url')
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


class ReadSentenceSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Sentence
        fields = ('id', 'text', 'language',)


class RecordingSerializerPost(serializers.ModelSerializer):
    class Meta:
        model = Recording
        fields = ('sentence_text', 'user_agent', 'audio_file', 'person', 'id')

    def create(self, validated_data):
        recording = \
            super(RecordingSerializerPost, self).create(validated_data)

        result = transcribe_audio(recording, validated_data['audio_file'])

        return recording
        # serializer = self.get_serializer(recording)
        # data = serializer.data
        # return Response(data)


class RecordingSerializer(serializers.ModelSerializer):
    sentence = SentenceSerializer(
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

    class Meta:
        model = Recording
        fields = ('person', 'sentence', 'audio_file_url', 'quality_control',
                  'id', 'sentence_text', 'user_agent', 'created')


class ListenSerializer(serializers.ModelSerializer):
    sentence = ReadSentenceSerializer(
        many=False,
        read_only=True
    )
    quality_control = QualityControRelatedField(
        many=True,
        read_only=True,
    )
    audio_file_url = serializers.CharField(source='get_recording_file_url',
                                           read_only=True)

    class Meta:
        model = Recording
        fields = ('sentence', 'audio_file_url', 'id', 'sentence_text', 'quality_control')
