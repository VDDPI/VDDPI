from fastapi import FastAPI,Response, HTTPException, status
import json
from datetime import datetime as dt
from pydantic import BaseModel
import random
import time
import base64
import urllib.parse
from Cryptodome.Signature import PKCS1_v1_5
from Cryptodome.Hash import SHA256
from Cryptodome.PublicKey import RSA
from Cryptodome import Random

app = FastAPI(title="Psuedo Attesation Service", version="1.0", timeout=180)

with open("sign.crt", "r") as f:
    SIGN_CERT = f.read()
with open("signCA.crt", "r") as f:
    SIGNCA_CERT = f.read()
with open("sign.key", "rb") as f:
    SIGN_KEY = RSA.import_key(f.read())

class Body(BaseModel):
    isvEnclaveQuote: str


@app.post("/sgx/dev/attestation/v4/report")
async def get_report(response: Response, body: Body):
    if (body.isvEnclaveQuote == ""):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Attestation Evidence Payload.")
    
    time.sleep(0.1)
    
    isvEnclaveQuote = base64.b64decode(body.isvEnclaveQuote)
    
    res = {
        "id": str(random.randint(10000000000000000000000000000000000000, 100000000000000000000000000000000000000 - 1)),
        "timestamp": dt.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
        "version": 4,
        "advisoryURL": "htts://security-center.intel.com",
        "advisoryIDs": ["INTEL-SA-00219","INTEL-SA-00289","INTEL-SA-00334","INTEL-SA-00381","INTEL-SA-00389","INTEL-SA-00477","INTEL-SA-00614","INTEL-SA-00615","INTEL-SA-00617","INTEL-SA-00828"],
        "isvEnclaveQuoteStatus": "OK",
        "isvEnclaveQuoteBody": base64.b64encode(isvEnclaveQuote[:432]).decode("utf-8")
    }
    
    sig = PKCS1_v1_5.new(SIGN_KEY).sign(SHA256.new(json.dumps(res).encode()))

    response.headers["Request-ID"] = hex(random.randint(16 ** 31, 16 ** 32 - 1))[2:]
    response.headers["X-IASReport-Signature"] = base64.b64encode(sig).decode("utf-8")
    response.headers["X-IASReport-Signing-Certificate"] = urllib.parse.quote(SIGN_CERT + SIGNCA_CERT)
    response.headers["Date"] = dt.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    
    return res

@app.get("/root-crt")
async def get_cert():
    return {
        "root-crt": SIGNCA_CERT
    }
