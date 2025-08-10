import boto3
from provider_contract import ProviderContract
from botocore.exceptions import ClientError
from typing import List
from multipart import EmailMessageData

class AWSProvider(ProviderContract):
    def __init__(self, s3_bucket: str, ses_sender: str, ses_region: str = "us-east-1"):
        self.s3_bucket = s3_bucket
        self.ses_sender = ses_sender
        self.ses_region = ses_region
        self.s3 = boto3.client("s3")
        self.ses = boto3.client("ses", region_name=ses_region)

    def download_files(self, file_list: List[str]) -> None:
        for file_key in file_list:
            try:
                self.s3.download_file(self.s3_bucket, file_key, file_key)
                print(f"[AWS] Downloaded {file_key} from S3 bucket {self.s3_bucket}")
            except ClientError as e:
                print(f"[AWS] Error downloading {file_key}: {e}")

    def upload_files(self, file_list: List[str]) -> None:
        for file_key in file_list:
            try:
                self.s3.upload_file(file_key, self.s3_bucket, file_key)
                print(f"[AWS] Uploaded {file_key} to S3 bucket {self.s3_bucket}")
            except ClientError as e:
                print(f"[AWS] Error uploading {file_key}: {e}")

    def send_email(self, msg_data: EmailMessageData) -> None:
        from multipart import build_multipart_message
        # Fill sender/recipient if not set
        msg_data.sender = self.ses_sender
        if not msg_data.recipient:
            raise ValueError("Recipient must be set in EmailMessageData")
        # Build raw MIME message
        mime_msg = build_multipart_message(msg_data)
        try:
            response = self.ses.send_raw_email(
                Source=self.ses_sender,
                Destinations=[msg_data.recipient],
                RawMessage={"Data": mime_msg.as_string()}
            )
            print(f"[AWS] Email sent to {msg_data.recipient} with subject '{msg_data.subject}'. MessageId: {response['MessageId']}")
        except ClientError as e:
            print(f"[AWS] Error sending email: {e}")
