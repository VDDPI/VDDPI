from flask import Flask, request, jsonify, make_response
from flask_restx import Resource, Api, fields
import ssl
import werkzeug
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
import ast
import base64
import json
import OpenSSL
import urllib.parse
from cryptography.hazmat.primitives import serialization
import hashlib
from OpenSSL.crypto import load_certificate
from OpenSSL.crypto import X509Store, X509StoreContext
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import PKCS1_v1_5
from Cryptodome.Hash import SHA256
import requests
import os
import MySQLdb
from datetime import datetime, timedelta
import subprocess
import jwt

data_file_path = "./data"

ROOTCA_CERT="./files/RootCA.pem"
# IAS_ROOTCA_CERT="./files/Intel_SGX_Attestation_RootCA.pem"
IAS_ROOTCA_CERT="./files/psuedo_Attestation_RootCA.pem"
ISV_STATUS_VALUE_FILE = "./files/isvEnclaveQuoteStatus.json"
REGISTRIES_API="./files/registries"

DBUSER = "root"
DBUSERPASS = "root"
DBPORT = 3306

HOST_NAME = os.environ["HOST_NAME"]
PRIVATE_CA = os.environ["PRIVATE_CA"]

class DataProcessingSpecification:
    
    def __init__(self, app_ID, input, output):
        self.app_ID = app_ID
        self.input = input
        self.output = output
    
    def is_same(self, app_ID, input, output):
        if (app_ID == self.app_ID and input == self.input and output == self.output):
            return True
        else:
            return False

class DataUsageDeclaration:

    def __init__(self, body, cert):

        keys = ["consumer", "app_ID", "data_ID", "arg_num", "counter", "location", "duration", "expiration_date", "signature"]
        
        data = ""
        
        for key in keys:
            try:
                locals()[key] = body[key]
                if (key != "signature"):
                    data = data + body[key]
            except:
                pass

        if (self.verify(data, locals()["signature"], cert)):
            self.consumer = locals()["consumer"]
            self.app_ID = locals()["app_ID"]
            self.data_ID = locals()["data_ID"]
            self.arg_num = locals()["arg_num"]
            
            if ("counter" in locals()):
                self.counter = int(locals()["counter"])
            else:
                self.counter = 0
            
            if ("location" in locals()):
                self.location = locals()["location"]
            else:
                self.location = None
            
            if ("duration" in locals()):
                self.duration = int(locals()["duration"])
            else:
                self.duration = 0

            if ("expiration_date" in locals()):
                self.expiration_date = locals()["expiration_date"]
            else:
                self.expiration_date = None

        else:
            raise RuntimeError("Failed to verify signature")

    def verify(self, data, signature, cert):
        # verify sig 
        sig = base64.b64decode(signature.encode())
        try:
            OpenSSL.crypto.verify(cert, sig, data, 'sha256')
            return True
        except OpenSSL.crypto.Error:
            return False

class DataProvidingPolcy:
    
    def __init__(self, provider, data_type, data_ID, consumer, app_ID, disclosing, counter, location, duration, expiration_date):
        self.provider = provider
        self.type = data_type
        self.data_ID = data_ID
        self.consumer = consumer
        self.app_ID = app_ID
        self.disclosing = disclosing
        self.counter = counter
        self.location = location
        self.duration = duration
        self.expiration_date = expiration_date

app = Flask(__name__)
api = Api(app, version='1.0', title='Data Providing Server', description="API for application")

def gen_certificate_request():
    subprocess.run(["openssl", "req", "-nodes", "-new", "-keyout", "files/private.key", "-out", "files/provider.csr", "-outform", "DER", "-subj", "/C=JP/CN=" + os.environ["HOST_NAME"]])

def get_server_cert():
    gen_certificate_request()
    with open("files/provider.csr", "rb") as f:
        csr = f.read()

    res = requests.post(url="http://" + PRIVATE_CA + "/issue", data=csr, params={"san": os.environ["HOST_NAME"]}, headers={"Context-Type": "application/octet-stream"})

    cert_filename = "files/server.pem"

    with open(cert_filename, "w") as f:
        f.write(res.text)

