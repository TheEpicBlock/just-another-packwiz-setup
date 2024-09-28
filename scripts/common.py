import json
import os
import shutil
import time
from pathlib import Path
import hashlib
import tomllib
from dataclasses import dataclass
import re

class Ansi:
    BOLD = '\033[1m'
    ITALIC = '\033[3m'
    YELLOW_FG = '\033[33m'
    RED_FG = '\033[31m'
    WARN = YELLOW_FG+BOLD
    ERROR = RED_FG+BOLD
    RESET = '\033[0m'

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

def get_generated_dir():
    dir = env("OUTPUT_DIR", default=(get_repo_root() / "generated"))
    if not dir.exists():
        dir.mkdir(exist_ok=True, parents=True)
    return dir

def read_file(path):
    with open(path, "r") as f:
        return f.read()

def fix_packwiz_pack(pack_toml):
    data = tomllib.loads(read_file(pack_toml))
    index = pack_toml.parent / data["index"]["file"]
    if not index.exists():
        index.touch()

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

def parse_packwiz(pack_toml_file):
    pack_toml = tomllib.loads(read_file(pack_toml_file))
    
    version_data = pack_toml["versions"]
    if not "minecraft" in version_data:
        raise Exception("pack.toml doesn't define a minecraft version")

    # detect loader
    supported_loaders = ["fabric", "neoforge"]
    loaders = {k:v for k, v in version_data.items() if k in supported_loaders}
    if len(loaders) >= 2:
        raise Exception("pack is using multiple loaders, unsure which one to use: ["+", ".join(loaders.keys())+"]")
    if len(loaders) == 0:
        raise Exception("pack does not seem to define a loader")

    loader = list(loaders.keys())[0]
    loader_version = list(loaders.values())[0]

    for v in version_data:
        if v != "minecraft" and v not in supported_loaders:
            raise Exception(f"pack is using unsupported software: {v}")

    return PackwizPackInfo(
        pack_toml.get("name"),
        pack_toml.get("author"),
        pack_toml.get("version"),
        version_data["minecraft"],
        loader,
        loader_version
    )

@dataclass
class PackwizPackInfo:
    name: str
    author: str
    pack_version: str
    minecraft_version: str
    loader: str
    loader_version: str

    def safe_name(self):
        return re.sub("[^a-zA-Z0-9]+", "-", self.name)