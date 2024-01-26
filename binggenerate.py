import aiofiles, aiohttp, re, asyncio, logging
from datetime import datetime
from tqdm.asyncio import tqdm_asyncio
from random import choice

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

    async def create(self, prompt: str, _U: str, verbose: bool = False):
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
            '_U': _U,
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
        start = datetime.now()
        logging.debug("posting a request")
        nexturl = await self.postrequest()
        query, id = re.findall(r"https://bing\.com/images/create\?q=(.*?)&rt=\d&FORM=GENCRE&id=(.*?)&nfy=1", nexturl)[0]
        self.url = f"https://www.bing.com/images/create/async/results/{id}?q={query}"
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
        logging.info("downloaded!: " + str(filenames))
        return filenames
        

    async def postrequest(self):
        async with aiohttp.ClientSession() as session:
            async with session.post('https://www.bing.com/images/create', params=self.params, cookies=self.cookies, headers=self.headers, data=self.data) as r:
                response = await r.text(encoding="utf-8")
        idpattern = r"content=\"https://www\.bing\.com/images/create(.*?)\""
        nexturl = "https://bing.com/images/create" + re.findall(idpattern, response)[0].replace("amp;", "")
        if "&id=" not in nexturl:
            raise binggenerate.post_failed(f"Failed to post the prompt to bing! Check authentication or if you aren't already generating 3 things or check if the prompt is allowed.")
        return nexturl
    
    async def check_generation(self) -> (None | list[str]):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=self.headers, cookies=self.cookies) as r:
                response = await r.text(encoding="utf-8")
        if "Unsafe image content detected" in response:
            raise binggenerate.unsafe_image(f"The image is considered unsafe by bing!")
        if "Content warning" in response:
            raise binggenerate.content_warning(f"The image has a content warning!")
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
        async with aiohttp.ClientSession() as session:
            for index, image in enumerate(imagelist):
                filename = f"image-{round(datetime.now().timestamp())}-{index}.jpg"
                async with session.get(image, headers=self.headers) as r:
                    with tqdm_asyncio(total=int(r.headers.get("content-length")) if r.headers.get("content-length") else None, unit="iB", unit_divisor=True, colour=choice(['red', 'green', 'blue', 'magenta'])) as progress:
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
    parser = ArgumentParser()
    parser.add_argument("prompt", type=str, help="prompt to use")
    parser.add_argument("-auth", type=str, help="cookie value (_U) that authenticates requests (mandatory)")
    parser.add_argument("-v", action="store_true", help="verbose")
    args = parser.parse_args()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(binggenerate().create(args.prompt, args.auth, args.v))
