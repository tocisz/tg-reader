from abc import ABC, abstractmethod

from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from multipart import EmailMessageData

class ProviderContract(ABC):
    @abstractmethod
    def download_files(self, file_list: List[str]) -> None:
        pass

    @abstractmethod
    def upload_files(self, file_list: List[str]) -> None:
        pass

    @abstractmethod
    def send_email(self, msg_data: 'EmailMessageData') -> None:
        """
        Send an email using the provided EmailMessageData object (see multipart.py).
        """
        pass
