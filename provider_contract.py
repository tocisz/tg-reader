from abc import ABC, abstractmethod

class ProviderContract(ABC):
    @abstractmethod
    def download_files(self, file_list):
        pass

    @abstractmethod
    def upload_files(self, file_list):
        pass

    @abstractmethod
    def send_email(self, msg_data):
        """
        Send an email using the provided EmailMessageData object (see multipart.py).
        """
        pass
