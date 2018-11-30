from __future__ import absolute_import, unicode_literals

from corpora.utils.tmp_files import prepare_temporary_environment

import commands


def get_media_duration(obj):
    '''
    Returns a media objects duration in seconds. Assumes the object has a
    `audio_file_field`
    '''

    file_path, tmp_stor_dir, tmp_file, absolute_directory = \
        prepare_temporary_environment(obj)

    code = \
        "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {0}".format(
            tmp_file)

    data = commands.getstatusoutput(code)
    return float(data[1])
