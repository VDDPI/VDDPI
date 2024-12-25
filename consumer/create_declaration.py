import argparse
from OpenSSL import crypto
import base64
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from Cryptodome.Hash import SHA256
import sys
import OpenSSL
import json
import requests

DEFAULT_SIG_KEY_PATH = "./consumer.key"
DECLARATION_FILE = "./code/data_usage_declaration"

CLIENT_CERT = "./consumer.crt"
CLIENT_KEY = "./consumer.key"
CA_CERT = "./code/RootCA.pem"

def create_declaration(subject, app_id, data_id, arg_num, counter, location, duration, expiration_date, key):
    
    # interactive
    if (subject == None):
        subject = input("Subject: ")
    
    if (app_id == None):
        app_id = input("App ID: ")
    
    if (data_id == None):
        data_id = input("Data ID: ")
    
    if (arg_num == None):
        arg_num = input("Argument Number: ")
    
    if (counter == None):
        counter = input("Counter: ")
    
    if (location == None):
        location = input("Location (Country Code): ")
    
    if (duration == None):
        duration = input("Duration (Days): ")
    
    if (expiration_date == None):
        expiration_date = input("Expiration Date (ISO Format): ")
    
    if (key == None):
        key = DEFAULT_SIG_KEY_PATH
    
    data = subject + app_id + data_id + arg_num + counter + location + duration + expiration_date
    with open(key, "r") as f:
        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, f.read())
        sig = base64.b64encode(crypto.sign(pkey, data, "sha256")).decode()

    ret = {
        "consumer": subject,
        "app_ID": app_id,
        "data_ID": data_id,
        "arg_num": arg_num,
        "counter": counter,
        "location": location,
        "duration": duration,
        "expiration_date": expiration_date,
        "signature": sig,
    }
    return ret

def apply(usage_statement):
    provider_addr = usage_statement["data_ID"].split("//")[1].split("/")[0]
    ret = json.loads(requests.post("https://" + provider_addr + "/apply", verify=CA_CERT, cert=(CLIENT_CERT, CLIENT_KEY), json=usage_statement).text)

    if (ret["status"] == "failed"):
        return
    
    with open("./code/tokens", "a") as f:
        f.write(ret["jwt"] + "," + ret["cert"].replace("\n", "\\n")[:-2] + "\n")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-subj", "--subject")
    parser.add_argument("-ai", "--app_id")
    parser.add_argument("-di", "--data_id")
    parser.add_argument("-an", "--arg_num")
    parser.add_argument("-ct", "--counter")
    parser.add_argument("-loc", "--location")
    parser.add_argument("-dr", "--duration")
    parser.add_argument("-exd", "--expiration_date")
    parser.add_argument("-key")

    args = parser.parse_args()
    
    usage_statement = create_declaration(args.subject, args.app_id, args.data_id, args.arg_num, args.counter, args.location, args.duration, args.expiration_date, args.key)
    
    apply(usage_statement)

