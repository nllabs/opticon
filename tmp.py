import ConfigParser

from email_interface import EmailHandler
from s3 import S3

config = ConfigParser.RawConfigParser()
config.read('opticon.cfg')

e = EmailHandler(config)
s = S3(config)
s.connect_to_s3()
e.connect_to_server()

complete_messages = []
for message in e.get_messages():
    (i, filename, attachment) = e.get_attachment(message)
    s.save_to_key(filename, attachment)
    print filename + '\n'
    complete_messages.append(i)
e.delete_messages(complete_messages)
e.disconnect_from_server()
