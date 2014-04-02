import poplib
import base64
from email.parser import Parser


class EmailHandler:

    def __init__(self, config):
        self.config = config

    def connect_to_server(self):
        self.pop_conn = poplib.POP3_SSL(self.config.get('Email', 'pop_url'))
        self.pop_conn.user(self.config.get('Email', 'username'))
        self.pop_conn.pass_(self.config.get('Email', 'password'))

    def disconnect_from_server(self):
        self.pop_conn.quit()

    def get_messages(self):
        messages = [(i, self.pop_conn.retr(i)) for i in range(1, len(self.pop_conn.list()[1]) + 1)]
        messages = [(i, "\n".join(mssg[1])) for (i, mssg) in messages]
        messages = [(i, Parser().parsestr(mssg)) for (i, mssg) in messages]
        return messages
    
    def delete_messages(self, message_indices):
        for message_index in message_indices:
            self.pop_conn.dele(message_index)

    def get_attachments(self, (i, message)):
        attachments = []
        if message['subject'] == "from your dvr's snap jpg":
            for attachment in message.get_payload()[1:]:
                filename = attachment['Content-Type'].replace('image/jpeg; name="', '').replace('"', '')
                binary = base64.b64decode(attachment.get_payload())
                attachments.append((i, filename, binary))
            return attachments
        else:
            return None
