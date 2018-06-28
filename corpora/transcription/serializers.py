from django.core.exceptions import ValidationError

from transcription.models import \
    Transcription, TranscriptionSegment, AudioFileTranscription

from people.helpers import get_person

from rest_framework import serializers
# from people.helpers import get_person
# from transcription.transcribe import transcribe_audio
from rest_framework.response import Response

from corpus.serializers import RecordingSerializer, QualityControRelatedField

import logging
logger = logging.getLogger('corpora')


class TranscriptionSerializerPost(serializers.ModelSerializer):
    class Meta:
        model = Transcription
        fields = ('recording', 'text', 'corrected_text', 'updated',
                  'source', 'quality_control')

    # def create(self, validated_data):
    #     recording = \
    #         super(RecordingSerializerPost, self).create(validated_data)

    #     result = transcribe_audio(recording, validated_data['audio_file'])

    #     return recording
    #     # serializer = self.get_serializer(recording)
    #     # data = serializer.data
    #     # return Response(data)


class TranscriptionSerializer(serializers.ModelSerializer):
    recording = RecordingSerializer(
        many=False,
        read_only=False
    )
    quality_control = QualityControRelatedField(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Transcription
        fields = ('recording', 'text', 'corrected_text', 'quality_control',
                  'id', 'source', 'updated')


class TranscriptionSegmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = TranscriptionSegment
        fields = ('corrected_text', 'start', 'end', 'parent', 'edited_by', 'pk')


class AudioFileTranscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = AudioFileTranscription
        fields = ('uploaded_by', 'audio_file', 'pk', 'name', 'transcription')
        read_only_fields = ('uploaded_by',)

    def validate_uploaded_by(self, validated_data):
        # if validated_data is None:
        return get_person(self.context['request'])
        # return validated_data

    def create(self, validated_data):
        validated_data['uploaded_by'] = get_person(self.context['request'])
        return super(AudioFileTranscriptionSerializer, self).create(validated_data)

    # def validate_audio_file(self, validated_data):
    #     if validated_data is None:
    #         raise ValidationError('A file is required')
    #     return validated_data
