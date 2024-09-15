import tomllib
import os
import urllib.request
import subprocess
from pathlib import Path

import common

def main():
    repo_root = common.get_repo_root()
    pack = repo_root / "pack_generated"
    pack_toml_file = pack / "pack.toml"
    test_server_working = Path(common.env("WORK_DIR", default=(repo_root / "run")))

    if not pack.exists():
        print(f"{pack} does not exist")
        raise Exception("Error, couldn't find pack. Please ensure that it was created (run assemble_packwiz.py)")
    if not pack_toml_file.exists():
        print(f"{pack_toml_file} does not exist")
        raise Exception("Pack is not a valid packwiz pack (pack.toml) doesn't exist")
    
    # Parse pack information

    pack_toml = tomllib.loads(common.read_file(pack_toml_file))

    print("Testing modpack "+str(pack_toml.get("name"))+" "+str(pack_toml.get("version")))

    version_data = pack_toml["versions"]
    if not "minecraft" in version_data:
        raise Exception("pack.toml doesn't define a minecraft version")
            
    mc_version = version_data["minecraft"]

    # detect loader
    supported_loaders = ["fabric", "neoforge"]

    for v in version_data:
        if v != "minecraft" and v not in supported_loaders:
            raise Exception(f"pack is using unsupported software: {v}")

    loaders = {k:v for k, v in version_data.items() if k in supported_loaders}
    if len(loaders) >= 2:
        raise Exception("pack is using multiple loaders, unsure which one to use: ["+", ".join(loaders.keys())+"]")
    if len(loaders) == 0:
        raise Exception("pack does not seem to define a loader")
    
    loader = list(loaders.keys())[0]
    loader_version = list(loaders.values())[0]

    print(f"Setting up a {loader} ({loader_version}) server")

    # Set up modloader
    server_hash = common.hash([mc_version, loader, loader_version])
    minecraft_dir = test_server_working / "loader" / server_hash
    minecraft_cached = minecraft_dir.exists()
    server_run_cmd = None
    if loader == "fabric":
        server_jar = minecraft_dir / "server.jar"
        if not minecraft_cached:
            print("Download fabric server jar")
            minecraft_dir.mkdir(exist_ok=True, parents=True)
            fabric_installer = "1.0.1"
            urllib.request.urlretrieve(f"https://meta.fabricmc.net/v2/versions/loader/{mc_version}/{loader_version}/{fabric_installer}/server/jar", server_jar)
        server_run_cmd = ["java", "-jar", server_jar]
    elif loader == "neoforge":
        installer_file = minecraft_dir / f"installer.jar"
        if not minecraft_cached:
            print("! Running neoforge installer")
            minecraft_dir.mkdir(exist_ok=True, parents=True)
            urllib.request.urlretrieve(f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{loader_version}/neoforge-{loader_version}-installer.jar", installer_file)
            subprocess.run(["java", "-jar", installer_file, "--install-server", minecraft_dir])
            print("! Neoforge installer ran")
        server_run_cmd = [minecraft_dir / ("run.bat" if os.name == "nt" else "run.sh")]
    else:
        raise RuntimeError(f"{loader} not handled")
    
    # Accept eula
    with open(minecraft_dir / "eula.txt", "w") as f:
        f.write("eula=true")

    # Set up the packwiz and game dir
    packwiz_dir = test_server_working / "packwiz-installer"
    game_dir = test_server_working / "game"
    packwiz_bootstrap = packwiz_dir / "packwiz-bootstrap.jar"
    if not packwiz_bootstrap.exists():
        print("Installing packwiz bootstrap")
        bootstrap_version = common.env("PACKWIZ_BOOTSTRAP_VERSION", default="v0.0.3")
        packwiz_dir.mkdir(exist_ok=True)
        urllib.request.urlretrieve(f"https://github.com/packwiz/packwiz-installer-bootstrap/releases/download/{bootstrap_version}/packwiz-installer-bootstrap.jar", packwiz_bootstrap)
    subprocess.run([
        "java", "-jar", packwiz_bootstrap,
        "--no-gui",
        # Ensures bootstrap installs packwiz to `packwiz_dir` for caching reasons
        "--bootstrap-main-jar", packwiz_dir / "packwiz-installer.jar",
        "--pack-folder", game_dir,
        f"file://{pack_toml_file}"
    ])

    # Run the server
    worlds_dir = test_server_working / "worlds"
    os.chdir(minecraft_dir) # mc misbehaves unless the pwd matches this. NeoForge refuses to run and Fabric will dump a bunch of files here
    subprocess.run(server_run_cmd + ["--universe", worlds_dir, "--gameDir", game_dir, "--no-gui"])

if __name__ == "__main__":
    main()