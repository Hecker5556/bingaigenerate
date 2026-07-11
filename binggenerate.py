from curl_cffi.requests import AsyncSession, Response
from curl_cffi import CurlMime
import asyncio
import aiofiles
import traceback
import json
import time
from typing import Literal
import logging
import os
import mimetypes
import re
from html import unescape
from base64 import b64encode

logger = logging.getLogger(__name__)
if logger.hasHandlers() is False:
    logger.addHandler(logging.NullHandler())

class binggenerate:
    def __init__(self, _U: str, _EDGE_S: str, session: AsyncSession = None, proxy: str = None):
        self.cookies = {
            'BCP': 'AD=0&AL=0&SM=0',
            '_U': _U,
            "_EDGE_S": _EDGE_S,
            'SRCHHPGUSR': 'SRCHLANG=en&PREFCOL=1&BRW=XW&BRH=M&CW=1472&CH=750&SCW=1457&SCH=3078&DPR=1.3&UTC=120&PV=10.0.0&B=0&HV=1783195967&HVE=CfDJ8A8rLfEh4ZdMhJ19YNJ4FtRXMNK7FYmRnkLfHYQ5olz6dJR1osLRF_5vDR_WS7ldj6ajYyZAoB-p9lnzU18qftrYDW7GDvPHUrEnBHsYZlvi7qOHz3ibzaF4gjXg2-cQOp4BXPNJDzZeXb1SDfgvrgzdbV8whRt8QZ-9RUs9ywMN2CODc_H879n15ZYmJFz_UQ&WEBTHEME=1&PRVCW=1472&PRVCH=750&EXLTT=5',
        }
        self.session = session
        self.proxy = proxy
        self._closeSession = None
    async def __aenter__(self):
        if (self.session is None):
            self.session = AsyncSession(proxies=self.proxy, impersonate="chrome")
            self._closeSession = True
        return self
    async def __aexit__(self, exc, extype, tb):
        if (exc):
            traceback.print_exception(exc, extype, tb)
        if (self._closeSession):
            await self.session.close()
    async def upload(self, pathToFile: str):
        if not os.path.exists(pathToFile):
            raise FileNotFoundError("Couldnt find provided file: " + pathToFile)
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.8',
            'origin': 'https://www.bing.com',
            'priority': 'u=1, i',
            'referer': 'https://www.bing.com/images/create/ai-image-generator?toWww=1',
            'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Brave";v="150"',
            'sec-ch-ua-arch': '"x86"',
            'sec-ch-ua-bitness': '"64"',
            'sec-ch-ua-full-version-list': '"Not;A=Brand";v="8.0.0.0", "Chromium";v="150.0.0.0", "Brave";v="150.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
        }

        file = None
        async with aiofiles.open(pathToFile, "rb") as f1:
            file = await f1.read()

        encoded = await asyncio.to_thread(b64encode, file)
        mp = CurlMime()
        mp.addpart("imageBase64", data=encoded)
        val = self.cookies.get("_EDGE_S").split("SID=")[1]
        r: Response = await self.session.post(f"https://www.bing.com/images/create/upload?&sid={val}", headers=headers, cookies=self.cookies, multipart=mp, stream=False)
        logger.debug(f"sending POST to {r.url} ({r.status_code}) with headers: \n{r.request.headers}")

        content = r.text
        result = await asyncio.to_thread(json.loads, content)
        if result.get('error') is not None:
            raise Exception(result['error'])
        return result.get("bcid")
    async def generate(self, query: str, model: Literal['MAI', 'GPT-4o', 'Dalle-3'] = 'Dalle-3', aspect_ratio: Literal['3:2', '1:1', '4:7', '7:4', '2:3'] = '3:2', timeout: float = None, providedFile: str = None, resultAmount: Literal['1', '2', '3', '4'] = '4'):
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.bing.com',
            'priority': 'u=0, i',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
        }
        aspectRatios = {
            "3:2": "4",
            "1:1": "1",
            "4:7": "3", 
            "7:4": "2",
            "2:3": "5",
        }
        models = {
            "MAI": "10",
            "GPT-4o": "1",
            "Dalle-3": "0",
        }
        if (model not in models):
            raise ValueError(f"{model} not in models: {list(models.keys())}")
        if (aspect_ratio not in aspectRatios):
            raise ValueError(f"{aspect_ratio} not in aspect ratios: {list(aspectRatios.keys())}")
        params = {
            'FORM': 'GENCRE',
            'q': query,
            'ctype': 'image',
            'mdl': models.get(model, "10"),
            'ar': aspectRatios.get(aspect_ratio, "4"),
            'rt': resultAmount,
        }
        if providedFile:
            bcid = await self.upload(providedFile)
            params['bcid'] = bcid
            params['edt'] = "1"
        logger.debug(f"Sending a post request to https://www.bing.com/images/create/ai-image-generator with parameters:\n{params}")
        r: Response = await self.session.post('https://www.bing.com/images/create/ai-image-generator', params=params, cookies=self.cookies, headers=headers, allow_redirects=False, stream=True)
        if r.status_code != 302:
            text = await r.atext()
            if "Content warning" in text:
                raise ValueError(f"Prompt has been blocked")
            async with aiofiles.open("response.txt", "w", encoding="utf-8") as f1:
                await f1.write(text) 
            raise Exception(f"Failed to send a generation request, check response.txt")
        logger.debug(f"New url: {str(r.url)}")
        logger.debug(f"{r.headers.get('location')}")
        
        queryId = None
        for i in r.headers.get('location').split("?")[1].split("&"):
            if i.split("=")[0] == "id":
                queryId = i.split("=")[1]
                break
        if queryId is None:
            async with aiofiles.open("response.txt", "wb") as f1:
                async for chunk in r.aiter_content(1024):
                    await f1.write(chunk)
            raise Exception(f"Couldn't get generation ID, status: {r.status_code}")
        logger.debug(f"Got queryid: {queryId}")
        waitingUrl = f"https://www.bing.com/images/create/ai-image-generator/async/results/{queryId}"
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.8',
            'priority': 'u=1, i',
            'referer': str(r.url),
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
        }
        start = time.time()
        isHTML = False
        while True:
            r: Response = await self.session.get(waitingUrl, headers=headers, cookies=self.cookies, stream=True)
            content = await r.acontent()
            if len(content) == 0:
                logger.debug(f"content len is {len(content)}, waiting 2 seconds...")
                await asyncio.sleep(2)
                continue
            if b"<style" in content:
                logger.debug("Html style polling received")
                isHTML = True
                break
            try:
                result = await asyncio.to_thread(json.loads, content)
            except:
                logger.debug(f"Failed to json decode content, len of content: {len(content)}")
                async with aiofiles.open("response.txt", "wb") as f1:
                    await f1.write(content)
                raise Exception("Errored in waiting for images")
            if result['status'] == 0:
                logger.info("Waiting 2 seconds...")
                await asyncio.sleep(2)
            else:
                if result['status'] == 1:
                    logger.info("Image(s) available, not 100% complete")
                    await asyncio.sleep(2)
                else:
                    logger.info("Image(s) available, fully complete")
                    break
            current = time.time() - start
            if timeout and current > timeout:
                raise asyncio.TimeoutError("Timed out waiting for generation")
        if isHTML:
            viewImagesPattern = r"data-imgseturl=\"(.*?)\""
            viewImgSetUrl = "https://www.bing.com" + unescape((await asyncio.to_thread(re.search, viewImagesPattern, content.decode())).group(1))
            viewImagesPattern = r'data-vimgseturl="(.*?)"'
            matched_path = "https://www.bing.com" + unescape((await asyncio.to_thread(re.search, viewImagesPattern, content.decode())).group(1))
            logger.debug(f"image set url: {viewImgSetUrl}")
            logger.debug(matched_path)
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.8',
                'priority': 'u=0, i',
                'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Brave";v="150"',
                'sec-ch-ua-arch': '"x86"',
                'sec-ch-ua-bitness': '"64"',
                'sec-ch-ua-full-version-list': '"Not;A=Brand";v="8.0.0.0", "Chromium";v="150.0.0.0", "Brave";v="150.0.0.0"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua-platform-version': '"10.0.0"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'sec-gpc': '1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
            }
            params = {
                "FORM": "GENCRE"
            }
            while True:
                try:
                    self.session.cookies.clear("www.bing.com")
                    self.session.cookies.clear(".bing.com")
                    r: Response = await self.session.get(viewImgSetUrl.split("?")[0], params=params, headers=headers, cookies=self.cookies, stream=True)
                    text = await r.atext()
                    dataMatch = await asyncio.to_thread(re.search, r"data-results=\"(.*?)\"", text)
                    result = await asyncio.to_thread(json.loads, unescape((dataMatch).group(1)))
                    result['status'] = result['requestStatus']
                    if result['status'] != 2:
                        continue
                    break
                except:
                    async with aiofiles.open("response.txt", "w", encoding="utf-8") as f1:
                        await f1.write(text)
                    raise Exception(f"Couldn't find data-results in source")
        errors = {
            16: "Unsafe image content detected",
        }
        if result['status'] == 3:
            logger.info(f"Errored in making image: {errors.get(result['errorType'])}")
            data = {
                "_U": self.session.cookies.get("_U"),
                "media": [],
                "model": None,
                "aspectRatio": None,
                'errored': True,
                'errorType': errors.get(result['errorType']),
            }
        else:
            data = {
                "_U": self.session.cookies.get("_U"),
                "media": result['records'][0]['mediaItems'],
                "model": result['records'][0]['model'],
                "aspectRatio": result['records'][0]['aspectRatio'],
                'errored': False,
            }
        return data
    async def download(self, result: dict):
        result['filenames'] = []
        for i in result['media']:
            async with aiofiles.open(os.path.join(os.path.dirname(__file__), i['thid']), "wb") as f1:
                r: Response = await self.session.get(i['src'].split("?")[0], stream=True)
                logger.debug(f"Sent a GET to {r.url} to download image, image size: {int(r.headers.get('content-length'))/(1024*1024):.2f}mb")
                async for chunk in r.aiter_content(1024):
                    await f1.write(chunk)
            ext = mimetypes.guess_extension(r.headers.get("content-type"))
            if ext is None:
                ext = ".jpg"
            os.rename(os.path.join(os.path.dirname(__file__), i['thid']), os.path.join(os.path.dirname(__file__), i['thid'] + ext))
            result['filenames'].append(os.path.join(os.path.dirname(__file__), i['thid'] + ext))
