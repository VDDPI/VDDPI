import requests
import argparse
import subprocess

def get_cert(ca_addr, cache_dir):

    key_path  = f"{cache_dir}/consumer.key"
    csr_path  = f"{cache_dir}/consumer.csr"
    cert_path = f"{cache_dir}/consumer.crt"
    pfx_path  = f"{cache_dir}/consumer.pfx"

    subprocess.run(["openssl", "req", "-nodes", "-new", "-keyout", key_path, "-out", csr_path, "-outform", "DER"])

    with open(csr_path, "rb") as f:
        csr = f.read()

    header = {
        "Context-Type": "application/octet-stream"
    }

    cert = requests.post("http://" + ca_addr + "/issue", data=csr, headers=header).text

    with open(cert_path, "w") as f:
        f.write(cert)

    subprocess.run(["openssl", "pkcs12", "-export", "-inkey", key_path, "-in", cert_path, "-out", pfx_path, "-passout", "pass:"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("CA_address")
    parser.add_argument("cache_dir")
    args = parser.parse_args()
    
    get_cert(args.CA_address, args.cache_dir)