@app.route("/data/<data_type>/<data>")
def provide_data(data_type, data):
    pem_cert = request.environ.get("SSL_CLIENT_CERT")
    cert = x509.load_pem_x509_certificate(pem_cert.encode(), default_backend())

    app_ID = get_MRENCLAVE(cert)
    
    conn = MySQLdb.connect(user=DBUSER, passwd=DBUSERPASS, host="provider-db", port=DBPORT, db="provider")
    cur = conn.cursor()
    
    query = "SELECT * FROM saved_policy WHERE app_id = '%s' && data_id = '%s'" % (app_ID, "https://" + HOST_NAME + ":" + os.environ["SERVER_PORT"] + "/data/" + data_type + "/" + data)
    num = cur.execute(query)
    
    if (num != 1):
        cur.close()
        conn.close()
        msg =  f"Failed to load data usage policy (query:{query})"
        print(msg)
        print(query)
        return msg, 400
    else:
        res = cur.fetchone()
        cur.close()
        conn.close()
        
        ret = {}
        try:
            with open(data_file_path + "/" + data_type + "/" + data + ".json", "r") as f:
                ret["data"] = json.load(f)
            
            ret["condition"] = {}
            if (res[3] != None):
                ret["condition"]["counter"] = res[3]
            else:
                ret["condition"]["counter"] = ""
            
            if (res[4] != None):
                ret["condition"]["location"] = res[4]
            else:
                ret["condition"]["location"] = ""
            
            strtimefmt = "%Y-%m-%d"
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if (res[5] != None and res[6] != None):
                if (today + timedelta(days=res[5]) < datetime.strptime(res[6], strtimefmt)):
                    ret["condition"]["expirationDate"] = (today + timedelta(days=res[5])).strftime("%Y-%m-%d")
                else:
                    ret["condition"]["expirationDate"] = res[6]
            else:
                if (res[5] != None):
                    ret["condition"]["expirationDate"] = (today + timedelta(days=res[5])).strftime("%Y-%m-%d")
                if (res[6] != None):
                    ret["condition"]["expirationDate"] = res[6]
                else:
                    ret["condition"]["expirationDate"] = ""
            print("="*10 + "Data and Condition" + "=" * 10)
            print(ret)
            print("="*38)
            
            return jsonify(ret), 200
        except:
            return "Failed to get requested data", 500

app_res_doc = {
    200: "Success",
    400: "Failed (Invalid request)",
    500: "Failed (Server internal error)"
}

app_body_doc = api.model("application body", {
    "consumer": fields.String(description="Data consumer", required=True),
    "app_ID": fields.String(description="MRENCLAVE of the data processing app", required=True),
    "data_ID": fields.String(description="Requested data identifier (URL)", required=True),
    "counter": fields.String(description="available count", required=False),
    "location": fields.String(description="available country code", required=False),
    "duration": fields.String(description="available duration", required=False),
    "expiration_date": fields.String(description="expiration data", required=False),
    "signature": fields.String(description="signature", required=True)
})

