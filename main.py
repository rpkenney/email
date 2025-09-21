from dotenv import load_dotenv
import os
import imaplib
from collections import Counter


load_dotenv()

EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
APP_PASSWORD = os.getenv("APP_PASSWORD")

IMAP_SERVER = "imap.mail.me.com"
IMAP_PORT = 993
mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)

mail.login(EMAIL_ACCOUNT, APP_PASSWORD)
mail.select("INBOX")  
print("Logged in")

status, data = mail.search(None, "SINCE", "01-Sep-2025")
ids = data[0].split()

total_messages = len(ids)
print("pulled %s messages", total_messages)
senders = Counter()

for i in range(0, 1):

    start = ids[i].decode()
    end = ids[i + 1].decode()

    sequence_set = f"{start}:{end}"
    
    status, msg_data = mail.fetch(sequence_set, "(BODY.PEEK[HEADER.FIELDS (FROM)])")
    if status != "OK":
        print("Error reading message ", ids[i])
    print(msg_data)
    

print("Top senders:")
for sender, count in senders.most_common(20):
    print(count, sender)