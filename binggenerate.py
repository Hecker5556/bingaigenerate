import aiofiles, aiohttp, re, asyncio, logging
from datetime import datetime
from tqdm.asyncio import tqdm_asyncio
from random import choice
from aiohttp_socks import ProxyConnector

class binggenerate:

    class post_failed(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class unsafe_image(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)
    
    class content_warning(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)
    def _create_connector(self, proxy: str = None):
        return ProxyConnector.from_url(proxy) if proxy and proxy.startswith("sock") else aiohttp.TCPConnector()
    async def create(self, prompt: str, _U: str, proxy: str = None, verbose: bool = False):
        if verbose:
            logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
        else:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        self.headers = {
            'authority': 'www.bing.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.8',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.bing.com',
            'referer': 'https://www.bing.com/images/create',
            'sec-ch-ua': '"Not A(Brand";v="99", "Brave";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        }
        self.cookies = {
            'BCP': 'AD=0&AL=0&SM=0',
            '_U': _U,
            'SRCHHPGUSR': 'SRCHLANG=en&PV=10.0.0&BRW=W&BRH=M&CW=1472&CH=783&SCW=1472&SCH=783&DPR=1.3&UTC=120&DM=1&HV=1726065521&PRVCW=1472&PRVCH=783&THEME=0&WEBTHEME=0&WTS=63861662294',
        }
        self.params = {
            'q': prompt,
            'rt': '3',
            'FORM': 'GENCRE',
        }

        self.data = {
            'q': prompt,
            'qs': 'ds',
        }
        self.proxy = proxy if proxy and proxy.startswith("http") else None
        start = datetime.now()
        logging.debug("posting a request")
        self.secondmethod = False
        async with aiohttp.ClientSession(connector = self._create_connector(proxy)) as session:
            self.session = session
            nexturl = await self.postrequest()
            logging.debug(f"is using daily boost: {self.secondmethod}")
            if self.secondmethod == False:
                query, id = re.findall(r"https://(?:www\.)?bing\.com/images/create\?q=(.*?)&rt=\d&FORM=GENCRE&id=(.*?)(?:&nfy=1)?$", nexturl)[0]
                self.url = f"https://www.bing.com/images/create/async/results/{id}?q={query}"
            else:
                self.url = nexturl
            logging.info("successfully posted request!")
            logging.info("waiting for generation to finish...")
            while True:
                result = await self.check_generation()
                if not result:
                    logging.debug("not ready yet, waiting for 5 seconds...")
                    await asyncio.sleep(5)
                    continue
                else:
                    logging.debug("got result!")
                    break
            end = datetime.now()
            difference = end-start
            logging.debug(f"it took {int(difference.total_seconds()//60):02}:{int(difference.total_seconds()%60):02} to get result")
            logging.info("got result, gonna download now")
            filenames = await self.download_images(result)
            logging.info("downloaded!: " + ", ".join(filenames))
            return filenames
        

    async def postrequest(self):
        async with self.session.post('https://www.bing.com/images/create', params=self.params, cookies=self.cookies, headers=self.headers, data=self.data, proxy=self.proxy) as r:
            response = await r.text(encoding="utf-8")
            idpattern = r"content=\"https://www\.bing\.com/images/create(.*?)\""
            nexturl = "https://bing.com/images/create" + re.findall(idpattern, response)[0].replace("amp;", "")
        if "&id=" not in nexturl:
            self.params['rt'] = '4'
            async with self.session.post('https://www.bing.com/images/create', params=self.params, cookies=self.cookies, headers=self.headers, data=self.data, proxy=self.proxy) as r:
                response = await r.text(encoding="utf-8")
            with open("response.txt", "w", encoding="utf-8") as f1:
                f1.write(response)
            match = re.findall(r"data-c=\"(/images/create/async/results/(?:.*?))\"", response)
            if match:
                nexturl = "https://bing.com" + match[0].replace("amp;", "")
                self.secondmethod = True
            else:
                raise self.post_failed("failed to post a request! check prompt or cookie validity")
        return nexturl
    
    async def check_generation(self) -> (None | list[str]):

        async with self.session.get(self.url, headers=self.headers, cookies=self.cookies, proxy=self.proxy) as r:
            response = await r.text(encoding="utf-8")
        if "Unsafe image content detected" in response:
            raise self.unsafe_image(f"The image is considered unsafe by bing!")
        if "Content warning" in response:
            raise self.content_warning(f"The image has a content warning!")
        imgurlspattern = r"src=\"(https:\/\/tse\d\.mm\.bing\.net(?:.*?))\""
        matches: list[str] = re.findall(imgurlspattern, response)
        if not matches:
            return None
        width = re.findall(r"https:\/\/tse\d\.mm\.bing\.net\/th\/id\/(?:.*?)\?w=(\d*?)&h=(\d*?)&", matches[0].replace("amp;", ""))[0][0]
        imageurls = [x.replace("amp;", "").replace(f"w={width}", "w=1024").replace(f"h={width}", "h=1024") for x in matches]
        return imageurls
    
    async def download_images(self, imagelist: list[str]) -> list[str]:
        filenames = []
        logging.debug(f"Downloading {len(imagelist)} images")
        colors = ['red', 'green', 'blue', 'magenta']

        async with aiohttp.ClientSession() as session:
            for index, image in enumerate(imagelist):
                color = choice(colors)
                colors.pop(colors.index(color))
                filename = f"image-{round(datetime.now().timestamp())}-{index}.jpg"
                async with session.get(image, headers=self.headers) as r:
                    with tqdm_asyncio(total=int(r.headers.get("content-length")) if r.headers.get("content-length") else None, unit="iB", unit_scale=True, colour=color) as progress:
                        async with aiofiles.open(filename, 'wb') as f1:
                            while True:
                                chunk = await r.content.read(1024)
                                if not chunk:
                                    break
                                progress.update(len(chunk))
                                await f1.write(chunk)
                filenames.append(filename)
        return filenames
                
if __name__ == "__main__":
    from argparse import ArgumentParser
    import os
    parser = ArgumentParser()
    parser.add_argument("prompt", type=str, help="prompt to use")
    parser.add_argument("-auth", type=str, help="cookie value (_U) that authenticates requests (mandatory), location to file or the cookie")
    parser.add_argument("-proxy", type=str, help="https/socks proxy to use in the connection")
    parser.add_argument("-v", action="store_true", help="verbose")
    args = parser.parse_args()
    if args.auth:
        if os.path.exists(args.auth):
            with open(args.auth, 'r') as f1:
                auth = f1.read()
        else:
            auth = args.auth
    else:
        try:
            from env import auth
        except:
            print("cant find auth anywhere!\nEither create an env.py file in the same directory as binggenerate.py and put auth = 'cookie' replacing cookie with the _U cookie\nor\nstore the auth in a .txt file and input the file name to -auth 'filename' when running in command prompt\nor\ndirectly input the auth cookie when running in command prompt with -auth 'cookie'")
            from sys import exit
            exit(1)
    asyncio.run(binggenerate().create(args.prompt, auth, args.proxy, args.v))
