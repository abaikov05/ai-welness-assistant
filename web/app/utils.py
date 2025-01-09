from .models import Chat, Message
from .assistant.settings import PRINT_FETCHED_CHAT_HISTOTY

from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
load_dotenv()
encryption_key = os.getenv("ENCRYPTION_KEY")

# Functions used by diffrent modules
async def get_chat_history(chat: Chat, limit: int, offset: int = 0, for_socket: bool = False, reverse:bool = False):
    encryption = Encryption()
    chat_history = []

    if offset > 0:
        offset = offset*limit
        limit = limit + offset
    message_range = slice(offset, limit)

    async for message in Message.objects.order_by('-time').filter(chat=chat)[message_range]:
        if message.is_bot:

            if for_socket:
                chat_history.append({"is_bot": True, "message": encryption.decrypt(message.text)})
            else:
                chat_history.append(f"Assistant: {encryption.decrypt(message.text)}")
        else:

            if for_socket:
                chat_history.append({"is_bot": False, "message": encryption.decrypt(message.text)})
            else:
                chat_history.append(f"User: {encryption.decrypt(message.text)}")
    
    if reverse:
        chat_history.reverse()
    if PRINT_FETCHED_CHAT_HISTOTY:
        print(f"{'_'*20}\nChat history fetched:")
        if for_socket:
            for i in chat_history:
                print(f"Bot:{i['is_bot']} - Msg: {i['message'][:70]}...")
        else:
            print('\n'.join(chat_history))
        print('_'*20)
    return chat_history

class Encryption():
    def __init__(self):
        self.encryptor = Fernet(encryption_key)
    def encrypt(self, text: str) -> str:
        encripted = self.encryptor.encrypt(text.encode())
        return encripted.decode()
    def decrypt(self, encrypted_text: str) -> str:
        text = self.encryptor.decrypt(encrypted_text.encode())
        return text.decode()
    