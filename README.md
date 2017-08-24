v_qq_dl - download videos from v.qq.com


# DESCRIPTION
**v_qq_dl** is a command-line program to download videos from v.qq.com(qq视频).

    v_qq_dl [OPTIONS] URL

It would show some information as following:

    title: 翼装飞行穿移动靶 中国翼装侠张树鹏创新世界纪录
    type: mp4
    size: 27643467
    quality: fhd
    Begin download:
    [-                                       ]	3 %


# FEATURES
1. **Automatic Proxy**. If you are using IP address out from China, this program can pick a Chinese proxy automatically to get information from tencent's api and download from your own IP. So that your download speed will not be compromised.
2. **Multi thread**. This program use multiple threads downloading for the video, the downloading speed can be up to around 1 MB/s.
3. **Continuously Downloading**. You can continue the downloading from where you stopped.



# OPTIONS
    -h, --help            show this help message and exit
    --ffmpeg_location FFMPEG_LOCATION
                          Location of the ffmpeg binary
    --aria2_location ARIA2_LOCATION
                          Location of the aria2 binary
    -v, --verbose, --debug
                          Print various debugging information
    --keep_tmp            Keep temporary files
  
# FAQ