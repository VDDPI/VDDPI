from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import ssl
import time

class Address(BaseModel):
    address: str

app = FastAPI()

@app.get("/time")
async def get_time():
    
    time.sleep(0.1)

    return JSONResponse({
        "abbreviation": "JST",
        "datetime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+09:00"),
        "timezone": "Asia/Tokyo"
    })

@app.post("/location")
async def get_location(addr: Address):
    
    time.sleep(0.1)
    
    return JSONResponse({
        "status": "success",
        "country": "Japan",
        "countryCode": "JP",
        "region": "23",
        "regionName": "Aichi",
        "city":"Nagoya",
        "zip":"462-0841",
        "lat":35.1926,
        "lon":136.906,
        "timezone":"Asia/Tokyo"
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80, log_level="debug")
