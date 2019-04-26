from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from corpus.models import Recording, QualityControl, Source
from django.contrib.contenttypes.models import ContentType
from corpus.views.views import RecordingFileView
from django.contrib.sites.shortcuts import get_current_site

from corpora.utils.media_functions import get_media_duration

from corpus.models import get_md5_hexdigest_of_file
from people.models import Person
from django.utils import timezone

from corpora.utils.tmp_files import prepare_temporary_environment

import datetime

from django.core.files import File
import wave
import contextlib
import os
import stat
import commands
import ast
import sys

from django.core.cache import cache

import logging
logger = logging.getLogger('corpora')
logger_test = logging.getLogger('django.test')


@shared_task
def encode_recording(recording):
    pass


@shared_task
def set_recording_length(recording_pk):
    try:
        recording = Recording.objects.get(pk=recording_pk)
    except ObjectDoesNotExist:
        logger.warning('Tried to get recording that doesn\'t exist')
        return 'Tried to get recording that doesn\'t exist'

    try:
        recording.duration = get_media_duration(recording)
        recording.save()
    except Exception as e:
        logger.error(e)
        return 'Cound not set Recording {0} duration'.format(recording.pk)

    return 'Recording {0} duration set to {1}'.format(
        recording.pk, recording.duration)


@shared_task
def set_all_recording_durations():
    recordings = Recording.objects.filter(duration__lte=0)
    for recording in recordings:
        set_recording_length(recording.pk)


@shared_task
def set_all_recording_md5():
    '''This method shouldn't live around too long because it's
   here to help with "migration". Once migration is done
   we could just run a task to ensure these fields are
   created. So this method is not very efficient and
   succient because we're gocusing on getting it done
   and then wil;l just delete it.
    '''
    recordings = Recording.objects\
        .filter(audio_file_md5=None)\
        .exclude(quality_control__delete=True)\
        .distinct()
    count = 0
    total = recordings.count()
    file_field = 'audio_file'

    start = timezone.now()

    if total == 0:
        recordings = Recording.objects\
            .filter(audio_file_wav_md5=None)\
            .exclude(quality_control__delete=True)\
            .distinct()

        count = 0
        total = recordings.count()
        file_field = 'audio_file_wav'

    logger_test.debug('Found {0} recordings to work on.'.format(total))
    source, created = Source.objects.get_or_create(
        source_name='Scheduled Task',
        source_type='M',
        author='Keoni Mahelona',
        source_url='/',
        description='Source for automated quality control stuff.'
    )
    person, created = Person.objects.get_or_create(
        uuid=settings.MACHINE_PERSON_UUID,
        full_name="Machine Person for Automated Tasks")
    if recordings:
        recording_ct = ContentType.objects.get_for_model(recordings.first())
    error = 0
    new_qc = 0
    for recording in recordings:
        count = count + 1
        if file_field == 'audio_file':
            audio_file_md5 = \
                get_md5_hexdigest_of_file(recording.audio_file)
            recording.audio_file_md5 = audio_file_md5
        elif file_field == 'audio_file_wav':
            audio_file_md5 = \
                get_md5_hexdigest_of_file(recording.audio_file_wav)
            recording.audio_file_wav_md5 = audio_file_md5
        else:
            continue

        if audio_file_md5 is not None:
            recording.save()
            logger_test.debug('{0} done.'.format(recording.pk))
        else:
            error = error + 1
            logger_test.debug(
                '{1: 6}/{2} Recording {0}: File does not exist.'.format(
                    recording.pk, count, total))
            qc, created = QualityControl.objects.get_or_create(
                delete=True,
                content_type=recording_ct,
                object_id=recording.pk,
                notes='File does not exist.',
                machine=True,
                source=source,
                person=person)
            if created:
                new_qc = new_qc + 1
            elif not qc:
                return "FATAL: WHY DON'T WE GET A QC!"
        if count >= 5000:
            # Terminate and respawn later.
            # minutes = 60*1
            # set_all_recording_md5.apply_async(
            #     countdown=minutes,
            # )
            time = timezone.now()-start
            return "Churned through {0} of {2} recordings with {3} errors. \
                    Created {1} QCs. Took {4}s".format(
                        count, new_qc, total, error, time.total_seconds())

    time = timezone.now()-start
    return "Churned through {0} of {2} recordings with {3} errors. \
            Created {1} QCs. Took {4}s".format(
            count, new_qc, total, error, time.total_seconds())


@shared_task
def transcode_audio(recording_pk):
    try:
        recording = Recording.objects.get(pk=recording_pk)
    except ObjectDoesNotExist:
        logger.warning('Tried to get recording that doesn\'t exist')

    key = u"xtrans-{0}-{1}".format(
        recording.pk, recording.audio_file.name)

    is_running = cache.get(key)

    result = ''
    if is_running is None:
        if not recording.audio_file_aac:
            is_running = cache.set(key, True, 60*5)
            result = encode_audio(recording)
            cache.set(key, False, 60)
        if not recording.audio_file_wav:
            is_running = cache.set(key, True, 60*5)
            result = result + encode_audio(recording, codec='wav')
            cache.set(key, False, 60)
        return result

    elif is_running:
        return u"Encoding in progress..."

    return u"Already encoded."