@api.route("/apply")
class apply(Resource):
    @api.doc(body=app_body_doc)
    @api.doc(responses=app_res_doc)
    def post(self):
        pem_cert = request.environ.get("SSL_CLIENT_CERT")
        cert = x509.load_pem_x509_certificate(pem_cert.encode(), default_backend())
        data = request.json
        try:
            body = request.json
            usage_declaration = DataUsageDeclaration(body, cert)
        except RuntimeError:
            return make_response(jsonify({
                        "status": "failed",
                        "description": "Failed to verify data usage declaration's signature"
                    }), 400)

        subject = cert.subject
        
        # obtain the data processing spec
        print(f"Start processing spec retrieval (app_id:{usage_declaration.app_ID})")
        start = datetime.now()
        processing_spec = get_processing_spec(usage_declaration.app_ID)
        if (processing_spec is None):
            return make_response(jsonify({
                        "status": "failed",
                        "description": "Failed to get data processing specification"
                    }), 400)
        end = datetime.now()
        print(f"Finish processing spec retrieval")
        elapsed_ms = round((end - start).total_seconds() * 1000)
        print(f"___BENCH___ Processing spec retrieval (Start:{start.strftime('%Y-%m-%d %H:%M:%S')}, End:{end.strftime('%Y-%m-%d %H:%M:%S')}, Duration_ms:{elapsed_ms})")
        
        # obtain the data providing policy
        providing_policy = get_providing_policy(usage_declaration.data_ID)
        if (providing_policy is None):
            return make_response(jsonify({
                        "status": "failed",
                        "description": f"Failed to get data providing policy (data_id:{usage_declaration.data_ID})"
                    }), 400)
        
        # determine whether or not to provide data
        args = []
        for data_type in processing_spec.input:
            if (providing_policy.type == data_type.split("_")[0]):
                args.append(data_type)
        if (not args):
            return make_response(jsonify({
                        "status": "failed",
                        "description": "Failed to apply due to input constraints"
                    }), 400)
        
        if (subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value != usage_declaration.consumer):
            return make_response(jsonify({
                        "status": "failed",
                        "description": "Failed to apply (certificate and declaration information does not match)"
                    }), 400)
        
        if (subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value not in providing_policy.consumer):
            return make_response(jsonify({
                        "status": "failed",
                        "description": "Failed to apply (not allowed to provide for this consumer)"
                    }), 400)
        
        if (usage_declaration.app_ID not in providing_policy.app_ID):
            return make_response(jsonify({
                        "status": "failed",
                        "description": "Failed to apply (Not Allowed to provide for this application)"
                    }), 400)
        
        try:
            for output in processing_spec.output:
                if (len(output) == 0):
                    break
                
                if (output not in [disc.split(".")[0] + "_" + str(usage_declaration.arg_num) + "." + disc.split(".")[1] for disc in providing_policy.disclosing]):
                    return make_response(jsonify({
                                "status": "failed",
                                "description": "Failed to apply (not allowed to disclose)"
                            }), 400)
        except IndexError:
            return make_response(jsonify({
                        "status": "failed",
                        "description": "Failed to apply (invalid index)"
                    }), 400)
        
        # Access Counter
        if (providing_policy.counter != 0 and usage_declaration.counter != 0):
            if (providing_policy.counter < usage_declaration.counter):
                return make_response(jsonify({
                            "status": "failed",
                            "description": "Failed to apply (exceeded number of accesses allowed)"
                        }), 400)
            
            else:
                saved_counter = usage_declaration.counter
        
        elif (providing_policy.counter != None):
            saved_counter = providing_policy.counter
        
        elif (usage_declaration.counter != None):
            saved_counter = usage_declaration.counter
        
        else:
            saved_counter = None

        # Location
        if (providing_policy.location != None and usage_declaration.location != None):
            if (providing_policy.location != usage_declaration.location):
                return make_response(jsonify({
                            "status": "failed",
                            "description": "Failed to apply (Locations where access is not permitted)"
                        }), 400)

            else:
                saved_location = usage_declaration.location

        elif (providing_policy.location != None):
            saved_location = providing_policy.location

        elif (usage_declaration.location != None):
            saved_location = usage_declaration.location
        
        else:
            saved_location = None

        
        # Duration
        if (providing_policy.duration != 0 and usage_declaration.duration != 0):
            if (providing_policy.duration < usage_declaration.duration):
                return make_response(jsonify({
                            "status": "failed",
                            "description": "Failed to apply (exceeded access duration)"
                        }), 400)

            else:
                saved_duration = usage_declaration.duration

        elif (providing_policy.duration != None):
            saved_duration = providing_policy.duration

        elif (usage_declaration.duration != None):
            saved_duration = usage_declaration.duration
        
        else:
            saved_duration = None
        
        
        strtimefmt = "%Y-%m-%d"
        
        # Expiration Date
        if (providing_policy.expiration_date != None and usage_declaration.expiration_date != None):
            pp_date = datetime.strptime(providing_policy.expiration_date, strtimefmt)
            ud_date = datetime.strptime(usage_declaration.expiration_date, strtimefmt)
            if (pp_date < ud_date):
                return make_response(jsonify({
                            "status": "failed",
                            "description": "Failed to apply (exceeding the date of available)"
                        }), 400)

            else:
                saved_expiration_date = usage_declaration.expiration_date

        elif (providing_policy.expiration_date != None):
            saved_expiration_date = providing_policy.expiration_date

        elif (usage_declaration != None):
            saved_expiration_date = usage_declaration.expiration_date
        
        else:
            saved_expiration_date = None

        # Save the usage declaration
        conn = MySQLdb.connect(user=DBUSER, passwd=DBUSERPASS, host="provider-db", port=DBPORT, db="provider")
        cur = conn.cursor()
        
        query = "INSERT INTO saved_policy(consumer_subject, app_id, data_id, data_counter, data_location, data_duration, data_expiration_date)VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (usage_declaration.consumer, usage_declaration.app_ID, usage_declaration.data_ID, saved_counter, saved_location, saved_duration, saved_expiration_date)
        num = cur.execute(query)

        conn.commit()
        cur.close()
        conn.close()

        if (num != 1):
            
            return make_response(jsonify({
                        "status": "failed",
                        "description": "Failed to store declaration"
                    }), 500)
        
        payload = {
            "status": "completed",
            "consumer": usage_declaration.consumer,
            "app_ID": usage_declaration.app_ID,
            "data_ID": usage_declaration.data_ID,
            "arg_num": usage_declaration.arg_num,
            "counter": saved_counter,
            "location": saved_location,
            "duration": saved_duration,
            "expiration_date": saved_expiration_date
        }
        
        with open("files/private.key", "r") as f:
            jwt_assertion = jwt.encode(payload, f.read(), algorithm="RS512")
        
        with open("files/server.pem", "r") as f:
            ret = {
                "status": "completed",
                "jwt": jwt_assertion,
                "cert": f.read()
            }
    
        return make_response(jsonify(ret), 200)


