source_file = "demo.txt"
final_file = "result.txt"
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
urls_limit = 10
response_time_weight = 0.5
resolution_weight = 0.5
recent_days = 30
ipv_type = "ipv4"
domain_blacklist = ["epg.pw"]
url_keywords_blacklist = []
# crawl_type的默认值为1-只爬取foodieguide网站；2-只爬取crawl_urls中配置的网站；3-全部
crawl_type = "1"
# 收集其他大佬url中的直播源
crawl_urls = []
# ftp上传result.txt文件
ftp_host = ""
ftp_port = ""
ftp_user = ""
ftp_pass = ""
ftp_remote_file = ""
