import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("")


class SimpleStorage(object):
    PUT_METHOD = "put_object"
    GET_METHOD = "get_object"

    def __init__(self, access_key, secret_key, endpoint=None, region="ap-southeast-1"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint = endpoint
        self.region = region
        self._client = None
        self._resource = None

    @property
    def client(self):
        if not self._client:
            self._client = boto3.client('s3', endpoint_url=self.endpoint, aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key, region_name=self.region)
        return self._client

    @property
    def resource(self):
        if not self._resource:
            self._resource = boto3.resource('s3', endpoint_url=self.endpoint, aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key, region_name=self.region)
        return self._resource

    def list_bucket(self):
        return self.client.list_buckets().get("Buckets", [])

    def list_bucket_name(self):
        return [i.get('Name') for i in self.client.list_buckets().get("Buckets", [])]

    def create_bucket(self, bucket_name):
        try:
            self.client.create_bucket(Bucket=bucket_name)
        except ClientError as e:
            logger.error(e)
            return False
        return True

    def remove_bucket(self, bucket_name):
        try:
            self.client.re(Bucket=bucket_name)
        except ClientError as e:
            logger.error(e)
            return False
        return True

    def generate_public_url(self, bucket_name, object_name, content_type=None, path=None, expired_time=20):
        object_key = object_name if not path else f"{path}/{object_name}"
        params = {
            'Bucket': bucket_name,
            'Key': object_key,
            "ResponseContentType": content_type
        }
        return self.client.generate_presigned_url(ClientMethod="get_object",
                                                  Params=params,
                                                  ExpiresIn=expired_time)

    def generate_post_request(self, bucket_name, object_name, content_type=None, path=None, expired_time=20):
        object_key = object_name if not path else f"{path}/{object_name}"
        return self.client.generate_presigned_post(Bucket=bucket_name,
                                                   Key=object_key,
                                                   ExpiresIn=expired_time)

    def check_object_exits(self, bucket_name, object_name, path=None):
        object_key = object_name if not path else f"{path}/{object_name}"
        try:
            content = self.client.head_object(Bucket=bucket_name, Key=object_key)
            if content.get('ResponseMetadata', None) is not None:
                return False
            else:
                return True
        except Exception as e:
            print(e)
            return False


class SimpleBucket(object):
    def __init__(self, bucket_name, storage: SimpleStorage):
        self.bucket_name = bucket_name
        self.storage = storage
        self.check_bucket_exist()

    def check_bucket_exist(self):
        if self.bucket_name not in self.storage.list_bucket_name():
            self.storage.create_bucket(self.bucket_name)

    def put_object(self, object_name, binary_data, path="", meta_data=None):
        if not meta_data:
            meta_data = {}
        object_key = object_name if not path else f"{path}/{object_name}"
        try:
            self.storage.client.put_object(Body=binary_data, Bucket=self.bucket_name, Key=object_key, Metadata=meta_data)
        except Exception as e:
            print(e)
            return False
        return True

    def generate_public_url(self, object_name, method=None, content_type=None, path=None, expired_time=20):
        return self.storage.generate_public_url(self.bucket_name, object_name, content_type=content_type, path=path, expired_time=expired_time)

    def generate_post_request(self, object_name, method=None, content_type=None, path=None, expired_time=20):
        return self.storage.generate_post_request(self.bucket_name, object_name, content_type=content_type, path=path, expired_time=expired_time)

    def check_object_exits(self, object_name, path=None):
        return self.storage.check_object_exits(self.bucket_name, object_name=object_name, path=path)


class SimpleObject(object):
    def __init__(self, bucket: SimpleBucket, name, path):
        self.bucket = bucket
        self.name = name
        self.path = path

    def put(self, binary_data):
        return self.bucket.put_object(self.name, binary_data, self.path)

    def get_url(self, expired_time=20):
        return self.bucket.generate_public_url(self.name, self.path, expired_time)
