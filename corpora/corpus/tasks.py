from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.conf import settings

from django.core.exceptions import ObjectDoesNotExist
from corpus.models import Recording
from corpus.views.views import RecordingFileView
from django.contrib.sites.shortcuts import get_current_site

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


@shared_task
def encode_recording(recording):
    pass


@shared_task
def set_recording_length(recording_pk):
    try:
        recording = Recording.objects.get(pk=recording_pk)
    except ObjectDoesNotExist:
        logger.warning('Tried to get recording that doesn\'t exist')

    with contextlib.closing(wave.open(recording.audio_file, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        length = frames / float(rate)

    recording.duration = length
    recording.save()

    return 'Recording duration saved'


@shared_task
def set_all_recording_durations():
    recordings = Recording.objects.filter(duration__lte=0)
    for recording in recordings:
        set_recording_length(recording.pk)


@shared_task
def transcode_audio(recording_pk):
    try:
        recording = Recording.objects.get(pk=recording_pk)
    except ObjectDoesNotExist:
        logger.warning('Tried to get recording that doesn\'t exist')

    key = u"transcoding-{0}-{1}".format(
        recording.pk, recording.audio_file.name)

    is_running = cache.get(key)

    if is_running is None:
        is_running = cache.set(key, True, 60*5)
        if not recording.audio_file_aac:
            result = encode_audio(recording)
            cache.set(key, False, 60*5)
            return result

    elif is_running:
        return "Encoding in progress..."

    return "Already encoded."


@shared_task
def transcode_all_audio():
    recordings = Recording.objects.filter(audio_file_aac__isnull=True)
    logger.debug('Found {0} recordings to encode.'.format(len(recordings)))
    for recording in recordings:
        logger.debug('Encoding {0}.'.format(recording))
        try:
            encode_audio(recording)
        except:
            logger.error(sys.exc_info()[0])
            continue


def prepare_temporary_environment(recording, test=False):
    # This method gets strings for necessary media urls/directories and create
    # tmp folders/files
    # NOTE: we use "media" that should be changed.

    file = recording.audio_file

    if 'http' in file.url:
        file_path = file.url
    else:
        file_path = settings.MEDIA_ROOT + file.name

    tmp_stor_dir = settings.MEDIA_ROOT+'tmp/'+str(recording.pk)

    if not os.path.exists(tmp_stor_dir):
        os.makedirs(tmp_stor_dir)
        os.chmod(tmp_stor_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                 stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH)
        logger.debug('Created: ' + os.path.abspath(tmp_stor_dir))
    else:
        logger.debug('Exists: ' + os.path.abspath(tmp_stor_dir))

    tmp_file = tmp_stor_dir+'/'+file.name.split('/')[-1].replace(' ', '')

    # Will just replace file since we only doing one encode.
    if 'http' in file_path:
        r = RecordingFileView()
        url = r.get_redirect_url(filepath=file.name)
        code = 'wget "'+url+'" -O ' + tmp_file
    else:
        code = "cp '%s' '%s'" % (file_path, tmp_file)
    logger.debug(code)
    result = commands.getstatusoutput(code)
    logger.debug(result[0])
    try:
        logger.debug(result[1])
    except:
        logger.debug(result)

    if not os.path.exists(tmp_file):
        logger.debug('ERROR GETTING: ' + tmp_file)
        raise ValueError
    else:
        logger.debug('Downloaded: ' + os.path.abspath(tmp_file))

    absolute_directory = ''

    # if test:
    logger.debug(
        '\nMEDIA_PATH:\t%s\nTMP_STOR_DIR:\t%s\nTMP_FILE:\t%s\nABS_DIR:\t%s'
        % (file_path, tmp_stor_dir, tmp_file, absolute_directory))

    return file_path, tmp_stor_dir, tmp_file, absolute_directory


def encode_audio(recording, test=False, codec='aac'):

    codecs = {
        'mp3': ['libmp3lame', 'mp3'],
        'aac': ['libfdk_aac', 'm4a']
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
        file_name = recording.get_recordign_file_name()
        extension = codecs[codec][1]

        code = "ffmpeg -i {0} -vn -acodec {1} {2}/{3}.{4}".format(
            tmp_file, codecs[codec][0], tmp_stor_dir, file_name, extension)

        logger.debug('Running: '+code)
        data = commands.getstatusoutput(code)
        logger.debug(data[1])

        logger.debug(u'FILE FILENAME: \t{0}'.format(file_name))
        if file_name is None:
            file_name = 'audio'
        recording.audio_file_aac.save(
            file_name+'.'+extension,
            File(open(tmp_stor_dir+'/{0}.{1}'.format(file_name, extension))))

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

    set_s3_content_deposition.apply_async(
        args=[recording.pk],
        countdown=2,
        task_id='set_recording_content_deposition-{0}'.format(
            recording.pk)
        )

    return "Encoded {0}".format(recording)


@shared_task
def set_s3_content_deposition(recording_pk):
    import mimetypes

    if 's3boto' in settings.DEFAULT_FILE_STORAGE.lower():
        recording = Recording.objects.get(pk=recording_pk)

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
