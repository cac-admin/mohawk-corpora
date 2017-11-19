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

    if not recording.audio_file_aac:
        return encode_audio(recording)
    else:
        return "Already encoded"


@shared_task
def transcode_all_audio():
    recordings = Recording.objects.filter(audio_file_aac__isnull=True)
    for recording in recordings:
        transcode_audio(recording.pk)


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
    if not os.path.exists(tmp_file):
        if 'http' in file_path:
            r = RecordingFileView()
            url = r.get_redirect_url(filepath=file.name)
            code = 'wget '+url+' -O ' + tmp_file
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
    else:
        logger.debug('Exists: ' + os.path.abspath(tmp_file))

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

    return True
