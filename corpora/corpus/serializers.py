from .models import QualityControl, Sentence, Recording
from rest_framework import serializers


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


class ContentTypeStringRelatedField(serializers.StringRelatedField):
    def to_representation(self, value):
        return value.model


class QualityControlSerializer(serializers.ModelSerializer):
    content_object = QualityControlHyperLinkedRelatedField(
        read_only=True,
        view_name='api:sentence-detail'
        )
    content_type = ContentTypeStringRelatedField(read_only=True)

    class Meta:
        model = QualityControl
        fields = ('id', 'good', 'bad', 'approved', 'approved_by', 'object_id', 'content_type',
                  'content_object', 'updated')


class QualityControRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        qc = value.all()[0]  # Length should always be 1!
        serializer = QualityControlSerializer(qc, context=self.parent.context)
        return serializer.data


class SentenceSerializer(serializers.HyperlinkedModelSerializer):
    quality_control = QualityControRelatedField(
        many=False,
        read_only=True
    )

    class Meta:
        model = Sentence
        fields = ('id', 'text', 'language', 'quality_control', 'updated')


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
        many=False,
        read_only=True
    )

    class Meta:
        model = Recording
        fields = ('person', 'sentence', 'audio_file', 'quality_control')
