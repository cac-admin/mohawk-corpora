from django.conf import settings

from storages.backends.s3boto import S3BotoStorage


# https://stackoverflow.com/questions/18536576/how-can-i-use-django-storages-for-both-media-and-static-files
class S3StaticStorage(S3BotoStorage):

    def __init__(self, *args, **kwargs):
        kwargs['bucket'] = settings.AWS_STATIC_BUCKET_NAME
        super(S3StaticStorage, self).__init__(*args, **kwargs)


class CachedS3BotoStorage(S3StaticStorage):
    """
    S3 storage backend that saves the files locally, too.
    """
    def __init__(self, *args, **kwargs):
        super(CachedS3BotoStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            "compressor.storage.CompressorFileStorage")()

    def save(self, name, content):
        self.local_storage._save(name, content)
        super(CachedS3BotoStorage, self).save(name, self.local_storage._open(name))
        return name
