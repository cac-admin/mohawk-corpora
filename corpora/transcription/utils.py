# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task

from corpora.utils.tmp_files import prepare_temporary_environment
from transcription.models import \
    TranscriptionSegment, AudioFileTranscription

from subprocess import Popen, PIPE


from wahi_korero import default_segmenter
import ast
from django.core.files import File

import logging
logger = logging.getLogger('corpora')


def dummy_segmenter(audio_file_path):
    MIN_DURATION = 4*100
    MAX_DURATION = 10*100

    code = "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {0}".format(
        audio_file_path)

    p = Popen(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
         'default=noprint_wrappers=1:nokey=1', audio_file_path],
        stdin=PIPE, stdout=PIPE)

    output, errors = p.communicate()

    duration = float(output)*100  # Milliseconds
    logger.debug("DURATION: {0:.2f}".format(duration))
    logger.debug("SEGMENTS:\n")
    segments = []
    time = 0
    while (time + MAX_DURATION) < duration:
        dt = MAX_DURATION + time
        segments.append({
            'start': time,
            'end': dt,
            'duration': MAX_DURATION})
        logger.debug("{0:04.2f}, {1:04.2f}".format(time/100, dt/100))
        time = time + MAX_DURATION

    segments.append({
            'start': time,
            'end': duration,
            'duration': MAX_DURATION})

    if len(segments) > 1:
        last_chunk = segments[-1]
        if last_chunk['end'] - last_chunk['start'] < MIN_DURATION:
            segments.pop()
            segments.pop()
            segments.append({
                'start': time-MAX_DURATION,
                'end': duration,
                'duration': MAX_DURATION
            })

        tt = segments[-1]
        logger.debug("{0:04.2f}, {1:04.2f}".format(tt['start']/100, tt['end']/100))

    return segments


def wahi_korero_segmenter(file_path):
    MIN_DURATION = 3*100

    p = Popen(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
         'default=noprint_wrappers=1:nokey=1', file_path],
        stdin=PIPE, stdout=PIPE)

    output, errors = p.communicate()
    duration = float(output)*100  # Milliseconds

    # Don't need to do this for short recordings!
    if duration < 10*100:
        return dummy_segmenter(file_path)

    segmenter = default_segmenter()
    segmenter.enable_captioning(
        caption_threshold_ms=50, min_caption_len_ms=None)
    seg_data, segments = segmenter.segment_audio(file_path)  # outputs "captioned" segments    
    segs = seg_data['segments']
    logger.debug(segs)

    captioned_for_real = []
    end = None
    while segs:
        seg = segs.pop(0)
        if end:
            start = end
        else:
            start = float(seg['start'])*100
        d = float(seg['duration'])*100

        while abs(int(d/100)) < int(MIN_DURATION/100):
            if segs:
                seg = segs.pop(0)
                d = d + float(seg['duration'])*100
            else:
                logger.debug('MOVING BACKWARDS')
                new_seg = captioned_for_real.pop()
                end = float(seg['end'])*100
                start = new_seg['start']
                d = end - start
                logger.debug("SEG:\t{0: 5.1f} {1: 5.1f}".format(start, end))
                logger.debug("DUR:\t{0: 3.1f}".format(d))

        end = start + d
        captioned_for_real.append({'start': start, 'end': end, 'duration': d})
        logger.debug(("SEG:\t{0: 6.1f} {1: 4.1f}").format(start/100, d/100))

    # for seg in segs:
    #     seg['start'] = float(seg['start'])*100
    #     seg['end'] = float(seg['end'])*100
    #     seg['duration'] = float(seg['duration'])*100
    return captioned_for_real


def create_transcription_segments_admin(aft):
    try:
        ts = create_and_return_transcription_segments(aft)
    except Exception as e:
        return "{0}".format(e)

    return "Created {0} segments from {1}".format(len(ts), aft.name)


def convert_audio_file_if_necessary(aft):
    file_path, tmp_stor_dir, tmp_file, absolute_directory = \
        prepare_temporary_environment(aft)

    #  Check that audio is in the right format
    command = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', tmp_file]
    p = Popen(command, stdin=PIPE, stdout=PIPE)
    output, errors = p.communicate()
    results = ast.literal_eval(output)
    convert = False
    for stream in results['streams']:
        if stream["codec_type"] in 'audio':
            if stream["codec_name"] not in "aac mp3 wav":
                convert = True

    if convert:
        new_file = '.'.join(tmp_file.split('.')[:-1]) + '.m4a'
        logger.debug(new_file)
        command = [
            'ffmpeg', '-i', tmp_file, '-ar', '44100', '-ac', '1',
            '-c:a', 'aac', new_file]

        logger.debug(command)
        p = Popen(command, stdin=PIPE, stdout=PIPE)
        output, errors = p.communicate()
        if not errors:
            aft.audio_file.save(new_file.split('/').pop(), File(open(new_file)))
            aft.save()
            # f.close()


def create_and_return_transcription_segments(aft):
    '''
    Creates the transcription segments from an AudioFileTranscription model.
    '''
    convert_audio_file_if_necessary(aft)
    # We should delete all segments if we're going to create more!
    deleted = TranscriptionSegment.objects.filter(parent=aft).delete()

    file_path, tmp_stor_dir, tmp_file, absolute_directory = \
        prepare_temporary_environment(aft)

    segments = wahi_korero_segmenter(tmp_file)

    # segments = dummy_segme   nter(tmp_file)

    logger.debug(segments)

    ts_segments = []
    for segment in segments:

        start = segment['start']
        end = segment['end']

        ts, created = TranscriptionSegment.objects.get_or_create(
            start=start,
            end=end,
            parent=aft)

        ts_segments.append(ts)
    return ts_segments


@shared_task
def compile_aft(aft_pk):
    aft = AudioFileTranscription.objects.get(pk=aft_pk)
    ts = TranscriptionSegment.objects\
        .filter(parent=aft)\
        .order_by('start')

    transcriptions = []
    for t in ts:
        if t.corrected_text:
            transcriptions.append(t.corrected_text.strip())

    aft.transcription = " ".join(transcriptions)

    aft.save()
