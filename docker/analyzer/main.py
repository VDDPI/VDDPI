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

    print(f"Received file: {file.filename}, size: {file.size}")
    
    upload_dir = open(UPLOAD_PATH, "wb+")
    shutil.copyfileobj(file.file, upload_dir)
    upload_dir.close()

    with open(UPLOAD_PATH, "r") as f:
        file_content = f.read()
        print(f"File content length: {len(file_content)}")
        print(f"First 100 chars: {file_content[:30]}")
        result, spec = analyzer.analyzer(file_content)
        print(f"Finish analyzer (code:{result})")

    if (result == 0):
        response.status_code = status.HTTP_200_OK
        return {"Result": "OK", "ProcessingSpec": spec.__dict__}
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"Result": "NG", "Error": "Incorrect format."}

@app.post("/update")
async def update(response: Response, lib: bytes = File(...)):

    if not lib:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"Result": "NG", "Error": "file was not sent"}
    with open(PLIB_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(lib.decode())

    response.status_code = status.HTTP_200_OK
    return "Updated"
