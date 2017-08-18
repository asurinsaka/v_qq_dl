#!/usr/bin/env python

import sys
import logging
from urllib import request, error, parse
import socket
import re
import json
import os
import glob
from bs4 import BeautifulSoup
import random
from .download import download
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


def pick_a_chinese_proxy():
    try:
        with open('proxy.json', 'r') as fp:
            data = json.load(fp)
    except FileNotFoundError:
        data = None
    if data and 'proxy_list' in data.keys():
        all_proxies = data['proxy_list']
    else:
        content = request.urlopen(
            "http://www.proxynova.com/proxy-server-list/country-cn/").read()
        soup = BeautifulSoup(content, 'lxml')
        all_proxies = []
        for row in soup.find_all('tr')[1:]:
            try:
                ip = row.find_all('td')[0].text.strip()         # document.write('23222.1'.substr(2) + '25.32.75')
                ip = re.search(r"'([0-9.]+)'.*'([0-9.]+)'", ip)
                ip = ip.group(1)[2:] + ip.group(2)
                port = row.find_all('td')[1].text.strip()
                cur_proxy = "{}:{}".format(ip, port)
                all_proxies.append(cur_proxy)
            except Exception as e:
                logging.debug('pick_a_chinese_proxy: %s' % e)
        if all_proxies:
            data = {'proxy_list': all_proxies}
            with open('proxy.json', 'w') as fp:
                json.dump(data, fp)
    return random.choice(all_proxies)

def get_content_through_proxy(url):

    logging.debug('get_content_through_proxy: %s' % url)
    while True:
        addr = pick_a_chinese_proxy()
        try:
            proxy = request.ProxyHandler({'http': addr})
            opener = request.build_opener(proxy)
            request.install_opener(opener)
            req = request.Request(url)
            response = request.urlopen(req, timeout=3)
            data = response.read()
        except Exception as e:
            logging.debug('get_content_through_proxy:  %s %s ' % (addr, e))
        else:
            data = data.decode('utf-8')
            logging.debug('get_content_through_proxy: %s %s' % (data, addr))
            return data


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

    while video_json['exem'] == 1:
        info = get_content_through_proxy(info_api)
        video_json = json.loads(re.search(r'QZOutputJson=(.*);', info).group(1))

    if video_json['exem'] != 0:
        logging.error(video_json['msg'])

    download_dict[info_api] = info

    fn_pre = video_json['vl']['vi'][0]['lnk']
    title = video_json['vl']['vi'][0]['ti']
    host = video_json['vl']['vi'][0]['ul']['ui'][0]['url']
    streams = video_json['fl']['fi']
    seg_cnt = video_json['vl']['vi'][0]['cl']['fc']

    download_dict['title'] = title
    if seg_cnt == 0:
        seg_cnt = 1

    best_quality = streams[-1]['name']
    part_format_id = streams[-1]['id']

    download_dict['quality'] = best_quality

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
        download_dict['total_size'] = total_size
        with open('{}.json'.format(vid), 'w') as fp:
            json.dump(download_dict, fp, sort_keys=True, indent=4)

    return download_dict


def script_main(script_name, **kwargs):
    logging.debug('script_main')
    url = kwargs['url']
    ffmpeg_loacation = kwargs['ffmpeg_location']


    content = get_content(url, 2)

    vid = parse.parse_qs(parse.urlparse(url).query).get('vid')
    vid = vid[0] if vid else re.search(r'vid"*\s*:\s*"\s*([^"]+)"', content).group(1)
    title = re.search(r'<a.*?id\s*=\s*"%s".*?title\s*=\s*"(.+?)".*?>' % vid, content)
    title = re.search(r'title">([^"]+)</p>', content) if not title else title
    title = re.search(r'"title":"([^"]+)"', content) if not title else title
    title = vid if not title else title.group(1)
    logging.info('title: %s' % title)

    data = get_url_from_vid(vid, title)

    # print(data)
    print('title: %s' % data['title'])
    print('type: %s' % data['ext'])
    print('size: %s' % data['total_size'])
    print('quality: %s' % data['quality'])


    urls = data['part_urls']
    ext = data['ext']
    title = data['title']
    total_size = data['total_size']

    logging.debug('script_main: total_size : %s' % data['total_size'])

    part_files = download(data, **kwargs)

    # TODO try to remove dependency
    call([ffmpeg_loacation, '-f', 'concat', '-safe', '0', '-i', '{}.txt'.format(vid), '-c', 'copy',
          '{}.{}'.format(title, ext)])


    # compare file size with total size and clean up


    if not os.path.isfile('{}.{}'.format(title, ext)):
        print("Something went wrong")
        sys.exit(1)

    files_size = 0
    # TODO fix the match
    for file in part_files:
        files_size += os.path.getsize(file)

    if not kwargs['keep_tmp'] and files_size == total_size <= os.path.getsize('{}.{}'.format(title, ext)):
        for file in part_files:
            os.remove(file)
        os.remove('{}.json'.format(vid))
        os.remove('{}.txt'.format(vid))


def main(**kwargs):
    script_main('v_qq_dl', **kwargs)