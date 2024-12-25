import json
import re

PLIB_PATH = "/root/pysa/plib.py"

class FunctionSpec:
    
    def __init__(self, function_name, args, ret):
        self.function_name = function_name
        self.args = args
        self.returns = ret
    
    def __set_returns(self):
        self.returns = ("arg1",)

    @classmethod
    def get_function_spec(cls):
        with open(PLIB_PATH, "r") as f:
            lib_file = f.read()
        
        spec_list = {}
        prev_line = ""
        for line in lib_file.split("\n"):
            if (re.match(r"def .+", line)):
                func_name = line.split("def ")[1].split("(")[0]
                spec_arg = line.split("def ")[1].split("(")[1].split(")")[0].split(", ")
                spec_ret = []
                try:
                    for ret in prev_line.split(": ")[1].split(", "):
                        if (ret == ""):
                            spec_ret.append(["None"])
                        else:
                            spec_ret.append(ret.split("/"))
                except IndexError:
                    spec_ret.append(["None"])
                spec_list[func_name] = FunctionSpec(func_name, spec_arg, spec_ret)
            else:
                prev_line = line
                continue
        
        return spec_list

class DataProcessingSpec:
    
    def __init__(self, input, function, output):
        self.Input = input
        self.Functions = function
        self.Output = output
    
    def print_spec(self):
        
        print("=" * 50)
        print("Input: {}".format(", ".join(self.Input)))
        print("Functions: {}".format(", ".join(self.Functions)))
        print("Output: {}".format(", ".join(self.Output)))
        print("=" * 50)

    def to_json(self):
        return json.dumps(self.__dict__)


