from dotenv import load_dotenv
import os
import imaplib
import re
from collections import Counter

import webbrowser
import threading
from flask import Flask, send_file, jsonify, request 
import time

app = Flask(__name__)
load_dotenv()

@app.route('/')
def index():
	return send_file('index.html')

def open_browser():
	time.sleep(.5)  
	webbrowser.open('http://localhost:8080')



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
print(f"filtered to {total_messages} messages")

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
    status, msgs = mail.fetch(sequence_set, "(UID BODY.PEEK[HEADER.FIELDS (FROM)])")
    if status != "OK":
        print("Error reading message ", ids[i])
    for msg in msgs:
        if not isinstance(msg, tuple):
            continue
        try: 
            numbers = re.findall(r"(\d+)", msg[0].decode())
            if len(numbers) >= 2:
                id = numbers[1]
            else:
                print(f"Unexpected message format: {msg[0].decode()}")
                continue
        except Exception as e:
            print("error reading the following msg ", msg[0].decode(), e)
        addr_groups = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", msg[1].decode()) #i ripped this email regex off the web 

        if addr_groups is None:
            bad_ids.append(id)
            continue

        addr = addr_groups.group(1)
        counts_by_addr[addr] += 1 
        
        if addr in ids_by_addr:
            ids_by_addr[addr].append(id)
        else:
            ids_by_addr[addr] = [id]


@app.route('/api/records')
def get_records():
    return jsonify([{'address': addr, 'count': count} for addr, count in counts_by_addr.most_common()])

@app.route('/api/delete', methods=['POST'])
def delete_emails(): #TODO check the response and return something else if need be
    addr = request.json['email']
    uids_to_delete = ids_by_addr[addr]
    uid_list = ','.join(uids_to_delete)
    mail.uid('STORE', uid_list, '+FLAGS', '(\\Deleted)')
    mail.expunge()
    return "OK", 200


threading.Thread(target=open_browser).start()
app.run(host='localhost', port=8080)