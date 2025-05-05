from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    location = "proevent-media"
    file_overwrite = False

    default_acl = "public-read"
    querystring_auth = False


class StaticStorage(S3Boto3Storage):
    location = "proevent-static"
    file_overwrite = True
    default_acl = "public-read"
    querystring_auth = False
