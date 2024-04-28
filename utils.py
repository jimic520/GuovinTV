try:
    import user_config as config
except ImportError:
    import config
import aiohttp
import asyncio
import time
import re
import datetime
import os
import urllib.parse
import ipaddress
from urllib.parse import urlparse, urljoin, quote, unquote
import m3u8
import requests
import ffmpeg


def getChannelItems():
    """
    Get the channel items from the source file
    """
    # Open the source file and read all lines.
    try:
        user_source_file = (
            "user_" + config.source_file
            if os.path.exists("user_" + config.source_file)
            else getattr(config, "source_file", "demo.txt")
        )
        with open(user_source_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Create a dictionary to store the channels.
        channels = {}
        current_category = ""
        pattern = r"^(.*?),(?!#genre#)(.*?)$"
        # total_channels = 0
        # max_channels = 200

        for line in lines:
            # if total_channels >= max_channels:
            #     break
            line = line.strip()
            if "#genre#" in line:
                # This is a new channel, create a new key in the dictionary.
                current_category = line.split(",")[0]
                channels[current_category] = {}
            else:
                # This is a url, add it to the list of urls for the current channel.
                match = re.search(pattern, line)
                if match:
                    if match.group(1) not in channels[current_category]:
                        channels[current_category][match.group(1)] = [match.group(2)]
                        # total_channels += 1
                    else:
                        channels[current_category][match.group(1)].append(
                            match.group(2)
                        )
        return channels
    finally:
        f.close()


def updateChannelUrlsTxt(cate, channelUrls):
    """
    Update the category and channel urls to the final file
    """
    try:
        with open("result_new.txt", "a", encoding="utf-8") as f:
            f.write(cate + ",#genre#\n")
            for name, urls in channelUrls.items():
                for url in urls:
                    if url is not None:
                        f.write(name + "," + url + "\n")
            f.write("\n")
    finally:
        f.close


def updateFile(final_file, old_file):
    """
    Update the file
    """
    if os.path.exists(old_file):
        os.replace(old_file, final_file)


def getUrlInfo(result):
    """
    Get the url, date and resolution
    """
    url = date = resolution = None
    result_div = [div for div in result.children if div.name == "div"]
    for result_sub_div in result_div:
        img_tags = result_sub_div.find_all("img")
        if not img_tags:
            continue
        if "copy" not in str(result_sub_div):
            continue
        channel_text = result_sub_div.get_text(strip=True)
        url_match = re.search(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            channel_text,
        )
        if url_match:
            url = url_match.group()
        info_text = result_div[-1].get_text(strip=True)
        if info_text:
            date, resolution = (
                (info_text.partition(" ")[0] if info_text.partition(" ")[0] else None),
                (
                    info_text.partition(" ")[2].partition("•")[2]
                    if info_text.partition(" ")[2].partition("•")[2]
                    else None
                ),
            )
        break
    return url, date, resolution


# async def getSpeed(url):
#     async with aiohttp.ClientSession() as session:
#         start = time.time()
#         try:
#             async with session.get(url, timeout=5) as response:
#                 resStatus = response.status
#         except:
#             return float("inf")
#         end = time.time()
#         if resStatus == 200:
#             return int(round((end - start) * 1000))
#         else:
#             return float("inf")

async def check_stream_speed(ts_url):
    try:
        start = time.time()
        probe = await asyncio.get_event_loop().run_in_executor(None, ffmpeg.probe, ts_url)
        video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
        if video_streams:
            width = video_streams[0]['width']
            height = video_streams[0]['height']
            #print(f"{input_url}-视频分辨率: {width}x{height}")
            end = time.time()
            return int(round((end - start) * 1000))
        else:
            #print("无法获取视频流信息")
            return float("inf")
    except Exception:
        return float("inf")

async def load_m3u8_async(url, timeout):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, m3u8.load, url, timeout)

async def getSpeed(url):
    if "$" in url:
        url = url.split('$')[0]
    url = quote(url, safe=':/?&=$[]')
    start = time.time()
    try:
        if ".php" not in url and ".m3u8" not in url:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    end = time.time()
                    if response.status == 200:
                        return int(round((end - start) * 1000))
        elif ".m3u8" in url or ".php" in url:
            playlist = await load_m3u8_async(url, timeout=5)
            ts_uri = playlist.segments.uri[0]
            ts_url = urljoin(url, ts_uri).strip()
            async with aiohttp.ClientSession() as session:
                async with session.head(ts_url, timeout=5) as res:
                    if res.status == 200:
                        speed = await check_stream_speed(ts_url)
                        return speed
        return float("inf")
    except Exception:
        return float("inf")
        
