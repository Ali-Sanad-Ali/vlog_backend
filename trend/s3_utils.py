import boto3
from django.conf import settings
from botocore.config import Config

s3_client = boto3.client('s3',
                         endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                         region_name=settings.AWS_S3_REGION_NAME,
                         aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                         config=Config(signature_version='s3v4'))


class S3:

    def get_presigned_url(self, key, time=3600):
        return s3_client.generate_presigned_url(ClientMethod='put_object', ExpiresIn=time,
                                                Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key})

    def get_file(self, key, time=3600):
        return s3_client.generate_presigned_url(ClientMethod='get_object', ExpiresIn=time,
                                                Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key})

    def delete_file(self, key):
        return s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
