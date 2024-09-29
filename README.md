# Generic packwiz setup

## Repository setup
Please create an (empty) `pack/index.toml`.
This will ensure packwiz commands work correctly in the `pack/` directory. `tomli_w` is the only dependency needed to run the scripts.

The `pack/` directory contains the bulk of the pack. The files in here can be updated using the [packwiz](https://github.com/packwiz/packwiz) utility. The final pack will also include all submissions (and their dependencies), which are pulled from ModFest's platform api. The `pack/` directory will always take priority and can be used to override submitted mods. Submissions can be excluded altogether by putting it in the `platform.ignore` file.

Submissions are version locked using the `submission-lock.json` file. Run `scripts/pull_platform.py` to pull the latest versions from platform. This script can also be run via a manually-triggered github action.

## Compiling the final pack
Run `scripts/assemble_packwiz.py`. It will output a full packwiz pack in `generated/pack/`.

## Creating auto-updating packs
Running `scripts/assemble_unsup.py` will create two zip files in the `generated` directory.
The file without a suffix can be put loaded into prism launcher.
The `-server.zip` file contains files needed to run a server. For Fabric it will contain a full server instance. For NeoForge you should run the server installer yourself and copy these files over top.