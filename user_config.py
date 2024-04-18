source_file = "user_demo.txt"
final_file = "user_result.txt"
favorite_list = [
    "广东珠江",
    "开平综合",
    "开平生活",
    "CCTV-1",
    "CCTV-5",
    "CCTV-5+",
    "CCTV-13",
    "广东体育",
    "广东卫视",
    "大湾区卫视",
    "浙江卫视",
    "湖南卫视",
    "翡翠台",
]
favorite_page_num = 3
default_page_num = 2
urls_limit = 20
response_time_weight = 0.5
resolution_weight = 0.5
recent_days = 30
ipv_type = "all"
domain_blacklist = ["epg.pw"]
url_keywords_blacklist = ["https://live.v1.mk/api/bestv.php?id=wxtyhd8m/8000000"]
# crawl_type的默认值为1-只爬取foodieguide网站；2-只爬取crawl_urls中配置的网站；3-全部
crawl_type = "3"
# 收集其他大佬url中的直播源
crawl_urls = ["https://mirror.ghproxy.com/raw.githubusercontent.com/tianya7981/jiekou/main/0406",
              "https://fanmingming.com/txt?url=https://live.fanmingming.com/tv/m3u/ipv6.m3u",
             "https://mirror.ghproxy.com/raw.githubusercontent.com/shidahuilang/shuyuan/shuyuan/iptv.txt"]
# ftp上传result.txt文件
ftp_host = ""
ftp_port = ""
ftp_user = ""
ftp_pass = ""
ftp_remote_file = ""