def verify(self, ssl_sock, client_address):
    der_cert = ssl_sock.getpeercert(True)
    cert = x509.load_der_x509_certificate(der_cert, default_backend())

    for ext in cert.extensions:
        if (ext.value.oid.dotted_string == "1.2.3.4"):
            header = ast.literal_eval(ext.value.value.decode())
            signature = base64.b64decode(header["x-iasreport-signature"])
            certs = urllib.parse.unquote(header["x-iasreport-signing-certificate"])
            report_signing_cert_pem = certs.split("-----END CERTIFICATE-----")[0] + "-----END CERTIFICATE-----\n"

            # load IAS root CA certificate
            with open(IAS_ROOTCA_CERT, "rb") as f:
                root_cert_pem = f.read()
            
            # verify a certificate chain
            root_cert = load_certificate(OpenSSL.crypto.FILETYPE_PEM, root_cert_pem)
            report_signing_cert = load_certificate(OpenSSL.crypto.FILETYPE_PEM, report_signing_cert_pem)
            store = X509Store()
            store.add_cert(root_cert)
            store_ctx = X509StoreContext(store, report_signing_cert)
            try:
                store_ctx.verify_certificate()
            except Exception as e:
                print(e)
                return False

        elif (ext.value.oid.dotted_string == "1.2.3.5"):
            report = ast.literal_eval(ext.value.value.decode())
            quote = base64.b64decode(report["isvEnclaveQuoteBody"])
            
            # verify IAS signature
            cert_obj = x509.load_pem_x509_certificate(report_signing_cert_pem.encode(), default_backend())
            public_key = cert_obj.public_key()

            rsa_key = RSA.import_key(public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
            verifier = PKCS1_v1_5.new(rsa_key)
            hash = SHA256.new(json.dumps(report).encode())

            if (not verifier.verify(hash, signature)):
                print("Signature verification of IAS report failed.")
                return False
            
            with open(ISV_STATUS_VALUE_FILE, "r") as f:
                isvEnclaveQuoteStatusValue = json.load(f)

            print("=" * 119)
            print("Report Data\n")
            print("  timestamp: " + report["timestamp"])
            print("  isvEnclaveQuoteStatus: " + report["isvEnclaveQuoteStatus"])
            print("\n  (" + isvEnclaveQuoteStatusValue[report["isvEnclaveQuoteStatus"]] + ")\n")
            print(f"  ATTRIBUTES.FLAGS: {quote[96:104].hex()}  [ Debug bit: {quote[96] & 2 > 0} ]")
            print(f"  ATTRIBUTES.XFRM:  {quote[104:112].hex()}")
            print(f"  MRENCLAVE:        {quote[112:144].hex()}")
            print(f"  MRSIGNER:         {quote[176:208].hex()}")
            print(f"  ISVPRODID:        {quote[304:306].hex()}")
            print(f"  ISVSVN:           {quote[306:308].hex()}")
            print(f"  REPORTDATA:       {quote[368:400].hex()}")
            print(f"                    {quote[400:432].hex()}\n")
            print("=" * 119)

            # check REPORT_DATA
            pubkey_hash = hashlib.sha256(cert.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.PKCS1)).digest().hex()
            if (quote[368:400].hex() == pubkey_hash):
                print("+" + "-" * 68 + "+")
                print("|The value of REPORT_DATA and the hash value of the public key match.|")
                print("+" + "-" * 68 + "+")
            else:
                print("+" + "-" * 72 + "+")
                print("|The value of REPORT_DATA did not match the hash value of the public key.|")
                print("+" + "-" * 72 + "+")
                return False
            
            # check security level
            rejection_list = [
                "SIGNATURE_INVALID",
                "GROUP_REVOKED",
                "SIGNATURE_REVOKED",
                "KEY_REVOKED",
                "SIGRL_VERSION_MISMATCH"
            ]
            if (report["isvEnclaveQuoteStatus"] in rejection_list):
                print("The consumer platform can be compromised.")
                return False
            
    else:
        print("The client certificate was successfully verified!")
        return True
    return False

