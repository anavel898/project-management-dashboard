# defining functions that will manage communication with s3 bucket
import boto3


def upload_file_to_s3(bucket_name: str, key: str, bin_file: bytes):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    try:
        bucket.put_object(Key=key, Body=bin_file)
    except Exception as ex:
        print(ex)
        raise ex
    else:
        return True
    

def download_file_from_s3(bucket_name: str, key: str):
    s3 = boto3.resource('s3')
    try:
        return s3.Object(bucket_name=bucket_name, key=key).get()['Body'].read()
    except Exception as ex:
        raise ex
    

def delete_file_from_s3(bucket_name: str, key: str):
    s3 = boto3.resource('s3')
    try:
        return s3.Object(bucket_name=bucket_name, key=key).delete()
    except Exception as ex:
        raise ex
