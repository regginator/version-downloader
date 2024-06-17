# version-downloader

Simple Python Script to Directly Download & Extract a Complete, Specific `WindowsPlayer`/`WindowsStudio` Roblox Deployment

## Usage

1. Clone the Repository

```sh
git clone https://github.com/regginator/version-downloader.git
cd version-downloader
```

2. Install requirements ([`aiohttp`](https://pypi.org/project/aiohttp)) via `pip`:

```sh
pip install -r requirements.txt
```

3. Run `main.py`

```txt
$ python3 main.py --help
usage: main.py [-h] [--channel CHANNEL] [--version VERSION] [--host HOST] [--ignore-manifest] [--is-player] [--is-studio]

Download a complete Roblox WindowsPlayer/WindowsStudio deployment directly from a channel & hash

options:
  -h, --help            show this help message and exit
  --channel CHANNEL, -c CHANNEL
                        The channel to download from (i.e. "LIVE", or a z-channel)
  --version VERSION, -v VERSION
                        (*) The deployment "hash" (e.g. "version-e28adbc917f34900")
  --host HOST           (*) The setup S3 bucket host (e.g. "https://setup.rbxcdn.com")
  --ignore-manifest
  --is-player
  --is-studio
```

*Downloaded versions will be stored in `./versions/{channel-name}/{version-hash}`*
