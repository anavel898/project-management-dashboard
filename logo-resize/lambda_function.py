import boto3
from PIL import Image
import io

s3_client = boto3.client('s3')

def resize_image(image_bytes, image_filetype):
    with Image.open(image_bytes) as image:
        image = image.resize((400, 400))
        output = io.BytesIO()
        image.save(output, format=image_filetype)
        output.seek(0)
        return output

def get_pil_format(image_object):
    image_filetype = image_object['ContentType']
    pil_format = 'JPEG'
    if image_filetype[6:] == 'png':
        pil_format = 'PNG'
    return pil_format


def lambda_handler(event, context):
    # get bucket name and file key from the event object
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    if bucket_name == 'logos-raw':
        new_bucket_name = 'logos-processed'
        # get raw image, resize and upload to processed bucket
        image_obj = s3_client.get_object(Bucket=bucket_name, Key=key)
        image_bytes = io.BytesIO(image_obj['Body'].read())
        file_type = get_pil_format(image_obj)
        resized_image = resize_image(image_bytes, file_type)
        s3_client.upload_fileobj(resized_image, new_bucket_name, key)
