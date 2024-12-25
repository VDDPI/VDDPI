import asn1
import hashlib
import requests
import base64
import json
from OpenSSL import crypto
import socket
import ssl

DUMMY_CERT = "./code/dummy.pem"
DUMMY_KEY = "./code/dummy.key"
CA_CERT = "./code/RootCA.pem"

def add_set(encoder, oid, value):
    encoder.enter(asn1.Numbers.Set)
    encoder.enter(asn1.Numbers.Sequence)
    
    encoder.write(oid, asn1.Numbers.ObjectIdentifier)
    encoder.write(value, asn1.Numbers.PrintableString)
    
    encoder.leave()
    encoder.leave()

def gen_certificate_request(c, st, l, o, cn, mail):
    encoder = asn1.Encoder()
    encoder.start()
    encoder.enter(asn1.Numbers.Sequence)
    encoder.enter(asn1.Numbers.Sequence)
    
    certReqInfoEncoder = asn1.Encoder()
    certReqInfoEncoder.start()
    certReqInfoEncoder.enter(asn1.Numbers.Sequence)
    
    # set version
    encoder.write(0, asn1.Numbers.Integer)
    certReqInfoEncoder.write(0, asn1.Numbers.Integer)

    # subject
    encoder.enter(asn1.Numbers.Sequence)
    certReqInfoEncoder.enter(asn1.Numbers.Sequence)
    
    # c = input("Country Name (2 letter code) [AU]:")
    if (c != ""):
        add_set(encoder, "2.5.4.6", c)
        add_set(certReqInfoEncoder, "2.5.4.6", c)

    # st = input("State or Province Name(full name) [Some-State]:")
    if (st != ""):
        add_set(encoder, "2.5.4.8", st)
        add_set(certReqInfoEncoder, "2.5.4.8", st)

    # l = input("Locality Name (eg, city) []:")
    if (l != ""):
        add_set(encoder, "2.5.4.7", l)
        add_set(certReqInfoEncoder, "2.5.4.7", l)

    # o = input("Organization Name (eg, company) [Internet Widgits Pty Ltd]:")
    if (o != ""):
        add_set(encoder, "2.5.4.10", o)
        add_set(certReqInfoEncoder, "2.5.4.10", o)

    # ou = input("Organization Name (eg, section) []:")
    ou = ""
    if (ou != ""):
        add_set(encoder, "2.5.4.11", ou)
        add_set(certReqInfoEncoder, "2.5.4.11", ou)

    # cn = input("Common Name (e.g. FQDN or YOUR name) []:")
    if (cn != ""):
        add_set(encoder, "2.5.4.3", cn)
        add_set(certReqInfoEncoder, "2.5.4.3", cn)

    # mail = input("Email Address []:")
    if (mail != ""):
        add_set(encoder, "1.2.840.113549.1.9.1", mail)
        add_set(certReqInfoEncoder, "1.2.840.113549.1.9.1", mail)

    encoder.leave()
    certReqInfoEncoder.leave()
    
    # entering subjectPublicKeyInfo
    encoder.enter(asn1.Numbers.Sequence)
    certReqInfoEncoder.enter(asn1.Numbers.Sequence)
    
    # entering algorithms
    encoder.enter(asn1.Numbers.Sequence)
    certReqInfoEncoder.enter(asn1.Numbers.Sequence)
    
    encoder.write("1.2.840.113549.1.1.1", asn1.Numbers.ObjectIdentifier)
    encoder.write(0, asn1.Numbers.Null)
    
    certReqInfoEncoder.write("1.2.840.113549.1.1.1", asn1.Numbers.ObjectIdentifier)
    certReqInfoEncoder.write(0, asn1.Numbers.Null)
    
    # leaving algorithm
    encoder.leave()
    certReqInfoEncoder.leave()
    
    # generate subject key
    subjectPKey, PKey = get_subject_pkey()
    
    # subjectPublicKey
    encoder.write(subjectPKey, asn1.Numbers.BitString)
    certReqInfoEncoder.write(subjectPKey, asn1.Numbers.BitString)
    
    # leaving subjectPublicKeyInfo
    encoder.leave()
    certReqInfoEncoder.leave()

    # entering attributes
    encoder.enter(0, asn1.Classes.Context)
    encoder.enter(asn1.Numbers.Sequence)

    certReqInfoEncoder.enter(0, asn1.Classes.Context)
    certReqInfoEncoder.enter(asn1.Numbers.Sequence)
    
    
    encoder.write("1.2.840.113549.1.9.14", asn1.Numbers.ObjectIdentifier)
    certReqInfoEncoder.write("1.2.840.113549.1.9.14", asn1.Numbers.ObjectIdentifier)
    
    encoder.enter(asn1.Numbers.Set)
    encoder.enter(asn1.Numbers.Sequence)
    encoder.enter(asn1.Numbers.Sequence)
    
    certReqInfoEncoder.enter(asn1.Numbers.Set)
    certReqInfoEncoder.enter(asn1.Numbers.Sequence)
    certReqInfoEncoder.enter(asn1.Numbers.Sequence)
    

    # get quote
    # get pubkey hash(sha256) and set REPORT_DATA
    pubKeyHash = hashlib.sha256(subjectPKey).digest()

    with open("/dev/attestation/user_report_data", "wb") as f:
        f.write(pubKeyHash)
    with open("/dev/attestation/quote", "rb") as f:
        quote = f.read()

    # get IAS report
    apiURL = 'http://192.168.11.1:8004/sgx/dev/attestation/v4/report/'
    json_data = {
        "isvEnclaveQuote": base64.b64encode(quote).decode("utf-8")
    }

    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY
    }

    response = requests.post(apiURL, json = json_data, headers=headers)

    encoder.write("1.2.3.4", asn1.Numbers.ObjectIdentifier)
    #encoder.write("false", asn1.Numbers.Boolean)
    encoder.write(str(response.headers), asn1.Numbers.OctetString)

    certReqInfoEncoder.write("1.2.3.4", asn1.Numbers.ObjectIdentifier)
    #certReqInfoEncoder.write("false", asn1.Numbers.Boolean)
    certReqInfoEncoder.write(str(response.headers), asn1.Numbers.OctetString)

    encoder.leave()
    certReqInfoEncoder.leave()

    encoder.enter(asn1.Numbers.Sequence)
    certReqInfoEncoder.enter(asn1.Numbers.Sequence)

    encoder.write("1.2.3.5", asn1.Numbers.ObjectIdentifier)
    #encoder.write("false", asn1.Numbers.Boolean)
    encoder.write(response.text, asn1.Numbers.OctetString)

    certReqInfoEncoder.write("1.2.3.5", asn1.Numbers.ObjectIdentifier)
    #certReqInfoEncoder.write("false", asn1.Numbers.Boolean)
    certReqInfoEncoder.write(response.text, asn1.Numbers.OctetString)

    encoder.leave()
    encoder.leave()
    encoder.leave()
    encoder.leave()
    encoder.leave()
    encoder.leave()

    certReqInfoEncoder.leave()
    certReqInfoEncoder.leave()
    certReqInfoEncoder.leave()
    certReqInfoEncoder.leave()
    certReqInfoEncoder.leave()
    certReqInfoEncoder.leave()

    certReqInfo = certReqInfoEncoder.output()
    sig = crypto.sign(PKey, certReqInfo, "sha1")

    # entering signatureAlgorithm
    encoder.enter(asn1.Numbers.Sequence)
    encoder.write("1.2.840.113549.1.1.5", asn1.Numbers.ObjectIdentifier)
    encoder.write(0, asn1.Numbers.Null)
    
    # leaving signatureAlgorithm
    encoder.leave()
    # signature
    encoder.write(sig, asn1.Numbers.BitString)

    encoder.leave()

    print("CSR was successfully generated.")
    
    return encoder.output(), PKey

