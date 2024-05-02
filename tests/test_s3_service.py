import unittest
from src.services.documents_utils import S3Service
from boto3.resources.factory import ServiceResource

class Test_S3Service(unittest.TestCase):
    def test_constructor(self):
        s3_service = S3Service("test-bucket-name")
        self.assertEqual("test-bucket-name", s3_service.bucket_name)
        self.assertIsInstance(s3_service.s3, ServiceResource)