def get_processing_spec(MRENCLAVE):
    params = {"MRENCLAVE": MRENCLAVE}
    
    with open(REGISTRIES_API, "r") as f:
        registries = f.read().split("\n")[:-1]

    for registry in registries:
        res = json.loads(requests.get(registry, params=params).text)
        try:
            if ("policy" not in locals()):

                if (res["Input"] != None):
                    res_input = res["Input"].split(", ")
                else:
                    res_input = []
                    
                if (res["Output"] != None):
                    res_output = res["Output"].split(", ")
                else:
                    res_output = []
                
                policy = DataProcessingSpecification(MRENCLAVE, res_input, res_output)
            else:
                
                if (res["Input"] != None):
                    res_input = res["Input"].split(", ")
                else:
                    res_input = []
                    
                if (res["Output"] != None):
                    res_output = res["Output"].split(", ")
                else:
                    res_output = []
                
                if (not policy.is_same(MRENCLAVE, res_input, res_output)):
                    print("Verification Failed")
                    return None
        except Exception as e:
            print("--- Exception!! ---")
            print(e)
            return None
    
    return policy

def get_MRENCLAVE(cert):
    for ext in cert.extensions:
        if (ext.value.oid.dotted_string == "1.2.3.5"):
            report = ast.literal_eval(ext.value.value.decode())
            quote = base64.b64decode(report["isvEnclaveQuoteBody"])
            return quote[112:144].hex()
    else:
        raise RuntimeError("Cannot get MRENCLAVE")

def get_providing_policy(data_ID):
    
    conn = MySQLdb.connect(user=DBUSER, passwd=DBUSERPASS, host="provider-db", port=DBPORT, db="provider")
    cur = conn.cursor()
    
    query = "SELECT * FROM policy WHERE data_id = '%s'" % data_ID
    num = cur.execute(query)

    if (num != 1):
        cur.close()
        conn.close()
        return None
    else:
        res = cur.fetchone()
        cur.close()
        conn.close()
        return DataProvidingPolcy(res[0], res[1], res[2], res[3].split(", "), res[4], res[5].split(","), res[6], res[7], res[8], res[9])

if __name__ == '__main__':
    
    get_server_cert()
    
    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain("./files/server.pem", "./files/private.key")

    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.load_verify_locations(ROOTCA_CERT)
    werkzeug.serving.BaseWSGIServer.verify_request = verify

    app.run(debug=True, host="0.0.0.0", port=os.environ["SERVER_PORT"], ssl_context=ssl_context)
