import traceback
from ftplib import FTP
import requests

try:
    import user_config as config
except ImportError:
    import config
import asyncio
from bs4 import BeautifulSoup
from utils import (
    getChannelItems,
    updateChannelUrlsTxt,
    updateFile,
    getUrlInfo,
    compareSpeedAndResolution,
    getTotalUrls,
    checkUrlIPVType,
    checkByDomainBlacklist,
    checkByURLKeywordsBlacklist,
    filterUrlsByPatterns, is_match_url,
)
import logging
import os
from tqdm import tqdm

# logging.basicConfig(
#     filename="result_new.log",
#     filemode="a",
#     format="%(message)s",
#     level=logging.INFO,
#     encoding='utf-8'
# )
logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("result_new.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class UpdateSource:

    def __init__(self, callback=None):
        self.callback = callback

    async def visitPage(self, channelItems):
        total_channels = sum(len(channelObj) for _, channelObj in channelItems.items())
        pbar = tqdm(total=total_channels)
        crawl_result_dict = {}
        if config.crawl_type in ["2", "3"]:
            for conf_url in config.crawl_urls:
                crawl_response = requests.get(conf_url.strip())
                crawl_response.encoding = 'utf-8'
                if crawl_response.status_code != 200:
                    continue
                crawl_data = crawl_response.text.split('\n')  # 按行分割数据
                for line in crawl_data:
                    parts = line.split(',')  # 按逗号分割每一行
                    if len(parts) == 2:
                        key = parts[0].strip() \
                            .replace("「", "").replace("」", "") \
                            .replace("电视台", "").replace("IPV6", "").replace("IPV4", "")
                        value = parts[1].strip()
                        is_url, url = is_match_url(value)
                        if not is_url:
                            continue
                        if key in crawl_result_dict:
                            crawl_result_dict[key].append(url)
                        else:
                            crawl_result_dict[key] = [value]

        for cate, channelObj in channelItems.items():
            channelUrls = {}
            channelObjKeys = channelObj.keys()
            for name in channelObjKeys:
                pbar.set_description(
                    f"Processing {name}, {total_channels - pbar.n} channels remaining"
                )
                isFavorite = name in config.favorite_list
                pageNum = (
                    config.favorite_page_num if isFavorite else config.default_page_num
                )
                infoList = []
                if config.crawl_type in ["1", "3"]:
                    for page in range(1, pageNum + 1):
                        try:
                            page_url = f"https://www.foodieguide.com/iptvsearch/?page={page}&s={name}"
                            headers = {
                                'Content-Type': 'applicationx-www-form-urlencoded;charset=UTF-8',
                                # 设置请求头中的Content-Type为JSON格式
                                'User-Agent': 'Mozilla5.0 (Linux; Android 8.0.0; SM-G955U BuildR16NW) AppleWebKit537.36 (KHTML, like Gecko) Chrome116.0.0.0 Mobile Safari537.36',
                                'Referer': 'httpswww.foodieguide.comiptvsearch',
                                'Origin': 'httpswww.foodieguide.com',
                                'Sec-Fetch-Mode': 'navigate',
                                'Sec-Ch-Ua-Platform': 'Android',
                                'Sec-Ch-Ua-Mobile': '1',
                                'Sec-Ch-Ua': 'Not_A Brand;v=8, Chromium;v=120, Google Chrome;v=120',
                                'Sec-Fetch-Dest': 'document',
                                'Sec-Fetch-Site': 'same-origin',
                                'Sec-Fetch-User': '1',
                                'Upgrade-Insecure-Requests': '1',
                                'Accept-Language': 'zh-CN,zh;q=0.9'
                            }
                            response = requests.get(page_url, headers=headers)
                            response.encoding = "UTF-8"
                            soup = BeautifulSoup(response.text, "html.parser")
                            tables_div = soup.find("div", class_="tables")
                            results = (
                                tables_div.find_all("div", class_="result")
                                if tables_div
                                else []
                            )
                            for result in results:
                                try:
                                    url, date, resolution = getUrlInfo(result)
                                    if (
                                            url
                                            and checkUrlIPVType(url)
                                            and checkByDomainBlacklist(url)
                                            and checkByURLKeywordsBlacklist(url)
                                    ):
                                        infoList.append((url, date, resolution))
                                except Exception as e:
                                    print(f"Error on result {result}: {e}")
                                    continue
                        except Exception as e:
                            traceback.print_exc()
                            print(f"Error on page {page}: {e}")
                            continue
                if config.crawl_type in ["2", "3"]:
                    tv_urls = crawl_result_dict.get(name, None)
                    if tv_urls is not None:
                        for tv_url in tv_urls:
                            if not tv_url:
                                continue
                            if not checkUrlIPVType(tv_url):
                                continue
                            if not checkByDomainBlacklist(tv_url):
                                continue
                            if not checkByURLKeywordsBlacklist(tv_url):
                                continue
                            infoList.append((tv_url, None, None))
                try:
                    sorted_data = await compareSpeedAndResolution(infoList)
                    if sorted_data:
                        channelUrls[name] = (
                                getTotalUrls(sorted_data) or channelObj[name]
                        )
                        for (url, date, resolution), response_time in sorted_data:
                            logger.info(
                                f"Name: {name}, URL: {url}, Date: {date}, Resolution: {resolution}, Response Time: {response_time}ms"
                            )
                    else:
                        channelUrls[name] = filterUrlsByPatterns(channelObj[name])
                except Exception as e:
                    print(f"Error on sorting: {e}")
                    continue
                finally:
                    pbar.update()
            updateChannelUrlsTxt(cate, channelUrls)
            # await asyncio.sleep(1)
        pbar.close()

    def main(self):
        asyncio.run(self.visitPage(getChannelItems()))
        for handler in logger.handlers:
            handler.close()
            logger.removeHandler(handler)
        user_final_file = getattr(config, "final_file", "result.txt")
        user_log_file = (
            "user_result.log" if os.path.exists("user_config.py") else "result.log"
        )
        updateFile(user_final_file, "result_new.txt")
        updateFile(user_log_file, "result_new.log")
        print(f"Update completed! Please check the {user_final_file} file!")

        ftp = None
        try:
            ftp_host = getattr(config, "ftp_host", None)
            ftp_host = ftp_host if ftp_host else os.getenv('ftp_host')
            ftp_port = getattr(config, "ftp_port", None)
            ftp_port = ftp_port if ftp_port else os.getenv('ftp_port')
            ftp_user = getattr(config, "ftp_user", None)
            ftp_user = ftp_user if ftp_user else os.getenv('ftp_user')
            ftp_pass = getattr(config, "ftp_pass", None)
            ftp_pass = ftp_pass if ftp_pass else os.getenv('ftp_pass')
            ftp_remote_file = getattr(config, "ftp_remote_file", None)
            ftp_remote_file = ftp_remote_file if ftp_remote_file else os.getenv('ftp_remote_file')
            if ftp_host and ftp_port and ftp_user and ftp_pass and ftp_remote_file:
                ftp = FTP()
                ftp.connect(ftp_host, int(ftp_port))
                ftp.login(user=ftp_user, passwd=ftp_pass)
                with open(user_final_file, 'rb') as file:
                    up_res = ftp.storbinary(f'STOR {ftp_remote_file}', file)
                    if up_res.startswith('226 Transfer complete'):
                        print('result upload success！')
                    else:
                        print('result upload fail!')
        finally:
            if ftp is not None:
                ftp.quit()


if __name__ == '__main__':
    UpdateSource().main()
