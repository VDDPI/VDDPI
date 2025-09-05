import requests
import json
import urllib3
import os
import jwt
import copy
import ast
import socket
import ssl
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from datetime import datetime
import plib
CA_CERT = "./code/RootCA.pem"
TRUSTED_CA_CERT = "./certs/RootCA.pem"
SKEY = "./certs/private.key"
CONSUMER_CERT = "./certs/client.pem"
DUMMY_CERT = "./code/dummy.pem"
DUMMY_KEY = "./code/dummy.key"

##############################################
######The following codes can be changed.#####
##############################################

def process_data(data):
    return data

##############################################
###The following codes must not be changed.###
##############################################

def data_acquisition(data_id, client_cn):
    try:
        received_data = receive_data(data_id, client_cn)
    except:
        return False, ""
    
    # cache data
    cache_data(received_data, received_data["path"])
    return True, received_data

def check_condition_phase(usage_condition):
    if(not check_expiration_date(usage_condition)):
        return False, 1
    
    if (not check_location(usage_condition)):
        return False, 0
    
    return True, 0

def check_expiration_date(condition):
    API_CA_CERT = """-----BEGIN CERTIFICATE-----
MIIDSzCCAjMCFDd4rPNHr1Devfmp0NLzGcr+6ggnMA0GCSqGSIb3DQEBCwUAMGIx
CzAJBgNVBAYTAkpQMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRl
cm5ldCBXaWRnaXRzIFB0eSBMdGQxGzAZBgNVBAMMEnJvb3RjYS5leGFtcGxlLmNv
bTAeFw0yNDA5MjcxMDE0MjBaFw0zNDA5MjUxMDE0MjBaMGIxCzAJBgNVBAYTAkpQ
MRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBXaWRnaXRz
IFB0eSBMdGQxGzAZBgNVBAMMEnJvb3RjYS5leGFtcGxlLmNvbTCCASIwDQYJKoZI
hvcNAQEBBQADggEPADCCAQoCggEBAM4/mSYFhpuHrREzpC64/RbICurPBeWsl7/T
2w21hXtS5z0FjD+sLaPAgr3C1mZkuh5GO/WzqIz9SNa9xMVMEMg+k7K6wIozgZzp
YPQVNBky1TvXQpm20rH+l0vms17ULXbuX26hqQJADARrUOSXdF+wsa8/CHHWqtWa
e06eoN79pqLZmTlRttCUBBMyWYXgEZy1iJczOgsi6u5iLlWj4zvmzUKcQev8BZV1
WC1DhmUgksfclgXLaVemyn35WRgUwsULMR5lB/URPcAjLRIf3n4eHie8mmMKLEez
9eOtvJImuwIWGNyT5cPv+jo9fY6y9lBt+Y6gXStFA5MPjAflIUkCAwEAATANBgkq
hkiG9w0BAQsFAAOCAQEArV2X1bcTzSFY3AtdtkDuUeJGwWlV6lfzyMm9lzS3WJJ3
rDOvQ8Q+G1ilJr4TC+xMIPcHS/XsUxmqPDlguPx9GaWxL/6MNczFsXhTllwBorZF
RHBhv8uT6LgV03xVq/XM+t4RT8SlTYmfz8xjKshFR4jdqz2QFJ6GrH2Xdny0hN3V
nwC3fcDP9wwIKMS5Jl8q9b0y7+uzjtB5qe3kW6cFNlJqDyP0cofH0cqGiRBDBZZC
RpW24O8MGN5wyHW/5P+FZ3UcQ78wS+s4girINinciiIqPayAWJsSLgfOKW8ogZ8P
krEL2VWGrv3IkBKvGUaSVu4rbwxqealC6vid1yi0TA==
-----END CERTIFICATE-----
"""
    CERT_PATH = "./certs/api_ca_cert.pem"
    TRUSTED_TIME_API_URL = "http://registry01.vddpi:8005/time"
    expiration_date_cond = condition["expirationDate"]
    if (expiration_date_cond == ""):
        return True, 1
    with open(CERT_PATH, "w") as f:
        f.write(API_CA_CERT)
    res_time = json.loads(requests.get(TRUSTED_TIME_API_URL, verify=CERT_PATH).text)["datetime"]
    os.remove(CERT_PATH)
    now = datetime.strptime(res_time[:19], "%Y-%m-%dT%H:%M:%S")
    datetime_expiration_date_cond = datetime.strptime(expiration_date_cond, "%Y-%m-%d")
    if (now <= datetime_expiration_date_cond):
        return True, 1
    else:
        return False, 0

