from .models import QualityControl, Sentence, Recording
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType


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
        fields = ('id', 'good', 'bad', 'approved', 'approved_by', 'object_id', 'content_type',
                  'content_object', 'updated', 'person')


class QualityControRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        data = []
        serializer = QualityControlSerializer(value, context=self.parent.context)
        return serializer.data

        qcs = value.all()  # Length should always be 1!
        for qc in qcs:
            serializer = QualityControlSerializer(qc, context=self.parent.context)
            data.append(serializer.data)
        return data


class SentenceSerializer(serializers.HyperlinkedModelSerializer):
    quality_control = QualityControRelatedField(
        many=True,
        read_only=True,
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
        many=True,
        read_only=True,
    )
    audio_file_url = serializers.CharField(source='get_recording_file_url',
                                           read_only=True)

    class Meta:
        model = Recording
        fields = ('person', 'sentence', 'audio_file_url', 'quality_control', 'id')
