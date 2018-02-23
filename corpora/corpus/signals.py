from django.dispatch import receiver
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from .models import Sentence, Recording, QualityControl
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from corpus.tasks import set_recording_length, transcode_audio
from people.tasks import update_person_score

# @receiver(models.signals.post_save, sender=Sentence)
# @receiver(models.signals.post_save, sender=Recording)


def create_quality_control_instance_when_object_created(
        sender, instance, **kwargs):
    qc, created = QualityControl.objects.get_or_create(
            object_id=instance.pk,
            content_type=ContentType.objects.get_for_model(instance)
        )
    if created:
        print "Created QC object {0}".format(qc.pk)
    else:
        print "QC object {0} exists".format(qc.pk)


@receiver(models.signals.pre_save, sender=Sentence)
def clear_quality_control_instance_when_object_modified(
        sender, instance, **kwargs):

    if isinstance(instance, Sentence):
        try:
            old_sentence = Sentence.objects.get(pk=instance.pk)

            if not (old_sentence.text == instance.text and
                    old_sentence.language == instance.language):
                qcs = QualityControl.objects.filter(
                    object_id=instance.pk,
                    content_type=ContentType.objects.get_for_model(instance)
                    )
                for qc in qcs:
                    print "Clearing quality control"
                    qc.delete()

        except ObjectDoesNotExist:
            pass


@receiver(models.signals.pre_save, sender=Sentence)
@receiver(models.signals.pre_save, sender=Recording)
@receiver(models.signals.pre_save, sender=QualityControl)
def update_update_field_when_model_saved(sender, instance, **kwargs):
    instance.updated = timezone.now()


@receiver(models.signals.pre_save, sender=Sentence)
def split_sentence_when_period_in_sentence(sender, instance, **kwargs):
    parts = instance.text.split('.')
    for i in range(1, len(parts)):
        if len(parts[i]) < 6:  # This is arbitrary
            continue
        else:
            if parts[0][-1] in '!?.;':
                instance.text = parts[0]
            else:
                instance.text = parts[0]+'.'
            new_sentence = Sentence.objects.create(
                text=parts[i]+'.',
                language=instance.language)
            print "Created {0}".format(new_sentence)


# @receiver(models.signals.pre_save, sender=Sentence)
# def prevent_sentence_from_changing_when_recordings_exist(
#         sender, instance, **kwargs):
#     recordings = Recording.objects.filter(sentence=instance)
#     if len(recordings) > 0:
#         try:
#             old_sentence = Sentence.objects.get(pk=instance.pk)
#             instance.text = old_sentence.text
#         except ObjectDoesNotExist:
#             pass


@receiver(models.signals.post_save, sender=Recording)
def set_sentence_text_when_recording_created(
        sender, instance, created, **kwargs):
    if created:
        instance.sentence_text = instance.sentence.text
        instance.save()


# @receiver(models.signals.post_save, sender=Recording)
# def set_upadted_when_recording_saved(
#         sender, instance, created, **kwargs):
#     instance.updated = timezone.now()
#     instance.save()


@receiver(models.signals.post_save, sender=Recording)
def set_recording_length_on_save(sender, instance, created, **kwargs):
    if instance.audio_file:
        if instance.duration <= 0:
            set_recording_length.apply_async(
                args=[instance.pk],
                countdown=2,
                task_id='set_recording_length-{0}-{1}-{2}'.format(
                    instance.person.pk,
                    instance.pk,
                    instance.__class__.__name__))

        if not instance.audio_file_aac:
            transcode_audio.apply_async(
                args=[instance.pk],
                countdown=3,
                task_id='transcode_audio-{0}-{1}-{2}'.format(
                    instance.person.pk,
                    instance.pk,
                    instance.__class__.__name__))


@receiver(models.signals.post_save, sender=QualityControl)
@receiver(models.signals.post_save, sender=Recording)
def update_person_score_when_model_saved(sender, instance, **kwargs):
    update_person_score.apply_async(
        args=[instance.person.pk],
        countdown=4,
        task_id='update_person_score-{0}-{1}-{2}'.format(
            instance.person.pk,
            instance.pk,
            instance.__class__.__name__))


