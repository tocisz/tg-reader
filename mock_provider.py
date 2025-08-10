from provider_contract import ProviderContract
from typing import List
from multipart import EmailMessageData

class MockProvider(ProviderContract):
    def download_files(self, file_list: List[str]) -> None:
        print(f"[MOCK] Downloading files from cloud: {file_list}")

    def upload_files(self, file_list: List[str]) -> None:
        print(f"[MOCK] Uploading files to cloud: {file_list}")

    def send_email(self, msg_data: EmailMessageData) -> None:
        print(f"[MOCK] Sending email to {msg_data.recipient} with subject '{msg_data.subject}' and body: {msg_data.html or msg_data.text}")
