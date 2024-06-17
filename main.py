# Simple Python Script to Directly Download & Extract a Complete, Specific WindowsPlayer/WindowsStudio Roblox Deployment

import os
import sys
import shutil
import aiohttp
import asyncio
import pathlib
import requests
from io import BytesIO
from zipfile import ZipFile
from argparse import ArgumentParser

parser = ArgumentParser(description="Download a complete Roblox WindowsPlayer/WindowsStudio deployment directly from a channel & hash")
parser.add_argument("--channel", "-c", default="LIVE", help="The channel to download from (i.e. \"LIVE\", or a z-channel)")
parser.add_argument("--version", "-v", help="(*) The deployment \"hash\" (e.g. \"version-e28adbc917f34900\")")
parser.add_argument("--host", default="https://setup.rbxcdn.com", help="(*) The setup S3 bucket host (e.g. \"https://setup.rbxcdn.com\")")
parser.add_argument("--ignore-manifest", action="store_true")
parser.add_argument("--is-player", action="store_true")
parser.add_argument("--is-studio", action="store_true")

args = parser.parse_args()

host = args.host
ignore_manifest = args.ignore_manifest

channel_path = host if args.channel == "LIVE" else f"{host}/channel/{args.channel.lower()}"
version_path = f"{channel_path}/{args.version}-"

# https://github.com/pizzaboxer/bloxstrap/blob/3b9ce6077919f4a93ae11661a4f24d67e86ba8e2/Bloxstrap/Bootstrapper.cs#L36-L63
player_extract_roots = {
    "RobloxApp.zip": "",
    "shaders.zip": "shaders/",
    "ssl.zip": "ssl/",

    "WebView2.zip": "",
    "WebView2RuntimeInstaller.zip": "WebView2RuntimeInstaller/",

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

# https://github.com/MaximumADHD/Roblox-Studio-Mod-Manager/blob/main/Config/KnownRoots.json
studio_extract_roots = {
    "RobloxStudio.zip": "",
    "redist.zip": "",
    "Libraries.zip": "",
    "LibrariesQt5.zip": "",

    "WebView2.zip": "",
    "WebView2RuntimeInstaller.zip": "",

    "shaders.zip": "shaders/",
    "ssl.zip": "ssl/",

    "Qml.zip": "Qml/",
    "Plugins.zip": "Plugins/",
    "StudioFonts.zip": "StudioFonts/",
    "BuiltInPlugins.zip": "BuiltInPlugins/",
    "ApplicationConfig.zip": "ApplicationConfig/",
    "BuiltInStandalonePlugins.zip": "BuiltInStandalonePlugins/",

    "content-qt_translations.zip": "content/qt_translations/",
    "content-sky.zip": "content/sky/",
    "content-fonts.zip": "content/fonts/",
    "content-avatar.zip": "content/avatar/",
    "content-models.zip": "content/models/",
    "content-sounds.zip": "content/sounds/",
    "content-configs.zip": "content/configs/",
    "content-api-docs.zip": "content/api_docs/",
    "content-textures2.zip": "content/textures/",
    "content-studio_svg_textures.zip": "content/studio_svg_textures/",

    "content-platform-fonts.zip": "PlatformContent/pc/fonts/",
    "content-terrain.zip": "PlatformContent/pc/terrain/",
    "content-textures3.zip": "PlatformContent/pc/textures/",

    "extracontent-translations.zip": "ExtraContent/translations/",
    "extracontent-luapackages.zip": "ExtraContent/LuaPackages/",
    "extracontent-textures.zip": "ExtraContent/textures/",
    "extracontent-scripts.zip": "ExtraContent/scripts/",
    "extracontent-models.zip": "ExtraContent/models/",
}

def write_full_path(file_path):
    path = pathlib.Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

# write all zips
if not ignore_manifest:
    print("Fetching rbxPkgManifest.. ", end="")
    pkg_manifest = requests.get(version_path + "rbxPkgManifest.txt").text
    pkg_manifest_lines = pkg_manifest.splitlines()
    print("done!")

    # decide the `extract_roots` to use
    if "RobloxApp.zip" in pkg_manifest_lines:
        extract_roots = player_extract_roots
        binary_type = "WindowsPlayer"
    elif "RobloxStudio.zip" in pkg_manifest_lines:
        extract_roots = studio_extract_roots
        binary_type = "WindowsStudio"
    else:
        print("[!] Bad manifest given, exitting..")
        sys.exit(1)
elif args.is_player:
    extract_roots = player_extract_roots
    binary_type = "WindowsPlayer"
elif args.is_studio:
    extract_roots = studio_extract_roots
    binary_type = "WindowsStudio"
else:
    print("--ignore-manifest true, but neither --is-player or --is-studio provided", file=sys.stderr)
    sys.exit(1)

extract_binding_keys = extract_roots.keys()

print(f"Fetching blobs for BinaryType `{binary_type}`..")

folder_path = f"versions/{args.channel}/{binary_type}/{args.version}/"
if os.path.exists(folder_path):
    print("[+] Existing folder for current version already downloaded, removing..")
    shutil.rmtree(folder_path)

os.makedirs(folder_path)

# lol
with open(folder_path + "AppSettings.xml", "w") as file:
    file.write("""<?xml version="1.0" encoding="UTF-8"?>
<Settings>
    <ContentFolder>content</ContentFolder>
    <BaseUrl>http://www.roblox.com</BaseUrl>
</Settings>
""")

async def download_package(package_name, session):
    print(f"Fetching `{package_name}`.. ")
    blob_url = version_path + package_name

    async with session.get(blob_url, timeout=9e9) as response:
        if response.status != 200:
            print(f"[X] Failed to fetch blob ({response.status}) @ {blob_url}")
            return

        blob = await response.content.read() # Will use the byte stream ret with `ZipFile()` directly
        print(f"`{package_name}` received!")

    #if not package_name.endswith(".zip"):
    #    # can skip and just add directly
    #    with open(folder_path + package_name, "wb") as file:
    #        file.write(blob)

    #    return

    #if not package_name in extract_binding_keys:
    #    print(f"[!] Package name \"{package_name}\" not defined in extract bindings, will skip extraction..")
    #    return

    print(f"Extracting {package_name}.. ")
    extract_binding_folder_path = folder_path + extract_roots[package_name]

    with ZipFile(BytesIO(blob), "r") as archive:
        for sub_file_name in archive.namelist():
            sub_file_path = sub_file_name.replace("\\", "/")
            extract_path = extract_binding_folder_path + sub_file_path

            if sub_file_path.endswith("/"):
                # directory!
                os.makedirs(extract_path, exist_ok=True)
                continue

            # write to extracted..
            with archive.open(sub_file_name, "r") as sub_file:
                write_full_path(extract_path)
                with open(extract_path, "wb") as extracted_file:
                    extracted_file.write(sub_file.read())
    
    print(f"{package_name} extracted!")

async def main():
    connector = aiohttp.TCPConnector(limit=None)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []

        for package_name in extract_binding_keys:
            if not "." in package_name:
                continue
            
            task = asyncio.ensure_future(download_package(package_name, session))
            tasks.append(task)

        # wait for all tasks to finish before exitting session context
        await asyncio.gather(*tasks)

asyncio.run(main())
