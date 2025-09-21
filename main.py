from dotenv import load_dotenv
import os
import imaplib
import re
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

status, data = mail.search(None, "BEFORE", "31-Dec-2024")
ids = data[0].split()

total_messages = len(ids)
print("filtered to %s messages", total_messages)

ids_by_addr = {}
counts_by_addr = Counter()
batch_size = 1000
bad_ids = []
for i in range(0, total_messages, batch_size):
    max_id = min(i + batch_size - 1, total_messages - 1)
    start = ids[i].decode()
    end = ids[max_id].decode()

    sequence_set = f"{start}:{end}"
    print("reading ids ", sequence_set) 
    status, msgs = mail.fetch(sequence_set, "(BODY.PEEK[HEADER.FIELDS (FROM)])")
    if status != "OK":
        print("Error reading message ", ids[i])
    for msg in msgs:
        if not isinstance(msg, tuple):
            continue
        try: 
            id = re.search(r"(\d+)", msg[0].decode()).group(1)
            addr_groups = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", msg[1].decode()) #i ripped this email regex off the web 
            if len(addr_groups.group()) == 0:
                bad_ids.append(id)
                continue
            addr = addr_groups.group(1)
            counts_by_addr[addr] += 1 
            
            if addr in ids_by_addr:
                ids_by_addr[addr].append(id)
            else:
                ids_by_addr[addr] = [id]
        except Exception as e:
            print("error reading the following msg ", msg[1].decode(), e)

for item, count in counts_by_addr.most_common(total_messages):
    print(item, count, ids_by_addr[item])

print("BAD IDS: ", bad_ids)