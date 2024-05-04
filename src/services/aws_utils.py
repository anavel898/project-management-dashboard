# defining functions that will manage communication with aws services
import os
import boto3
from dotenv import load_dotenv

class SESService():
    @staticmethod
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

