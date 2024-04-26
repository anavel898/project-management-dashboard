import boto3
from PIL import Image

s3_client = boto3.client('s3')

def resize_image(image_path, resized_path):
    with Image.open(image_path) as image:
        image = image.resize((400, 400))
        image.save(resized_path)

def lambda_handler(event, context):
    # get bucket name and file key from the event object
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    download_path = f'/tmp/{key}'
    upload_path = f'/tmp/resized-{key}'
    
    if bucket_name == 'logos-raw':
        new_bucket_name = 'logos-processed'
        # download to /tmp directory, resize and upload to processed bucket
        s3_client.download_file(bucket_name, key, download_path)
        resize_image(download_path, upload_path)
        s3_client.upload_file(upload_path, new_bucket_name, key)
