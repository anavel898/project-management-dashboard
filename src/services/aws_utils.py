# defining functions that will manage communication with aws services
import os
import boto3
from dotenv import load_dotenv


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
    

def send_email_via_ses(text:str, to_address: str):
    ses = boto3.client('ses')
    load_dotenv()
    sender = os.getenv("SES_SENDER")
    response = ses.send_email(
        Source=sender,
        Destination={
            'ToAddresses': [to_address]
            },
            Message={
                'Subject': {
                    'Data': 'Invite to project',
                    'Charset': 'utf-8'
                },
                'Body': {
                    'Text': {
                        'Data': text,
                        'Charset': "utf-8"
                        }
                }
            })
    return response['MessageId']

