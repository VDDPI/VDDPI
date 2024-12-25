from fastapi import FastAPI, File, Form, Response, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
from datetime import datetime as dt
import os

serverURL = 'http://fablo-rest.' + os.environ['REGISTRY_ID'] + ":8000"

def get_bearerToken(serverURL, id, password):
    headers = {"Authorization": "Bearer"}
    payload = {"id": id, "secret": password}
    res = requests.post(serverURL + "/user/enroll", headers=headers, data=json.dumps(payload))
    return json.loads(res.text)["token"]

def set_headers():
    global HEADERS
    HEADERS = {"Authorization": "Bearer " + get_bearerToken(serverURL, ADMINID, ADMINPW)}

ADMINID = "admin"
ADMINPW = "adminpw"

HEADERS = {"Authorization": "Bearer " + get_bearerToken(serverURL, ADMINID, ADMINPW)}
app = FastAPI(title="Registry API", version="1.0", timeout=180)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register")
async def register(response: Response, program: bytes = File(), SPID: str = Form(), isLinkable: str = Form()):
    
    set_headers()
    
    if (SPID == "" or isLinkable == ""):
        ret = {
            "status": "failed",
            "detail": "Required field is not provided"
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=ret)
        
    # まずUpdateをする
    payload = {
        "method": "UpdateLib",
        "args": []
    }
    
    res = requests.post(serverURL + "/invoke/channel2/chaincode2", headers=HEADERS, data=json.dumps(payload))
    if (res.status_code != 200):
        ret = {
            "status": "failed",
            "detail": "Failed to update library"
        }
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR , content=ret)
    
    # registration
    payload = {
        "method": "RegisterProgram",
        "args": [
            program.decode("utf-8"),
            SPID,
            isLinkable
        ]
    }
    res = requests.post(serverURL + "/invoke/channel1/chaincode1", headers=HEADERS, data=json.dumps(payload))

    if (res.status_code == 200):
        registered_data = json.loads(res.text)["response"]
        
        DPs_feedback = {}
        feedback_res_idx = 3
        while True:
            if ("Output" in registered_data.split("\n")[feedback_res_idx]):
                sent_line = registered_data.split("\n")[feedback_res_idx]
                DPs_feedback["Output(" + sent_line.split("(")[1].split(")")[0] + ")"] = sent_line.split(": ")[1].split(", ")
                feedback_res_idx += 1
            else:
                break
        
        ret = {
            "status": "completed",
            "DataProcessingSpec": {
                "App_ID": registered_data.split("\n")[0].split(": ")[1],
                "Input": registered_data.split("\n")[1].split(": ")[1].split(", "),
                "Output": registered_data.split("\n")[2].split(": ")[1].split(", "),
            }
        }
        ret["DataProcessingSpec"] = dict(**ret["DataProcessingSpec"], **DPs_feedback)
        
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=ret)
    res_text = res.text.split("\n")[1].split("message=")[1]
    if (res_text == "Cannot get MRENCLAVE," or res_text == "A data leak has been detected."):
        ret = {
            "status": "failed",
            "detail": res_text
        }
        return JSONResponse(status_code=status.status.HTTP_400_BAD_REQUEST , content=ret)

    ret = {
        "status": "failed",
        "detail": "Failed to registration: " + res.text
    }
    return JSONResponse(status_code=status.status.HTTP_500_INTERNAL_SERVER_ERROR , content=ret)

@app.get("/spec")
async def get_spec(MRENCLAVE: str, response: Response):
    set_headers()
    
    if (MRENCLAVE == ""):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Required field is not provided"
    
    payload = {
        "method": "GetProcessingSpec",
        "args": [
            MRENCLAVE
        ]
    }
    
    res = requests.post(serverURL + "/invoke/channel1/chaincode1", headers=HEADERS, data=json.dumps(payload))
    if (res.status_code == 200):
        res = json.loads(res.text)["response"]
        ret = {
            "MRENCLAVE": res.get("MRENCLAVE"),
            "DateRegistered": res.get("Date"),
            "Input": res.get("Input"),
            "Output": res.get("Output"),
            "CalledFunctions": res.get("Functions")
        }
        response.status_code = status.HTTP_200_OK
        return ret
    else:
        raise HTTPException(status_code=500, detail="Failed to get policy")

@app.get("/library")
async def get_library(response: Response, Date: str = ""):
    set_headers()
    if (Date == ""):
        payload = {
            "method": "GetCurrentLib",
            "args": []
        }
        res = requests.post(serverURL + "/invoke/channel2/chaincode2", headers=HEADERS, data=json.dumps(payload))
        if (res.status_code == 200):
            response.status_code = status.HTTP_200_OK
            return PlainTextResponse(status_code=status.HTTP_200_OK, content=json.loads(res.text)["response"])
        else:
            raise HTTPException(status_code=500, detail="Failed to get current library")
    else:
        try:
            registered_date = dt.strptime(Date, "%Y-%m-%d %H:%M:%S")
        except:
            raise HTTPException(status_code=400, detail="Required field is not provided")
        
        payload = {
            "method": "ReadSuggestedFunc",
            "args": []
        }
        res = requests.post(serverURL + "/invoke/channel2/chaincode2", headers=HEADERS, data=json.dumps(payload))
        infos = json.loads(res.text)["response"]
        
        ret = ""
        for info in infos:
            if (info["Status"] != "Accepted"):
                continue
            
            if (dt.strptime(info["DateAccepted"], "%Y-%m-%d %H:%M:%S") < registered_date):
                ret = ret + info["Func"]
                
        return PlainTextResponse(status_code=status.HTTP_200_OK, content=ret)
