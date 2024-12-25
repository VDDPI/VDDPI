import requests
import argparse

PLIB_FILE = "./code/plib.py"

def main(reg_url):
    res = requests.get(reg_url + "/library")
    if (res.status_code != 200):
        raise RuntimeError("Failed to get plib: " + res.text)
    
    with open(PLIB_FILE, "w") as f:
        f.write(res.text.replace("\\n", "\n").replace("\\", ""))
    print("Library file updated!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("reg_addr")
    main(parser.parse_args().reg_addr)
