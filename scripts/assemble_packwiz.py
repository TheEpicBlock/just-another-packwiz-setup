import shutil
import json
import common
import os
import subprocess
import re
import tomli_w

def main():
    repo_root = common.get_repo_root()
    submission_lock_file = repo_root / "submissions-lock.json"
    source_pack = repo_root / "pack"
    dest_pack = repo_root / "pack_generated"
    exclude_file = repo_root / "platform.ignore"
    packwiz = common.check_packwiz()

    common.fix_packwiz_pack(source_pack / "pack.toml")

    if dest_pack.exists():
        shutil.rmtree(dest_pack)
    shutil.copytree(source_pack, dest_pack)
    common.fix_packwiz_pack(dest_pack / "pack.toml")

    exclusions = list(filter(lambda l : len(l) > 0, [re.sub("#.*", "", l.strip()) for l in common.read_file(exclude_file).split("\n")]))

    locked_data = json.loads(common.read_file(submission_lock_file))
    for platformid, moddata in locked_data.items():
        if not "files" in moddata:
            raise RuntimeError(f"lock data for {platformid} is invalid. Does not contain file key")
        
        if platformid in exclusions:
            print(f"skipping {platformid}")
            continue

        for filename, filedata in moddata["files"].items():
            dst_file = dest_pack / "mods" / filename
            if not dst_file.exists():
                # We want all mods to be on both sides for singleplayer compat
                filedata["side"] = "both"
                with open(dst_file, "w") as f:
                    f.write(tomli_w.dumps(filedata))

    for e in exclusions:
        if not e in locked_data:
            raise Exception(f"{e} was given as an exclusion, but does not actually appear in the submission data. Was it a typo?")

    os.chdir(dest_pack)
    subprocess.run([packwiz, "refresh"])

if __name__ == "__main__":
    main()