@shared_task
def transcode_all_audio():
    recordings = Recording.objects.filter(
        Q(audio_file_aac='') | Q(audio_file_aac=None))
    logger.debug('Found {0} recordings to encode.'.format(len(recordings)))
    count = 0
    message = []

    if settings.DEBUG:
        # We're in a dev env so no point transcoding old stuff
        t = timezone.now() - datetime.timedelta(days=1)
        recordings = recordings.filter(created__gte=t)

    for recording in recordings:
        logger.debug('Encoding {0}.'.format(recording))
        try:
            result = encode_audio(recording)
            message.append(result)
            count = count+1
        except:
            logger.error(sys.exc_info()[0])
            continue

    recordings = Recording.objects.filter(
        Q(audio_file_wav='') | Q(audio_file_wav=None))
    logger.debug(
        'Found {0} recordings to encode into wav.'.format(len(recordings)))
    count = 0
    for recording in recordings:
        logger.debug('Encoding {0}.'.format(recording))
        try:
            result = encode_audio(recording, codec='wav')
            message.append(result)
            count = count+1
        except:
            logger.error(sys.exc_info()[0])
            continue

    return u"Encoded {0}. {1}".format(count, ", ".join([i for i in message]))


def encode_audio(recording, test=False, codec='aac'):

    codecs = {
        'mp3': ['libmp3lame', 'mp3'],
        'aac': ['aac', 'm4a'],
        'wav': ['pcm_s16le', 'wav', 16000, 1]
    }

    file_path, tmp_stor_dir, tmp_file, absolute_directory = \
        prepare_temporary_environment(recording)

    # If a video doesn't have audio this will fail.
    command = 'ffprobe -v quiet -show_entries stream -print_format json ' + \
              tmp_file
    data = ast.literal_eval(commands.getoutput(command))
    streams = data['streams']

    audio = False
    for stream in streams:
        if stream['codec_type'] in 'audio':
            audio = True

    if audio:
        file_name = recording.get_recording_file_name()
        if codec in 'wav':
            file_name = file_name + '_16kHz'
        extension = codecs[codec][1]

        if codec in 'wav':
            code = "ffmpeg -i {0} -vn -acodec {1} -ar {2} -ac {3} {4}/{5}.{6}".format(
                tmp_file,
                codecs[codec][0], codecs[codec][2], codecs[codec][3],
                tmp_stor_dir, file_name, extension)
        else:
            code = "ffmpeg -i {0} -vn -acodec {1} {2}/{3}.{4}".format(
                tmp_file, codecs[codec][0], tmp_stor_dir, file_name, extension)

        logger.debug('Running: '+code)
        data = commands.getstatusoutput(code)
        logger.debug(data[1])

        logger.debug(u'FILE FILENAME: \t{0}'.format(file_name))
        if file_name is None:
            file_name = 'audio'

        if 'aac' in codec:
            recording.audio_file_aac.save(
                file_name+'.'+extension,
                File(open(tmp_stor_dir+'/{0}.{1}'.format(
                    file_name, extension))))
        elif 'wav' in codec:
            recording.audio_file_wav.save(
                file_name+'.'+extension,
                File(open(tmp_stor_dir+'/{0}.{1}'.format(
                    file_name, extension))))

        code = 'rm '+tmp_stor_dir+'/{0}.{1}'.format(file_name, extension)
        logger.debug('Running: '+code)
        data = commands.getstatusoutput(code)
        logger.debug(data[1])

    if not audio:
        logger.debug('No audio stream found.')
        return False

    data = commands.getstatusoutput('rm ' + tmp_file)
    logger.debug('Removed tmp file %s' % (tmp_file))

    data = commands.getstatusoutput('rm -r ' + tmp_stor_dir)
    logger.debug('Removed tmp stor dir %s' % (tmp_stor_dir))

    set_s3_content_deposition(recording)

    return "Encoded {0}".format(recording)


@shared_task
def set_s3_content_deposition(recording):
    import mimetypes

    if 's3boto' in settings.DEFAULT_FILE_STORAGE.lower():

        from boto.s3.connection import S3Connection
        c = S3Connection(
            settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        b = c.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)  # , validate=False)

        attrs = ['audio_file', 'audio_file_aac']
        for attr in attrs:
            file = getattr(recording, attr)
            if file:

                k = file.name
                key = b.get_key(k)  # validate=False)

                if key is None:
                    return "Error: key {0} doesn't exist in S3.".format(key)
                else:
                    metadata = key.metadata
                    metadata['Content-Disposition'] = \
                        "attachment; filename={0}".format(
                            file.name.split('/')[-1])
                    metadata['Content-Type'] = \
                        mimetypes.guess_type(file.url)[0]
                    key.copy(
                        key.bucket,
                        key.name,
                        preserve_acl=True,
                        metadata=metadata)
        return metadata

    else:
        return 'Non s3 storage - not setting s3 content deposition.'
