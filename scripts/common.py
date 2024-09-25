import json
import os
import shutil
import time
from pathlib import Path
import hashlib

def check_packwiz():
    packwiz = env("PACKWIZ", default="packwiz")
    if p := shutil.which(packwiz):
        return p
    else:
        raise RuntimeError(f"!!! Couldn't find packwiz (looked for '{packwiz}'). Please put packwiz on your path or set the PACKWIZ environment variable to a packwiz executable")

def check_java():
    java = "java"
    if "JAVA_HOME" in os.environ:
        java = Path(os.environ["JAVA_HOME"]) / "bin/java"
        if not java.exists():
            raise RuntimeError(f"!!! JAVA_HOME is invalid. {java} does not exist")
        return java
    else:
        if java := shutil.which("java"):
            return p
        else:
            raise RuntimeError(f"!!! Couldn't find java on path. Please add it or set JAVA_HOME")


def get_repo_root():
    # This file should be located in <repo_root>/scripts/common.py, so the root
    # is one directory up from this one
    return Path(os.path.join(os.path.dirname(__file__), '..'))

def read_file(path):
    with open(path, "r") as f:
        return f.read()

class JSONWithCommentsDecoder(json.JSONDecoder):
    def __init__(self, **kw):
        super().__init__(**kw)

    def decode(self, s: str):
        s = '\n'.join(l if not l.lstrip().startswith('//') else '' for l in s.split('\n'))
        return super().decode(s)

def jsonc_at_home(input):
    return json.loads(input, cls=JSONWithCommentsDecoder)

def hash(values: list[str]):
    hasher = hashlib.sha256()
    for value in values:
        hasher.update(value.encode("UTF-8"))
    return hasher.hexdigest()

def env(env: str, **kwargs):
    if env in os.environ:
        return os.environ[env]
    else:
        return kwargs.get("default")

class Ratelimiter:
    def __init__(self, time):
        # Time is given in seconds, convert to nanoseconds
        self.wait_time = time
        self.last_action = 0
    
    def limit(self):
        time.sleep(max(0, self.wait_time - (time.time() - self.last_action)))
        self.last_action = time.time()