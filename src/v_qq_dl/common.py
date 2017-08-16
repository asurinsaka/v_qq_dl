#!/usr/bin/env python

import sys
import logging
from urllib import request, error, parse
import socket
import re
import json
import threading
from subprocess import call

def urlopen_with_retry(attempt, *args, **kwargs):
    for i in range(attempt):
        try:
            return request.urlopen(*args, **kwargs)
        except socket.timeout:
            logging.debug('request attemp %s timeout: %s' % str(i + 1))
        except error.HTTPError as http_error:
            logging.debug('HTTP Error with code{}'.format(http_error.code))
        except Exception as e:
            logging.debug('urlopen_with_retry: %s' %e)

def get_content(url, attempt):
    """Gets the content of a URL via sending a HTTP GET request.

       Args:
           url: A URL.


       Returns:
           The content as a string.
       """
    logging.debug('get_content: %s' % url)

    req = request.Request(url)
    response = urlopen_with_retry(attempt, req)
    data = response.read()
    # print(data.decode('utf-8'))
    data = data.decode('utf-8')
    return data


def url_info(url):
    try:
        response = urlopen_with_retry(2, request.Request(url))
    except Exception as e:
        logging.debug('url_info: %s %s' % (e, url))

    headers = response.headers

    type = headers['content-type']
    type_mapping = {
        'video/3gpp': '3gp',
        'video/f4v': 'flv',
        'video/mp4': 'mp4',
        'video/MP2T': 'ts',
        'video/quicktime': 'mov',
        'video/webm': 'webm',
        'video/x-flv': 'flv',
        'video/x-ms-asf': 'asf',
        'audio/mp4': 'mp4',
        'audio/mpeg': 'mp3',
        'audio/wav': 'wav',
        'audio/x-wav': 'wav',
        'audio/wave': 'wav',
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'application/pdf': 'pdf',
    }
    if type in type_mapping:
        ext = type_mapping[type]
    else:
        type = None

    if headers['transfer-encoding'] != 'chunked':
        size = headers['content-length'] and int(headers['content-length'])
    else:
        size = None

    return type, ext, size



def get_url_from_vid(vid, title):

    # a json file to save temporary information in case download failed
    try:
        with open('{}.json'.format(vid), 'r') as fp:
            download_dict = json.load(fp)
    except FileNotFoundError:
        download_dict = {'vid': vid, 'title': title}
    info_api = 'http://vv.video.qq.com/getinfo?otype=json&appver=3.2.19.333&platform=11&defnpayver=1&vid={}'.format(vid)
    if info_api in download_dict.keys():
        info = download_dict[info_api]
    else:
        info = get_content(info_api, 2)
    video_json = json.loads(re.search(r'QZOutputJson=(.*);', info).group(1))

    if video_json['exem'] != 0:
        logging.error(video_json['msg'])

    fn_pre = video_json['vl']['vi'][0]['lnk']
    title = video_json['vl']['vi'][0]['ti']
    host = video_json['vl']['vi'][0]['ul']['ui'][0]['url']
    streams = video_json['fl']['fi']
    seg_cnt = video_json['vl']['vi'][0]['cl']['fc']
    if seg_cnt == 0:
        seg_cnt = 1

    best_quality = streams[-1]['name']
    part_format_id = streams[-1]['id']

    part_urls = []
    total_size = 0

    for part in range(1, seg_cnt+1):
        if 'part_urls' in download_dict.keys():
            part_urls = download_dict['part_urls']
            break
        filename = fn_pre + '.p' + str(part_format_id % 10000) + '.' + str(part) + '.mp4'
        key_api = "http://vv.video.qq.com/getkey?otype=json&platform=11&format={}&vid={}&filename={}&appver=3.2.19.333".format(
            part_format_id, vid, filename)
        if key_api in download_dict.keys():
            key_json = download_dict[key_api]
        else:
            part_info = get_content(key_api, 2)
            key_json = json.loads(re.search(r'QZOutputJson=(.*);', part_info).group(1))
            download_dict[key_api] = key_json
        if key_json.get('key') is None:
            logging.warning(key_json['msg'])
            break
        vkey = key_json['key']
        url = '{}{}?vkey={}'.format(host, filename, vkey)
        part_urls.append(url)
        _, ext, size = url_info(url)
        total_size += size
    else:
        download_dict['part_urls'] = part_urls
        download_dict['ext'] = ext
        with open('{}.json'.format(vid), 'w') as fp:
            json.dump(download_dict, fp, sort_keys=True, indent=4)


def download_with_aria2(url, out_file):
    call(["/usr/local/aria2/bin/aria2c", "-x", '16', url, '-o', out_file])
    pass


def download(vid, title, urls, ext):
    files = []
    threads = []

    for i, url in enumerate(urls):
        filename = '{}[{}].{}'.format(title, i, ext)
        t = threading.Thread(target=download_with_aria2, args=(url, filename))
        files.append(filename)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


    with open('{}.txt'.format(vid), 'w') as fp:
        for filename in files:
            fp.write("file '{}'\n".format(filename))

    # call(['/Users/asurin/bin/ffmpeg', '-f', 'concat', '-safe', '0', '-i', '{}.txt'.format(vid), '-c', 'copy',
    #       '{}.{}'.format(title, ext), '-v', '48'])
    call(['/Users/asurin/bin/ffmpeg', '-f', 'concat', '-safe', '0', '-i', '{}.txt'.format(vid), '-c', 'copy',
          '{}.{}'.format(title, ext)])


def script_main(script_name, **kwargs):
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    url = sys.argv[1]

    content = get_content(url, 2)

    vid = parse.parse_qs(parse.urlparse(url).query).get('vid')
    vid = vid[0] if vid else re.search(r'vid"*\s*:\s*"\s*([^"]+)"', content).group(1)
    title = re.search(r'<a.*?id\s*=\s*"%s".*?title\s*=\s*"(.+?)".*?>' % vid, content)
    title = re.search(r'title">([^"]+)</p>', content) if not title else title
    title = re.search(r'"title":"([^"]+)"', content) if not title else title
    title = vid if not title else title.group(1)
    logging.info('title: %s' % title)

    get_url_from_vid(vid, title)

    with open('{}.json'.format(vid), 'r') as fp:
        data = json.load(fp)
    if data.get('part_urls') is None or data.get('ext') is None:
        logging.error('scrpt_main: can\'t get video urls or ext')
    urls = data['part_urls']
    ext = data['ext']
    download(vid, title, urls, ext)


def main(**kwargs):
    script_main('v_qq_dl', **kwargs)