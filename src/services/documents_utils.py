import boto3

from src.logs.logger import get_logger

logger = get_logger(__name__)

class S3Service():
    """
        Class for managing communication with s3 buckets
    """
    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name
        self.s3 = boto3.resource('s3')
    
    def upload_file_to_s3(self, key: str, bin_file: bytes, content_type: str):
        bucket = self.s3.Bucket(self.bucket_name)
        try:
            bucket.put_object(Key=key, Body=bin_file, ContentType=content_type)
        except Exception as ex:
            logger.error(f"Failed to upload file to S3. Error message: {ex}")
            raise ex
        else:
            return True
        

    def download_file_from_s3(self, key: str):
        try:
            return self.s3.Object(bucket_name=self.bucket_name, key=key).get()['Body'].read()
        except Exception as ex:
            logger.error(f"Failed to download from S3. Error message: {ex}")
            raise ex
    

    def delete_file_from_s3(self, key: str):
        try:
            return self.s3.Object(bucket_name=self.bucket_name, key=key).delete()
        except Exception as ex:
            logger.error(f"Failed to delete from S3. Error message: {ex}")
            raise ex
