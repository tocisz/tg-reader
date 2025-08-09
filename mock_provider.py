from provider_contract import ProviderContract

class MockProvider(ProviderContract):
    def download_files(self, file_list):
        print(f"[MOCK] Downloading files from cloud: {file_list}")

    def upload_files(self, file_list):
        print(f"[MOCK] Uploading files to cloud: {file_list}")

    def send_email(self, address, subject, body):
        print(f"[MOCK] Sending email to {address} with subject '{subject}' and body: {body}")
