from fastapi import FastAPI, File, UploadFile, status, Response
import shutil
import analyzer

app = FastAPI()

UPLOAD_PATH = "/root/pysa/source.py"
PLIB_PATH = "/root/pysa/plib.py"

@app.post("/verify")
async def verify(response: Response, file: UploadFile = File(...)):
    if not file:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"Result": "NG", "Error": "file was not sent"}
    
    upload_dir = open(UPLOAD_PATH, "wb+")
    shutil.copyfileobj(file.file, upload_dir)
    upload_dir.close()

    with open(UPLOAD_PATH, "r") as f:
        result, spec = analyzer.analyzer(f.read())
    if (result == 1):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"Result": "NG", "Error": "Incorrect format."}
    else:
        response.status_code = status.HTTP_200_OK
        return {"Result": "OK", "ProcessingSpec": spec.__dict__}

@app.post("/update")
async def update(response: Response, lib: bytes = File(...)):

    if not lib:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"Result": "NG", "Error": "file was not sent"}
    with open(PLIB_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(lib.decode())

    response.status_code = status.HTTP_200_OK
    return "Updated"