def check_location(condition):
    API_CA_CERT = """-----BEGIN CERTIFICATE-----
MIIDSzCCAjMCFDd4rPNHr1Devfmp0NLzGcr+6ggnMA0GCSqGSIb3DQEBCwUAMGIx
CzAJBgNVBAYTAkpQMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRl
cm5ldCBXaWRnaXRzIFB0eSBMdGQxGzAZBgNVBAMMEnJvb3RjYS5leGFtcGxlLmNv
bTAeFw0yNDA5MjcxMDE0MjBaFw0zNDA5MjUxMDE0MjBaMGIxCzAJBgNVBAYTAkpQ
MRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBXaWRnaXRz
IFB0eSBMdGQxGzAZBgNVBAMMEnJvb3RjYS5leGFtcGxlLmNvbTCCASIwDQYJKoZI
hvcNAQEBBQADggEPADCCAQoCggEBAM4/mSYFhpuHrREzpC64/RbICurPBeWsl7/T
2w21hXtS5z0FjD+sLaPAgr3C1mZkuh5GO/WzqIz9SNa9xMVMEMg+k7K6wIozgZzp
YPQVNBky1TvXQpm20rH+l0vms17ULXbuX26hqQJADARrUOSXdF+wsa8/CHHWqtWa
e06eoN79pqLZmTlRttCUBBMyWYXgEZy1iJczOgsi6u5iLlWj4zvmzUKcQev8BZV1
WC1DhmUgksfclgXLaVemyn35WRgUwsULMR5lB/URPcAjLRIf3n4eHie8mmMKLEez
9eOtvJImuwIWGNyT5cPv+jo9fY6y9lBt+Y6gXStFA5MPjAflIUkCAwEAATANBgkq
hkiG9w0BAQsFAAOCAQEArV2X1bcTzSFY3AtdtkDuUeJGwWlV6lfzyMm9lzS3WJJ3
rDOvQ8Q+G1ilJr4TC+xMIPcHS/XsUxmqPDlguPx9GaWxL/6MNczFsXhTllwBorZF
RHBhv8uT6LgV03xVq/XM+t4RT8SlTYmfz8xjKshFR4jdqz2QFJ6GrH2Xdny0hN3V
nwC3fcDP9wwIKMS5Jl8q9b0y7+uzjtB5qe3kW6cFNlJqDyP0cofH0cqGiRBDBZZC
RpW24O8MGN5wyHW/5P+FZ3UcQ78wS+s4girINinciiIqPayAWJsSLgfOKW8ogZ8P
krEL2VWGrv3IkBKvGUaSVu4rbwxqealC6vid1yi0TA==
-----END CERTIFICATE-----
"""
    CERT_PATH = "./certs/api_ca_cert.pem"
    TRUSTED_GEOLOCATION_API_URL = "http://registry01.vddpi:8005/location"
    location_cond = condition["location"]
    if (location_cond == ""):
        return True, 1
    with open(CERT_PATH, "w") as f:
        f.write(API_CA_CERT)
    loc_info = json.loads(requests.post(TRUSTED_GEOLOCATION_API_URL, verify=CERT_PATH, json={"address": "dummy_ipAddr"}).text)
    os.remove(CERT_PATH)
    if (loc_info["countryCode"] == location_cond):
        return True, 1
    else:
        return False, 1

def data_saving(data):
    try:
        if (data["expired"] == True):
            return True
    except:
        pass
    
    if (data["condition"]["counter"] != "" and int(data["condition"]["counter"]) <= 0):
        return True
    else:
        store_data(data)
        return False

def verify_token(token, cert):
    # Verify Cert
    with open(TRUSTED_CA_CERT, "rb") as f:
        root_ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
    cert = x509.load_pem_x509_certificate(cert.replace("\\n", "\n").encode(), default_backend())
    
    root_ca_cert.public_key().verify(
        cert.signature,
        cert.tbs_certificate_bytes,
        padding.PKCS1v15(),
        cert.signature_hash_algorithm,
    )
    
    # Verify JWT
    public_key_pem = cert.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    payload = jwt.decode(
        jwt=token,
        key=public_key_pem.decode(),
        algorithms=["RS512"]
    )
    
    # Verify Indentity
    with open(CONSUMER_CERT, "rb") as f:
        client_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
    
    cname = client_cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
    if (payload["consumer"] != cname):
        raise RuntimeError("Invalid consumer")
    
    for ext in cert.extensions:
        if (ext.value.oid.dotted_string == "1.2.3.5"):
            report = ast.literal_eval(ext.value.value.decode())
            MRENCLAVE = base64.b64decode(report["isvEnclaveQuoteBody"])[112:144].hex()
            if (MRENCLAVE != payload["app_ID"]):
                raise RuntimeError("Invalid App")
            else:
                break
    
    return payload

def read_data_from_cache(file_path, client_cn):
    with open(file_path, "r") as f:
        cached_data = json.load(f)
        if (cached_data["clientCN"] != client_cn):
            print("Failed to load cached data due to invalid client CN.")
        return cached_data

CERTIFICATE_DN_CHECKED = False
def receive_data(data_id, received_cert_cn):
    global CERTIFICATE_DN_CHECKED
    if (not CERTIFICATE_DN_CHECKED):
        with open(CONSUMER_CERT, "rb") as cert_file:
            cert_data = cert_file.read()
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        consumer_cn = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
        if (received_cert_cn != consumer_cn):
            raise RuntimeError("Invalid Client Certificate (failed to verify client CN)")
        CERTIFICATE_DN_CHECKED = True
    
    data = json.loads(requests.get(data_id, verify=TRUSTED_CA_CERT, params={"data_id": data_id}, cert=(CONSUMER_CERT, SKEY)).text)
    data["path"] = "./data/" + data_id.replace("/", "-")
    data["clientCN"] = client_cn
    return data

