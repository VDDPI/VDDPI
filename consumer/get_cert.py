import requests
import argparse
import subprocess

KEY_PATH = "./consumer.key"
CSR_PATH = "./consumer.csr"
CERT_PATH = "./consumer.crt"
PFX_PATH = "./consumer.pfx"

def get_cert(ca_addr):

    subprocess.run(["openssl", "req", "-nodes", "-new", "-keyout", KEY_PATH, "-out", CSR_PATH, "-outform", "DER", "-days", "365"])

    with open(CSR_PATH, "rb") as f:
        csr = f.read()

    header = {
        "Context-Type": "application/octet-stream"
    }

    cert = requests.post("http://" + ca_addr + "/issue", data=csr, headers=header).text

    with open(CERT_PATH, "w") as f:
        f.write(cert)

    pfx = subprocess.run(["openssl", "pkcs12", "-export", "-inkey", KEY_PATH, "-in", CERT_PATH, "-out", PFX_PATH, "-passout", "pass:"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("CA_address")
    args = parser.parse_args()
    
    get_cert(args.CA_address)
