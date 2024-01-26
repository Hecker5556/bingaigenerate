# Script in python to generate AI images using bing's free access to Dall E

## How it works
I checked the network tab in the developer tab to see what happens when you're generating something and just converted it to python code, also making sure to get highest quality image (not thumbnail)

## Installation
[python](https://www.python.org/downloads/) (I used 3.10.9)


in cmd

```bash
git clone https://github.com/Hecker5556/bingaigenerate.git
```
```bash
cd bingaigenerate
```
```bash
pip install -r requirements.txt
```

## Usage

```bash
usage: binggenerate.py [-h] [-auth AUTH] [-v] prompt

positional arguments:
  prompt      prompt to use

options:
  -h, --help  show this help message and exit
  -auth AUTH  cookie value (_U) that authenticates requests (mandatory)
  -v          verbose
```
## Python usage

```python
import sys
if "/path/to/bingaigenerate" not in sys.path:
    sys.path.append("/path/to/bingaigenerate")
from bingaigenerate import binggenerate
generator = binggenerate()

#not in async

import asyncio
loop = asyncio.get_event_loop()
filenames = loop.run_until_complete(generator.create("prompt", "authcookie"))

#in async

async def example():
    filenames = await generator.create("prompt", "authcookie")
```

## Authentication

Luckily there is only one cookie value needed to authenticate your requests, and that's the _U cookie, which you can get from using a cookie viewing extension.

Only issue is I haven't tested it enough to know if its a temporary cookie.

## Extra info about bing

- Bing allows at most 3 concurrent image generating processes
- There are many blacklisted prompts, such as famous people and religious stuff (not always)
- Sometimes bing will assume a result is bad, and theres nothing you can really do except change the prompt and experiment