def get_subject_pkey():
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    
    cert = crypto.X509()
    cert.get_subject().C = 'JP'
    cert.get_subject().ST = 'test'
    cert.get_subject().L = 'test'
    cert.get_subject().O = 'test'
    cert.get_subject().OU = 'test'
    cert.get_subject().CN = 'test'
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')

    decoder = asn1.Decoder()
    decoder.start(crypto.dump_certificate(crypto.FILETYPE_ASN1, cert))
    
    _, value = decoder.read()
    decoder.start(value)
    _, value = decoder.read()
    decoder.start(value)
    _, _ = decoder.read()
    _, _ = decoder.read()
    _, _ = decoder.read()
    _, _ = decoder.read()
    _, _ = decoder.read()
    _, value = decoder.read()
    decoder.start(value)
    _, _ = decoder.read()
    _, value = decoder.read()

    return value, key

if __name__ == '__main__':

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=DUMMY_CERT, keyfile=DUMMY_KEY)
    context.load_verify_locations(cafile=CA_CERT)
    context.verify_mode = ssl.CERT_REQUIRED

    bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bind_socket.bind(('0.0.0.0', 8001))
    bind_socket.listen(1)

    client_socket, fromaddr = bind_socket.accept()
    with context.wrap_socket(client_socket, server_side=True) as tls_socket:
        print(f"Client connected: {fromaddr} ")
        
        client_cert = tls_socket.getpeercert()
        if client_cert:
            subject = dict(x[0] for x in client_cert['subject'])
            client_cn = subject['commonName']
            print(f"Common Name: {client_cn}")
        else:
            print("Client certificate not found.")
            exit(1)
        
        data = tls_socket.recv(1024)
        msg = data.decode()
        privateCA = msg.split("\n")[0]
        SUBSCRIPTION_KEY = msg.split("\n")[1]
    
    csr, pkey = gen_certificate_request(subject.get("countryName", ""), subject.get("stateOrProvinceName", ""), subject.get("localityName", ""), subject.get("organizationName", ""), subject.get("commonName", ""), subject.get("mail", ""))

    with open("certs/private.key", "w") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey).decode("utf-8"))
    
    res = requests.post(url=privateCA, data=csr, headers={"Context-Type": "application/octet-stream"}).text

    cert_filename = "certs/client.pem"
    with open(cert_filename, "w") as f:
        f.write(res)
    
    client_socket.close()

