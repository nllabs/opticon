from boto.s3.connection import S3Connection
from boto.s3.key import Key


class S3:
    def __init__(self, config):
        self.config = config
        self.bucket_url = self.config.get('AWS', 'bucket_url')

    def connect_to_s3(self):
        self.conn = S3Connection(self.config.get('AWS', 'aws_access_key_id'), self.config.get('AWS', 'aws_secret_access_key'))
        self.bucket = self.conn.get_bucket(self.config.get('AWS', 's3_bucket'))

    def save_to_key(self, filename, binary):
        k = Key(self.bucket)
        k.key = filename
        k.set_contents_from_string(binary)
        k.set_acl('private')


    def get_dominated_prefixes(self, prefix):
        return map(lambda x : x.name, self.bucket.list(prefix=prefix, delimiter='_'))

    def get_captures_from_prefix(self, prefix):
        l = map(lambda x: (x.key, self.bucket_url + x.key), self.bucket.list(prefix=prefix))
        return reversed(l)