async def compareSpeedAndResolution(infoList):
    """
    Sort by speed and resolution
    """
    response_times = await asyncio.gather(*(getSpeed(url) for url, _, _ in infoList))
    valid_responses = [
        (info, rt) for info, rt in zip(infoList, response_times) if rt != float("inf")
    ]

    def extract_resolution(resolution_str):
        numbers = re.findall(r"\d+x\d+", resolution_str)
        if numbers:
            width, height = map(int, numbers[0].split("x"))
            return width * height
        else:
            return 0

    default_response_time_weight = 0.5
    default_resolution_weight = 0.5
    response_time_weight = getattr(
        config, "response_time_weight", default_response_time_weight
    )
    resolution_weight = getattr(config, "resolution_weight", default_resolution_weight)
    # Check if weights are valid
    if not (
            0 <= response_time_weight <= 1
            and 0 <= resolution_weight <= 1
            and response_time_weight + resolution_weight == 1
    ):
        response_time_weight = default_response_time_weight
        resolution_weight = default_resolution_weight

    def combined_key(item):
        (_, _, resolution), response_time = item
        resolution_value = extract_resolution(resolution) if resolution else 0
        return (
                -(response_time_weight * response_time)
                + resolution_weight * resolution_value
        )

    sorted_res = sorted(valid_responses, key=combined_key, reverse=True)
    return sorted_res


def filterByDate(data):
    """
    Filter by date and limit
    """
    default_recent_days = 60
    use_recent_days = getattr(config, "recent_days", 60)
    if (
            not isinstance(use_recent_days, int)
            or use_recent_days <= 0
            or use_recent_days > 365
    ):
        use_recent_days = default_recent_days
    start_date = datetime.datetime.now() - datetime.timedelta(days=use_recent_days)
    recent_data = []
    unrecent_data = []
    for (url, date, resolution), response_time in data:
        if date:
            date = datetime.datetime.strptime(date, "%m-%d-%Y")
            if date >= start_date:
                recent_data.append(((url, date, resolution), response_time))
            else:
                unrecent_data.append(((url, date, resolution), response_time))
    if len(recent_data) < config.urls_limit:
        recent_data.extend(unrecent_data[: config.urls_limit - len(recent_data)])
    return recent_data[: config.urls_limit]


def getTotalUrls(data):
    """
    Get the total urls with filter by date and depulicate
    """
    total_urls = []
    if len(data) > config.urls_limit:
        total_urls = [url for (url, _, _), _ in filterByDate(data)]
    else:
        total_urls = [url for (url, _, _), _ in data]
    return list(dict.fromkeys(total_urls))


def is_ipv6(url):
    """
    Check if the url is ipv6
    """
    try:
        host = urllib.parse.urlparse(url).hostname
        ipaddress.IPv6Address(host)
        return True
    except ValueError:
        return False


def checkUrlIPVType(url):
    """
    Check if the url is compatible with the ipv type in the config
    """
    ipv_type = getattr(config, "ipv_type", "ipv4")
    if ipv_type == "ipv4":
        return not is_ipv6(url)
    elif ipv_type == "ipv6":
        return is_ipv6(url)
    else:
        return True


def checkByDomainBlacklist(url):
    """
    Check by domain blacklist
    """
    domain_blacklist = [
        urlparse(domain).netloc if urlparse(domain).scheme else domain
        for domain in getattr(config, "domain_blacklist", [])
    ]
    return urlparse(url).netloc not in domain_blacklist


def checkByURLKeywordsBlacklist(url):
    """
    Check by URL blacklist keywords
    """
    url_keywords_blacklist = getattr(config, "url_keywords_blacklist", [])
    return not any(keyword in url for keyword in url_keywords_blacklist)


def filterUrlsByPatterns(urls):
    """
    Filter urls by patterns
    """
    urls = [url for url in urls if checkUrlIPVType(url)]
    urls = [url for url in urls if checkByDomainBlacklist(url)]
    urls = [url for url in urls if checkByURLKeywordsBlacklist(url)]
    return urls


def is_match_url(url):
    url_match = url.strip().startswith("http")
    if url_match:
        return True, url.strip()
    return False, None


def filter_CCTV_key(key: str):
    if "cctv" not in key.lower():
        return key
    chinese_pattern = re.compile("[\u4e00-\u9fa5]+")  # 匹配中文字符的 Unicode 范围
    filtered_text = chinese_pattern.sub('', key)  # 使用 sub 方法替换中文字符为空字符串
    result = re.sub(r'\[\d+\*\d+\]', '', filtered_text)
    return result.strip()
