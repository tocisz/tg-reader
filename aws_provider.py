import boto3
import os
from provider_contract import ProviderContract
from botocore.exceptions import ClientError

class AWSProvider(ProviderContract):
    def __init__(self, s3_bucket, ses_sender, ses_region="us-east-1"):
        self.s3_bucket = s3_bucket
        self.ses_sender = ses_sender
        self.ses_region = ses_region
        self.s3 = boto3.client("s3")
        self.ses = boto3.client("ses", region_name=ses_region)

    def download_files(self, file_list):
        for file_key in file_list:
            try:
                self.s3.download_file(self.s3_bucket, file_key, file_key)
                print(f"[AWS] Downloaded {file_key} from S3 bucket {self.s3_bucket}")
            except ClientError as e:
                print(f"[AWS] Error downloading {file_key}: {e}")

    def upload_files(self, file_list):
        for file_key in file_list:
            try:
                self.s3.upload_file(file_key, self.s3_bucket, file_key)
                print(f"[AWS] Uploaded {file_key} to S3 bucket {self.s3_bucket}")
            except ClientError as e:
                print(f"[AWS] Error uploading {file_key}: {e}")

    def send_email(self, address, subject, body):
        try:
            response = self.ses.send_email(
                Source=self.ses_sender,
                Destination={"ToAddresses": [address]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Data": body}}
                }
            )
            print(f"[AWS] Email sent to {address} with subject '{subject}'. MessageId: {response['MessageId']}")
        except ClientError as e:
            print(f"[AWS] Error sending email: {e}")
