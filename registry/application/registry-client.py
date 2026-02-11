import argparse
import requests
import json
import re

ADMINID = "admin"
ADMINPW = "adminpw"

URL = ["http://localhost:8801", "http://localhost:8802", "http://localhost:8803"]

CHANNEL_CC = {"channel1": "chaincode1", "channel2": "chaincode2"}

CC = [
    {
        "register": "RegisterProgram",
        "get": "GetProgramInfo",
        "getAll": "GetAllProgramInfo"
    }, 
    {
        "RegisterID": "RegisterID", 
        "propose": "ProposeFunc",
        "vote": "Vote",
        "update": "UpdateLib",
        "getLib": "GetCurrentLib",
        "getProposed": "ReadProposedFunc"
    }
]

CC_INFO = {
    "RegisterProgram": [
        "program path",
        "SPID",
        "isLinkable"
    ],
    "GetProgramInfo": [
        "MRENCLAVE"
    ],
    "GetAllProgramInfo": [],
    "RegisterID": [],
    "ProposeFunc": [
        "func name",
        "program path",
    ],
    "Vote": [
        "func name",
        "accept?",
    ],
    "UpdateLib":[],
    "GetCurrentLib":[],
    "ReadProposedFunc": []
}

def main():
    parser = argparse.ArgumentParser(description="Fablo-REST client")

    parser.add_argument("registry", help="registry info Ex.) 1")
    parser.add_argument("user_id", help="user_id")
    parser.add_argument("user_password", help="user_password")
    parser.add_argument("-f", help="file", default="./test.txt")
    parser.add_argument("-r", help="register user info", action="store_true")
    parser.add_argument("-i", help="interactive mode", action="store_true")


    args = parser.parse_args()
    
    serverURL = URL[int(args.registry) - 1]
    
    
    if (args.r):
        token = get_bearerToken(serverURL, ADMINID, ADMINPW)
        register_user(serverURL, token, args.user_id, args.user_password)
    else:
        token = get_bearerToken(serverURL, args.user_id, args.user_password)
        if (args.i):
            interactive_client(serverURL, token)
        else:
            client(serverURL, token, args.f)

def register_user(serverURL, token, user_id, user_password):

    headers = {"Authorization": "Bearer " + token}
    payload = {"id": user_id, "secret": user_password}
    res = requests.post(serverURL + "/user/register", headers=headers, data=json.dumps(payload))
    if (res.status_code == 201):
        print("Registration Success")
    else:
        print("Registration Failed: %s\n" % res.text)

def interactive_client(serverURL, token):
    
    while True:
        channel = input("Channel (channel1/channel2): ")
        try:
            chaincode = CHANNEL_CC[channel]
        except Exception as e:
            print(e)
            print("Invalid channel: %s" % channel)
            continue

        if (channel == "channel1"):
            CC_index = 0
        else:
            CC_index = 1

        print("methods: [%s]" % ", ".join(CC[CC_index].keys()))
        method = CC[CC_index][input("method: ")]

        if (method == "RegisterProgram"):
            update_lib(serverURL, token)
        
        args = []
        for arg in CC_INFO[method]:
            tmp = input(arg + ": ")
            
            if (arg == "program path"):
                with open(tmp, "r") as f:
                    args.append(f.read())
            else:
                args.append(tmp)
            
        headers = {"Authorization": "Bearer " + token}
        payload = {
            "method": method,
            "args": args
        }
        res = requests.post(serverURL + "/invoke/" + channel + "/" + chaincode, headers=headers, data=json.dumps(payload))
        if (res.status_code == 200):
            print("Invoke Success")

            if (method == "GetProgramInfo"):
                print("========================")
                print("MRENCLAVE: %s" % json.loads(res.text)["response"]["MRENCLAVE"])
                print("Date: %s" % json.loads(res.text)["response"]["Date"])
                print("Objective: %s" % json.loads(res.text)["response"]["Objective"])
                print("========================")
            elif (method == "GetAllProgramInfo"):
                print("========================")
                for info in json.loads(res.text)["response"]:
                    print("MRENCLAVE: %s" % info["MRENCLAVE"])
                    print("Date: %s" % info["Date"])
                    print("Objective: %s" % info["Objective"])
                    print("========================")
            elif (method == "Vote"):
                print("Current %s %s" % (args[0], json.loads(res.text)["response"]), end="")
            elif (method == "GetCurrentLib"):
                print("======Valid plib.py=====")
                print(json.loads(res.text)["response"], end="")
                print("========================")
            elif (method == "ReadProposedFunc"):
                res = json.loads(res.text)["response"]
                print("========================")
                for func_info in res:
                    print("Function:\n %s" %  func_info["Func"])
                    print("Date: %s" % func_info["Date"])
                    print("Status: %s" % func_info["Status"])
                    if (func_info["Status"] == "Accepted"):
                        print("DateAccepted: %s" % func_info["DateAccepted"])
                    print("(%s)" % func_info["IsApproved"])
                    print("========================")
            else:
                print("Response: %s" % json.loads(res.text)["response"])
        else:
            print("Invoke Failed: %s" % res.text)
        print()
        if (input("exit?: ")):
            print()
            break


def client(serverURL, token, file_path):

    headers = {"Authorization": "Bearer " + token}

    with open(file_path, "r") as f:
        for line in f:
            line = line[:-1]
            channel = line.split(" ")[0]
            chaincode = line.split(" ")[1]
            method = line.split(" ")[2]
            args = []
            try:
                index = 3
                while True:
                    if (re.match(r".+\.py", line.split(" ")[index])):
                        with open(line.split(" ")[index], "r") as f:
                            args.append(f.read())
                    else:
                        args.append(line.split(" ")[index])
                    index = index + 1
            except:
                pass
            payload = {
                "method": method,
                "args": args
            }
            res = requests.post(serverURL + "/invoke/" + channel + "/" + chaincode, headers=headers, data=json.dumps(payload))
            if (res.status_code != 200):
                print("Invoke Falied: %s: %s" % (line, res.text))
                exit(1)
    print("Success")

def get_bearerToken(serverURL, id, password):
    headers = {"Authorization": "Bearer"}
    payload = {"id": id, "secret": password}
    res = requests.post(serverURL + "/user/enroll", headers=headers, data=json.dumps(payload))
    return json.loads(res.text)["token"]

def update_lib(serverURL, token):
    headers = {"Authorization": "Bearer " + token}
    payload = {
        "method": "UpdateLib",
        "args": []
    }
    res = requests.post(serverURL + "/invoke/channel2/chaincode2", headers=headers, data=json.dumps(payload))
    if (res.status_code == 200):
        print("Library file update success")
    else:
        print("Library file update Falied")
        exit(1)


if __name__ == "__main__":
    main()