def cache_data(data, file_path):
    with open(file_path, "w") as f:
        f.write(json.dumps(data))

def remove_data(data):
    try:
        os.remove(data["path"])
    except Exception as e:
        print("Failed to remove cached data")
        tls_socket.send("Failed to remove cached data".encode())

def store_data(data):
    with open(data["path"], "w") as f:
        f.write(json.dumps(data))

def request(client_cn, tokens):

    cached = False

    with open(CA_CERT, "rb") as cert:
        with open(TRUSTED_CA_CERT, "wb") as trusted_cert:
            trusted_cert.write(cert.read())
        
    providers = []
    for line in tokens.split("\n")[:-1]:
        try:
            payload = verify_token(line.split(",")[0], line.split(",")[1])
            providers.append(payload)
        except jwt.exceptions.InvalidSignatureError as e:
            print(f"JWT Invalid Signature: {e}")
            print(f"Problematic line: {line}")

            import traceback
            traceback.print_exc()

            tls_socket.send("Invalid Signature".encode())
        except Exception as e:
            print("Invalid Certificate")
            print(f"Error: {e}")
            print(f"Exception type: {type(e).__name__}")

            import traceback
            traceback.print_exc()

            tls_socket.send("Invalid Certificate".encode())

    provided_data_uc = []
    provided_data = []
    is_met_condition = True

    start = datetime.now()
    for usage_statement in providers:
        # is data cached?
        file_path = "./data/" + usage_statement["data_ID"].replace("/", "-")
        if (os.path.isfile(file_path)):
            # cache acquisition phase
            provided_data_uc.append(read_data_from_cache("./data/" + usage_statement["data_ID"].replace("/", "-"), client_cn))
            cached = True
        else:
            # data acquisition phase
            is_succeeded, data = data_acquisition(usage_statement["data_ID"], client_cn)
            if (not is_succeeded):
                print("Failed to receive data: " + usage_statement["data_ID"])
                tls_socket.send("Failed to receive data".encode())
                continue
            provided_data_uc.append(data)

        # data usage condition check phase
        is_ok, is_expired = check_condition_phase(provided_data_uc[-1]["condition"])
        if (not is_ok):
            print("The usage condition is not met: " + usage_statement["data_ID"])
            tls_socket.send("The usage condition is not met".encode())
            if (is_expired == 0):
                provided_data_uc[-1]["expired"] = True
            is_met_condition = False
        else:
            if (int(usage_statement["arg_num"]) == len(provided_data) + 1):
                provided_data.append(copy.deepcopy(provided_data_uc[-1]["data"]))
            else:
                print("Invalid argument number.")
                tls_socket.send("Invalid argument number".encode())
                continue
    
    if (is_met_condition):
        processed_data = process_data(*provided_data)
        
        # count decrement after processing data
        for data in provided_data_uc:
            if (data["condition"]["counter"] != ""):
                data["condition"]["counter"] = str(int(data["condition"]["counter"]) - 1)
        
        # output
        tls_socket.send(processed_data.encode())
    
    # data storing
    for data in provided_data_uc:
        expired = data_saving(data)
        if (expired):
            remove_data(data)

    end = datetime.now()
    elapsed_ms = round((end - start).total_seconds() * 1000)

    return start, end, elapsed_ms, is_met_condition, cached

if __name__ == "__main__":
    urllib3.disable_warnings(urllib3.exceptions.SecurityWarning)
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=DUMMY_CERT, keyfile=DUMMY_KEY)
    context.load_verify_locations(cafile=CA_CERT)
    context.verify_mode = ssl.CERT_REQUIRED
    
    bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bind_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bind_socket.bind(('0.0.0.0', 8002))
    bind_socket.listen(1)
    
    client_socket, fromaddr = bind_socket.accept()
    with context.wrap_socket(client_socket, server_side=True) as tls_socket:
        print(f"Client connected: {fromaddr} ")
        
        client_cert = tls_socket.getpeercert()
        if not client_cert:
            print("Client certificate not found.")
            exit(1)

        subject = dict(x[0] for x in client_cert['subject'])
        client_cn = subject['commonName']
        print(f"Common Name: {client_cn}")
        
        msg1 = tls_socket.recv(1024).decode()
        msg2 = ""
        for _ in range(int(msg1)):
            msg2 += tls_socket.recv(2048).decode()
    
        start, end, elapsed_ms, data_processed, cached = request(client_cn, msg2)

        msg = f"Session completed (start:{start.strftime('%Y-%m-%d %H:%M:%S')}, end:{end.strftime('%Y-%m-%d %H:%M:%S')}, duration_ms:{elapsed_ms}, data_processed:{data_processed}, cached:{cached})"

        tls_socket.send(msg.encode('utf-8'))

    bind_socket.close()
