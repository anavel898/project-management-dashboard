# defining functions that will manage communication with s3 bucket
import boto3


async def upload_file_to_s3(bucket_name: str, key: str, bin_file: bytes):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    try:
        #s3.upload_fileobj(bin_file, bucket_name, key)
        bucket.put_object(Key=key, Body=bin_file)
    except Exception as ex:
        print(ex)
        raise ex
    else:
        return True
    

async def download_file_from_s3(bucket_name: str, key: str):
    s3 = boto3.resource('s3')
    try:
        return s3.Object(bucket_name=bucket_name, key=key).get()['Body'].read()
    except Exception as ex:
        raise ex
    

async def delete_file_from_s3(bucket_name: str, key: str):
    s3 = boto3.resource('s3')
    try:
        return s3.Object(bucket_name=bucket_name, key=key).delete()
    except Exception as ex:
        raise ex
