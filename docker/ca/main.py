from flask import Flask, request
import subprocess
import requests
import ipaddress

OPENSSL_CONF = "/etc/ssl/openssl.cnf"
CAROOT_CRT = "/etc/ssl/CA/cacert.pem"
SAN_FILE = "./san.txt"

app = Flask(__name__)

def format_san_entry(san):
    """Convert SAN value to appropriate IP or DNS format string"""
    try:
        ipaddress.ip_address(san)
        return "IP:" + san
    except ValueError:
        return "DNS:" + san

@app.route("/issue", methods=["POST"])
def issue():
    
    pem_csr = request.data
    
    try:
        san_data = request.args["san"]

        with open(SAN_FILE, "w") as f:
            f.write("subjectAltName = " + format_san_entry(san_data) + "\n")
        
        with open("tmp.csr", "wb") as f:
            f.write(pem_csr)
        subprocess.run(["openssl", "ca", "-batch", "-key", "test", "-inform", "DER", "-in", "tmp.csr", "-out", "tmp_pem.crt", "-extfile", SAN_FILE, "-config", OPENSSL_CONF])

    except:
        with open("tmp.csr", "wb") as f:
            f.write(pem_csr)
        subprocess.run(["openssl", "ca", "-batch", "-key", "test", "-inform", "DER", "-in", "tmp.csr", "-out", "tmp_pem.crt", "-config", OPENSSL_CONF])

    with open("tmp_pem.crt", "r") as f:
        cert = f.read()
        subprocess.run(["rm", "tmp.csr", "tmp_pem.crt"])
        return "-----BEGIN CERTIFICATE-----" + cert.split("-----BEGIN CERTIFICATE-----")[1]

@app.route("/root-crt", methods=["GET"])
def send_root_crt():
    with open(CAROOT_CRT, "r") as f:
        return f.read()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
