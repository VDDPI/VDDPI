import argparse
from OpenSSL import crypto
import base64
import json
import requests

from datetime import datetime, timedelta

def get_expiration(_days):
    today = datetime.now().date()
    thirty_days_later = today + timedelta(days=_days)
    return thirty_days_later.strftime('%Y-%m-%d')

def create_declaration(subject, app_id, data_id, arg_index, key, counter, location, duration, expiration_date):
    
    data = subject + app_id + data_id + arg_index + counter + location + duration + expiration_date
    with open(key, "r") as f:
        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, f.read())
        data_bytes = data.encode("utf-8")
        sig = base64.b64encode(crypto.sign(pkey, data_bytes, "sha256")).decode()

    ret = {
        "consumer": subject,
        "app_ID": app_id,
        "data_ID": data_id,
        "arg_num": arg_index,
        "counter": counter,
        "location": location,
        "duration": duration,
        "expiration_date": expiration_date,
        "signature": sig,
    }
    return ret

def apply(usage_statement, output_path, write_mode):

    client_cert = "./cache/consumer.crt"
    client_key  = "./cache/consumer.key"
    ca_cert     = "./cache/RootCA.pem"

    provider_addr = usage_statement["data_ID"].split("//")[1].split("/")[0]
    ret = json.loads(requests.post("https://" + provider_addr + "/apply", verify=ca_cert, cert=(client_cert, client_key), json=usage_statement).text)

    if (ret["status"] == "failed"):
        print(ret)
        return
    
    with open(output_path, write_mode) as f:
        f.write(ret["jwt"] + "," + ret["cert"].replace("\n", "\\n")[:-2] + "\n")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-ct", "--counter", default="5")
    parser.add_argument("-loc", "--location", default="JP")
    parser.add_argument("-dr", "--duration", default="30")
    parser.add_argument("-exd", "--expiration_date", default=get_expiration(30))
    parser.add_argument("-o", "--output-path", default="cache/tokens")
    parser.add_argument("-a", "--append-token", action="store_true")

    parser.add_argument("subject")
    parser.add_argument("app_id")
    parser.add_argument("data_id")
    parser.add_argument("arg_index")
    parser.add_argument("key")

    args = parser.parse_args()
    
    usage_statement = create_declaration(args.subject, args.app_id, args.data_id, args.arg_index, args.key, args.counter, args.location, args.duration, args.expiration_date)

    write_mode = "w"
    if args.append_token:
        write_mode = "a"

    apply(usage_statement, args.output_path, write_mode)

