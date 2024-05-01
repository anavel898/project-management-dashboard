import boto3
from PIL import Image
import io

s3_client = boto3.client('s3')

def resize_image(image_bytes):
    with Image.open(image_bytes) as image:
        image = image.resize((400, 400))
        output = io.BytesIO()
        image.save(output, format='JPEG')
        output.seek(0)
        return output

def lambda_handler(event, context):
    # get bucket name and file key from the event object
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    if bucket_name == 'logos-raw':
        new_bucket_name = 'logos-processed'
        # download to /tmp directory, resize and upload to processed bucket
        image_obj = s3_client.get_object(Bucket=bucket_name, Key=key)
        image_bytes = io.BytesIO(image_obj['Body'].read())
        resized_image = resize_image(image_bytes)
        s3_client.upload_fileobj(resized_image, new_bucket_name, key)
