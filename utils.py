is_v6 = is_ipv6(url_info[0])
    if is_v6 and os.getenv("ipv6_proxy"):
        url = os.getenv("ipv6_proxy") + quote(url_info[0])
    else:
        url = url_info[0]
    start = time.time()
    try:
        ffprobe = await asyncio.get_event_loop().run_in_executor(None, ffmpeg_probe, url, 15)
        if ffprobe is None:
            return float("inf")
        video_streams = [stream for stream in ffprobe['streams'] if stream['codec_type'] == 'video']
        if video_streams:
            width = video_streams[0]['width']
            height = video_streams[0]['height']
            if is_ipv6(url_info[0]):
                url_info[0] = url_info[0] + f"{url_info[0]}${width}x{height}|ipv6"
            else:
                url_info[0] = f"{url_info[0]}${width}x{height}"
            url_info[2] = f"{width}x{height}"
            end = time.time()
            return int(round((end - start) * 1000))
        else:
            return float("inf")
    except Exception as e:
        # traceback.print_exc()
        print(e)
        return float("inf")
