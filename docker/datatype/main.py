from fastapi import FastAPI, File, Form, Response, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
import json

app = FastAPI(title="DataType-API", version="1.0", timeout=180)

@app.get("/schemas/{type}")
async def get_type(type):
    try:
        with open("schemas/" + type + ".json", "r") as f:
            return JSONResponse(status_code=status.HTTP_200_OK, content=json.load(f))
    except FileNotFoundError:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={})
