# simple util for downloading deployments directly :)

import os
import shutil
import pathlib
import requests
from zipfile import ZipFile
from argparse import ArgumentParser

# args
parser = ArgumentParser(description="Download a complete Roblox version deployment directly from a channel & hash")
parser.add_argument("--channel", type=str, default="LIVE", help="The channel to download from (i.e. \"LIVE\", or a z-channel)")
parser.add_argument("--version", type=str, help="(*) The deployment \"hash\" (e.g. \"version-e28adbc917f34900\")")

args = parser.parse_args()

# yeah the other shit
channel_path = "https://setup.rbxcdn.com" if args.channel == "LIVE" else f"https://setup.rbxcdn.com/{args.channel.lower()}"
version_path = f"{channel_path}/{args.version}-"

folder_path = f"versions/{args.channel}/{args.version}/"
if os.path.exists(folder_path):
    print("[+] Existing folder for current version already downloaded, removing..")
    shutil.rmtree(folder_path)

raw_folder_path = folder_path + "raw/"
extracted_folder_path = folder_path + "extracted/"
os.makedirs(raw_folder_path)
os.makedirs(extracted_folder_path)

# https://github.com/pizzaboxer/bloxstrap/blob/3b9ce6077919f4a93ae11661a4f24d67e86ba8e2/Bloxstrap/Bootstrapper.cs#L36-L63
extract_bindings = {
    "RobloxApp.zip": "",
    "shaders.zip": "shaders/",
    "ssl.zip": "ssl/",

    #"WebView2.zip": "",
    #"WebView2RuntimeInstaller.zip": "WebView2RuntimeInstaller/",

    "content-avatar.zip": "content/avatar/",
    "content-configs.zip": "content/configs/",
    "content-fonts.zip": "content/fonts/",
    "content-sky.zip": "content/sky/",
    "content-sounds.zip": "content/sounds/",
    "content-textures2.zip": "content/textures/",
    "content-models.zip": "content/models/",

    "content-textures3.zip": "PlatformContent/pc/textures/",
    "content-terrain.zip": "PlatformContent/pc/terrain/",
    "content-platform-fonts.zip": "PlatformContent/pc/fonts/",

    "extracontent-luapackages.zip": "ExtraContent/LuaPackages/",
    "extracontent-translations.zip": "ExtraContent/translations/",
    "extracontent-models.zip": "ExtraContent/models/",
    "extracontent-textures.zip": "ExtraContent/textures/",
    "extracontent-places.zip": "ExtraContent/places/",
}

extract_bindings_keys = extract_bindings.keys()

def write_file_path(file_path):
    path = pathlib.Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

# write all zips
session = requests.session()

print("Fetching rbxPkgManifest.. ", end="")
pkg_manifest = session.get(version_path + "rbxPkgManifest.txt").text
print("done!")

# start from line 2 (after the version declare), and every 4 lines after that
for package_name in pkg_manifest.splitlines():
    if not "." in package_name:
        continue

    print(f"Fetching `{package_name}`.. ", end="")

    blob_response = session.get(version_path + package_name)
    blob = blob_response.content

    file_path = folder_path + f"raw/{package_name}"
    with open(file_path, "wb") as file:
        file.write(blob)

    print("done!")

    if not package_name in extract_bindings_keys and package_name.endswith(".zip"):
        print(f"[!] Package name \"{package_name}\" not defined in extract bindings, will skip extraction..")

# now we'll close the session after completion, of course
session.close()

print("-------- Extracting zips --------")
for file_name in os.listdir(raw_folder_path):
    file_path = raw_folder_path + file_name

    if not file_name.endswith(".zip"):
        # can skip and just ins directly
        shutil.copy(file_path, extracted_folder_path)
        continue

    if not file_name in extract_bindings_keys:
        continue

    extract_binding_folder_path = extracted_folder_path + extract_bindings[file_name]

    print(f"Extracting {file_name} contents.. ", end="")

    with ZipFile(file_path, "r") as zip:
        for sub_file_name in zip.namelist():
            if sub_file_name.endswith("\\"):
                # directory!
                continue
            
            # write to extracted..
            with zip.open(sub_file_name, "r") as sub_file:
                extract_path = extract_binding_folder_path + sub_file_name

                write_file_path(extract_path)
                with open(extract_path, "wb") as extracted_file:
                    extracted_file.write(sub_file.read())

    print("done!")
