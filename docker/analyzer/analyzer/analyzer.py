import subprocess
import re
import json
from policy import DataProcessingSpec, FunctionSpec
import requests

TEMPLATE_PROGRAM = "/root/template.py"
LIB_FILE = "/root/pysa/plib.py"
FILTER_LIB_FILE = "/root/filter/plib.py"
TARGET_FILE = "/root/pysa/source.py"
MODELED_TARGET_FILE="/root/pysa/target.py"
RESULT_FILE = "/root/pysa/taint-output.json"
FILTER_RESULT_FILE = "/root/filter/taint-output.json"
CONFIG_FILE = "/root/pysa/stubs/taint/general.pysa"
TAINT_CONFIG_FILE = "/root/pysa/stubs/taint/taint.config"

LEAKAGE_CODE = 5001

DATATYPE_API_ENDPOINT = "http://192.168.11.1:8003"

def analyzer(source_code):

    spec_dist = FunctionSpec.get_function_spec()

    ret, args, = check_format(source_code)
    if (ret == 1):
        return 1, None

    ret, func = check_func(spec_dist, TARGET_FILE, "process_data")
    if (ret == 1):
        return 1, None

    config_source_text = ""
    
    all_taint_name_arr = []
    for i, arg in enumerate(args):
        try:
            res = get_schema(arg)
        except RuntimeError:
            return 1, None
        
        taint_name_arr, returnpath_arr = get_taint_name(arg, i, res, "")
        all_taint_name_arr += taint_name_arr
        for j in range(len(taint_name_arr)):
            config_source_text += "def target.get_" + arg + "_" + str(i + 1) + "() -> TaintSource[" + taint_name_arr[j] + ", " + returnpath_arr[j] + "\n"
    
    
    config_sink_text = "def target.process_data() -> TaintSink[DC]: ...\n"
    
    with open(CONFIG_FILE, "w") as f:
        f.write(config_source_text + config_sink_text)
    
    # modify pysa/stubs/taint.config
    template_config = {
        "sources": [
        ],

        "sinks": [
            {
                "name": "DC",
                "comment": "data consumer"
            }
        ],

        "features": [],

        "rules": [
            {
                "name": "Data Linkage",
                "code": LEAKAGE_CODE,
                "sources": [],
                "sinks": [ "DC" ],
                "message_format": "Provided data Leaks"
            }
        ]
    }
    
    for taint_name in all_taint_name_arr:
        template_config["sources"].append(
            {
                "name": taint_name,
                "comment": "Provided data from DPs"
            }
        )
        for i in range(len(template_config["rules"])):
            template_config["rules"][i]["sources"].append(taint_name)
    
    with open(TAINT_CONFIG_FILE, "w") as f:
        json.dump(template_config, f, indent=4)
    
    ret = modeling_app(spec_dist, args)
    if (ret == 1):
        return 1, None
    
    # pysa
    result = subprocess.run(["cd pysa && source ~/.venvs/venv/bin/activate && pyre analyze --save-results-to ./"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, executable="/bin/bash")
    if (result.returncode != 0):
        print("AA")
        return 1, None
    
    issue_info_arr = []
    with open(RESULT_FILE, "r") as f:
        lines = f.readlines()
        for line in lines:
            try:
                loaded_json = json.loads(line)
                if (loaded_json["kind"] == "model" and loaded_json["data"]["callable"] == "source.process_data"):
                    analyzed_res = loaded_json
                elif (loaded_json["kind"] == "issue"):
                    if (loaded_json["data"]["code"] == LEAKAGE_CODE):
                        issue_info_arr.append(loaded_json)
            except Exception:
                continue
    
    input_list = []
    for arg in args:
        input_list.append(arg)
    
    result_sink = []
    try:
        for issue_info in issue_info_arr:
            for trace in issue_info["data"]["traces"]:
                if (trace["name"] == "forward"):
                    for kind in trace["roots"][0]["kinds"]:
                        taint_name = kind["kind"]
                        tmp_sink_name = "_".join(taint_name.split("_")[0:2])
                        for n in taint_name.split("_")[3:]:
                            tmp_sink_name += "." + n
                        result_sink.append(tmp_sink_name)
    except KeyError:
        pass
    
    return 0, DataProcessingSpec(input_list, func, result_sink)

PROCESS_LINE_NUM = 24
END_LINE_NUM = 280

def check_format(source_code):
    
    target_program = read_programfile(source_code=source_code)
    template_program = read_programfile(file_path=TEMPLATE_PROGRAM)
    
    current = 0
    args = []
    
    for line in target_program:
        try:
            if (current == PROCESS_LINE_NUM):
                if (re.match(r"def process_data\(.*\):", line)):
                    args = line.split("(")[1].split(")")[0].replace(" ", "").split(",")
                    # check argument format
                    try:
                        for arg in args:
                            if (not arg.split("_")[1].isdigit()):
                                return 1, args
                    except IndexError:
                        return 1, args
                elif (re.match(r"\treturn.*", line) or re.match(r"    return.*", line)):
                    current = current + 2
                continue

            # check the validity of the source code
            if (line != template_program[current]):
                return 1, args
            else:
                if (current == END_LINE_NUM):
                    return 0, args
                current += 1
        except IndexError:
            return 1, args
    return 1, args

def read_programfile(source_code=None, file_path=None):
    
    if (source_code != None):
        ret = []
        for line in source_code.split("\n"):
            if (re.match("^$", line) or line.isspace()):
                continue
            ret.append(line.replace("\n", ""))
    elif (file_path != None):
        ret = []
        with open(file_path, "r") as f:
            while True:
                line = f.readline()
                if line:
                    if (re.match(" *\n", line)):
                        continue
                    
                    ret.append(line.replace("\n", ""))
                else:
                    break
                
    return ret

def check_func(spec_dist, target_file, specified_func_name):
    result = subprocess.run("code2flow " + target_file + " --include-only-functions " + specified_func_name, shell=True, stderr=subprocess.PIPE, executable="/bin/bash")
    functions = []
    for res in result.stderr.decode().split("\n"):
        if ("Found calls" in res):
            for func in res.split("[")[1].split("]")[0].split(", "):
                func_name = func.replace("\'", "").replace("(", "").replace(")", "")
                if (func_name == ""):
                    return 0, []
                if ('plib.' in func_name):
                    func_name = func_name.replace('plib.', '')
                else:
                    return 1, []
                for spec_func in spec_dist:
                    if (func_name == spec_func):
                        functions.append(func_name)
                        break
                else:
                    return 1, []
    else:
        return 0, functions

def modeling_lib(spec_dist, libfile_path):
    
    modeled_func = ""
    for func_name, func_spec in spec_dist.items():
        modeled_func += "def " + func_spec.function_name + "(" + ", ".join(func_spec.args) +"):" + "\n"
        modeled_ret = []
        for rets in func_spec.returns:
            if (rets == ["None"]):
                modeled_ret.append("".join(rets))
                break
            modeled_func += "    " + "".join(rets) + " = " + " + ".join(rets) + "\n"
            modeled_ret.append("".join(rets))
        modeled_func += "    return " + ", ".join(modeled_ret) + "\n"
    
    with open(TARGET_FILE, "a") as f:
        f.write(modeled_func)

def get_schema(datatype):
    res = requests.get(DATATYPE_API_ENDPOINT + "/schemas/" + datatype.split("_")[0])
    if (res.status_code != 200):
        raise RuntimeError
    return json.loads(res.text)["schema"]

def modeling_app(spec_dist, args):
    modeled_app_code = ""
    
    # dummy data
    var_name_arr = []
    for i, arg in enumerate(args):
        try:
            res = get_schema(arg)
        except RuntimeError:
            return 1
        modeled_app_code += "def get_" + arg + "_" + str(i + 1) + "():\n"
        modeled_app_code += "    return " + json.dumps(res) + "\n"
        modeled_app_code += arg + "_" + str(i + 1) + " = get_" + arg + "_" + str(i + 1) + "()\n\n"
        var_name_arr.append(arg + "_" + str(i + 1))
    
    # define defined function @ DL
    for func_name, func_spec in spec_dist.items():
        modeled_app_code += "def " + func_spec.function_name + "(" + ", ".join(func_spec.args) +"):" + "\n"
        modeled_ret = []
        for rets in func_spec.returns:
            if (rets == ["None"]):
                modeled_ret.append("".join(rets))
                break
            modeled_app_code += "    " + "".join(rets) + " = " + " + ".join(rets) + "\n"
            modeled_ret.append("".join(rets))
        modeled_app_code += "    return " + ", ".join(modeled_ret) + "\n" 
    
    # define process_data from app
    with open(TARGET_FILE, "r") as f:
        lines = f.readlines()
    is_in_func = False
    for line in lines:
        if (re.match(r"def process_data\(.*\):", line)):
            is_in_func = True
            modeled_app_code += line
        elif (re.match(r"\treturn.*", line) or re.match(r"    return.*", line)):
            modeled_app_code += line.replace("plib.", "")
            break
        elif (is_in_func):
            modeled_app_code += line
    
    # invoke data processing
    modeled_app_code += "process_data(" + var_name_arr[0]
    for v in var_name_arr[1:]:
        modeled_app_code += ", " + v
    modeled_app_code += ")\n"
    
    with open(MODELED_TARGET_FILE, "w") as f:
        f.write(modeled_app_code)
    return 0

def get_taint_name(arg_name, index, dict, pkeys):
    taint_name_arr = []
    return_path_arr = []
    
    for k, v in dict.items():
        if (type(v) == type({})):
            if (pkeys == ""):
                arr1, arr2 = get_taint_name(arg_name, index, v, k)
                taint_name_arr += arr1
                return_path_arr += arr2
            else:
                arr1, arr2 = get_taint_name(arg_name, index, v, pkeys + "_" + k)
                taint_name_arr += arr1
                return_path_arr += arr2
        else:
            return_path_keys_str = ""
            attr_name_str = ""
            for pkey in pkeys.split("_"):
                if (pkey == ""):
                    break
                return_path_keys_str += "[\"" + pkey + "\"]"
            return_path_keys_str += "[\"" + k + "\"]"
            
            return_path_arr.append("ReturnPath[_" + return_path_keys_str + "]]: ...")
            
            if (pkeys == ""):
                taint_name_arr.append(arg_name + "_" + str(index + 1) + "_" + k)
            else:
                taint_name_arr.append(arg_name + "_" + str(index + 1) + "_" + pkeys + "_" + k)
    return taint_name_arr, return_path_arr

def main():
    with open("pysa/source.py", "r") as f:
        analyzer(f.read())[1].print_spec()

if __name__ == "__main__":
    main()
