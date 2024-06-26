import json
import subprocess
import traceback

import requests

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
from urllib.parse import urlparse, urljoin, quote

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable


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
        if os.path.exists(final_file):
            os.remove(final_file)
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

async def check_stream_speed(url_info):
    try:
        is_v6 = is_ipv6(url_info[0])
        if is_v6 and os.getenv("ipv6_proxy"):
            url = os.getenv("ipv6_proxy") + quote(url_info[0])
            response = requests.get(url)
            if response.status_code == 200:
                if not url_info[2]:
                    url_info[2] = '1920x1080'
                url_info[0] = url_info[0] + f"${url_info[2]}|ipv6"
                return 1
            else:
                return float("inf")
        else:
            url = url_info[0]
        start = time.time()
        ffprobe = await asyncio.get_event_loop().run_in_executor(None, ffmpeg_probe, url, 15)
        if ffprobe is None:
            return float("inf")
        video_streams = [stream for stream in ffprobe['streams'] if stream['codec_type'] == 'video']
        if video_streams:
            width = video_streams[0]['width']
            height = video_streams[0]['height']
            print("***************************")
            print(f"{width}x{height}")
            print("***************************")
            url_info[0] = url_info[0] + f"${width}x{height}"
            if is_v6:
                url_info[0] = url_info[0] + "|ipv6"
            url_info[2] = f"{width}x{height}"
            end = time.time()
            return int(round((end - start) * 1000))
        else:
            return float("inf")
    except Exception as e:
        # traceback.print_exc()
        print(e)
        return float("inf")


async def getSpeed(url_info):
    url, _, _ = url_info
    if "$" in url:
        url = url.split('$')[0]
    url = quote(url, safe=':/?&=$[]')
    url_info[0] = url
    try:
        speed = await check_stream_speed(url_info)
        return speed
    except Exception:
        return float("inf")


async def compareSpeedAndResolution(infoList):
    """
    Sort by speed and resolution
    """
    response_times = await asyncio.gather(*[getSpeed(url_info) for url_info in infoList])
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


def convert_kwargs_to_cmd_line_args(kwargs):
    """Helper function to build command line arguments out of dict."""
    args = []
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if isinstance(v, Iterable) and not isinstance(v, str):
            for value in v:
                args.append('-{}'.format(k))
                if value is not None:
                    args.append('{}'.format(value))
            continue
        args.append('-{}'.format(k))
        if v is not None:
            args.append('{}'.format(v))
    return args


def convert_kwargs_to_cmd_line_args(kwargs):
    """Helper function to build command line arguments out of dict."""
    args = []
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if isinstance(v, Iterable) and not isinstance(v, str):
            for value in v:
                args.append('-{}'.format(k))
                if value is not None:
                    args.append('{}'.format(value))
            continue
        args.append('-{}'.format(k))
        if v is not None:
            args.append('{}'.format(v))
    return args


def ffmpeg_probe(filename, timeout, cmd='ffprobe', **kwargs):
    """Run ffprobe on the specified file and return a JSON representation of the output.

    Raises:
        :class:`ffmpeg.Error`: if ffprobe returns a non-zero exit code,
            an :class:`Error` is returned with a generic error message.
            The stderr output can be retrieved by accessing the
            ``stderr`` property of the exception.
    """
    args = [cmd, '-show_format', '-show_streams', '-of', 'json']
    args += convert_kwargs_to_cmd_line_args(kwargs)
    args += [filename]
    p = None
    try:
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        communicate_kwargs = {}
        if timeout is not None:
            communicate_kwargs['timeout'] = timeout
        out, err = p.communicate(**communicate_kwargs)
        if p.returncode != 0:
            return None
        return json.loads(out.decode('utf-8'))
    except Exception:
        #traceback.print_exc()
        return None
    finally:
        graceful_exit(p)

def graceful_exit(process):
    if process is None:
        return
    try:
        process.terminate()
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()