async def main(query: str, model: str, aspectRatio: str, file: str):
    from env import _U, _EDGE_S
    async with binggenerate(_U, _EDGE_S) as bing:
        result = await bing.generate(query, model, aspectRatio, providedFile=file)
        await bing.download(result)
        _ = result.copy()
        _.pop("_U")
        print(json.dumps(_, indent=4, ensure_ascii=False))
        if result.get("_U") is not None and result.get("_U") != _U:
            with open("env.py", "r") as f1:
                env = f1.read()
            env = re.sub(r"_U[ \t]*?=[ \t]*?[rf]{0,2}[\"\']{1,3}(.*?)[\"\']{1,3}", f"_U = \"{result.get('_U')}\"", env, 1)
            with open("env.py", "w") as f1:
                f1.write(env)
            logger.debug("Updated _U value in env.py")
        if bing.session.cookies.get("_EDGE_S") is not None and bing.session.cookies.get("_EDGE_S") != _EDGE_S:
            with open("env.py", "r") as f1:
                env = f1.read()
            env = re.sub(r"_EDGE_S[ \t]*?=[ \t]*?[rf]{0,2}[\"\']{1,3}(.*?)[\"\']{1,3}", f"_U = \"{bing.session.cookies.get('_EDGE_S')}\"", env, 1)
            with open("env.py", "w") as f1:
                f1.write(env)
            logger.debug("Updated _U value in env.py")
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="query")
    parser.add_argument("--model", "-m", choices = ['MAI', 'GPT-4o', 'Dalle-3'], help="Model to use", default="Dalle-3")
    parser.add_argument("--aspect-ratio", "-a", choices = ['3:2', '1:1', '4:7', '7:4', '2:3'], help="Aspect ratio of images", default="1:1")
    parser.add_argument("--verbose", "-v", help="enable verbosity", action="store_true")
    parser.add_argument("--file", "-f", help="Provide path to file for image->image generation")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, handlers = [
        logging.StreamHandler()
    ], format="%(levelname)s - %(message)s")
    asyncio.run(main(args.query, args.model, args.aspect_ratio, args.file))