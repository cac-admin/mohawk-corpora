from transcription.models import Transcription
from rest_framework import serializers
# from people.helpers import get_person
# from transcription.transcribe import transcribe_audio
from rest_framework.response import Response

from corpus.serializers import RecordingSerializer, QualityControRelatedField


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
