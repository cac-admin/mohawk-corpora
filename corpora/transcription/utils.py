# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task

from corpora.utils.tmp_files import prepare_temporary_environment
from transcription.models import \
    TranscriptionSegment, AudioFileTranscription

from subprocess import Popen, PIPE


from wahi_korero import default_segmenter


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
        logger.debug("{0:04.2f}, {1:04.2f}".format(time, dt))
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
        logger.debug("{0:04.2f}, {1:04.2f}".format(tt['start'], tt['end']))

    return segments


def wahi_korero_segmenter(file_path):
    MIN_DURATION = 3*100
    segmenter = default_segmenter()
    segmenter.enable_captioning(100)
    seg_data, segments = segmenter.segment_audio(file_path)  # outputs "captioned" segments    
    segs = seg_data['segments']
    logger.debug(segs)

    captioned_for_real = []
    end=None
    while len(segs)>0:
        seg = segs.pop(0)
        if end:
            start = end
        else:
            start = float(seg['start'])*100
        d = float(seg['duration'])*100
        while d < MIN_DURATION:
            seg = segs.pop(0)
            d = d + float(seg['duration'])*100
        end = start + d
        captioned_for_real.append({'start': start, 'end': end})

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


def create_and_return_transcription_segments(aft):
    '''
    Creates the transcription segments from an AudioFileTranscription model.
    '''

    # We should delete all segments if we're going to create more!
    deleted = TranscriptionSegment.objects.filter(parent=aft).delete()

    try:
        file_path, tmp_stor_dir, tmp_file, absolute_directory = \
            prepare_temporary_environment(aft)
    except Exception as e:
        logger.debug('ERROR: {0}'.format(e))
        raise ValueError("{0}".format(e))


    # segmenter = DefaultSegmenter()
    # # segmenter.enableCaptioning(3, 8)
    # # segmenter.segmentAudio(file_path, tmp_stor_dir)  # save output to "path/to/output"
    # seg_data, audio_files = segmenter.segmentAudio(file_path)  # return output to user

    # logger.debug(seg_data)
    # logger.debug(audio_files)

    # segments = seg_data['segments']

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
