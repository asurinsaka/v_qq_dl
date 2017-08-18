v_qq_dl - download videos from v.qq.com


# DESCRIPTION
**v_qq_dl** is a command-line program to download videos from v.qq.com.

    v_qq_dl [OPTIONS] URL

# FEATURES
1. If you are using IP address out from China, this program can pick a Chinese proxy automatically to get information from tencent's api and download from your own IP. So that your download speed will not be compromised.
2. This program use multiple threads downloading for the video, the downloading speed can be up to around 1 MB/s.




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