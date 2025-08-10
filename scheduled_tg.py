# All imports
import os
import shutil
import json
import email_content


# Provider imports
from mock_provider import MockProvider
try:
    from aws_provider import AWSProvider
except ImportError:
    AWSProvider = None

# Load scheduled task configuration
with open('scheduled.json', 'r') as f:
    config = json.load(f)

tg_args = config.get('tg_args', {})
email_address = config.get('email_address')
cloud_files = config.get('cloud_files', [])



# Select provider from config
provider_cfg = config.get("provider", {})
provider_type = provider_cfg.get("type", "mock")
if provider_type == "aws" and AWSProvider is not None:
    aws_settings = provider_cfg.get("aws", {})
    provider = AWSProvider(
        s3_bucket=aws_settings.get("s3_bucket"),
        ses_sender=aws_settings.get("ses_sender"),
        ses_region=aws_settings.get("ses_region", "us-east-1")
    )
else:
    provider = MockProvider()


# Step 1: Download important files from cloud storage
def download_files():
    for file_key in cloud_files:
        try:
            provider.download_files([file_key], dest=file_key)
        except TypeError:
            provider.download_files([file_key])


# Step 2: Run tg logic (synchronous entrypoint)
def run_tg():
    # Import tg after files are downloaded
    import tg
    tg.main(
        tg_args.get('group_name'),
        tg_args.get('cutoff_time'),
        tg_args.get('message_limit', 1000),
        tg_args.get('summarize', False),
        silent=True
    )


# Step 3: Send email with results
def send_emails():
    if email_address:
        emails = email_content.generate_emails_from_chats("chats")
        for email in emails:
            msg_data = email["msg_data"]
            # Set recipient (and sender if needed)
            msg_data.recipient = email_address
            provider.send_email(msg_data)


# Step 4: Upload important files back to cloud storage (mocked)
def upload_files():
    for file_key in cloud_files:
        try:
            provider.upload_files([file_key])
        except TypeError:
            provider.upload_files([file_key])


def main():
    download_files()
    run_tg()
    send_emails()
    upload_files()


def lambda_handler(event, context):
    # Copy "config.json" to /tmp for Lambda execution
    shutil.copy('config.json', '/tmp/config.json')
    # Change working directory to /tmp at the start so all file I/O is Lambda-safe
    os.chdir('/tmp')

    main()

    return {"status": "ok"}

if __name__ == "__main__":
    main()
