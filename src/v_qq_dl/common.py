#!/usr/bin/env python3

import sys
import logging
from urllib import request, error, parse
import socket
import re
import json
import os
from bs4 import BeautifulSoup
import random
from .download import download
from subprocess import call
import threading
import time


def urlopen_with_retry(attempt, *args, **kwargs):
    for i in range(attempt):
        try:
            return request.urlopen(*args, **kwargs)
        except socket.timeout:
            logging.exception('request attemp %s timeout: %s' % str(i + 1))
            raise
        except error.HTTPError as http_error:
            logging.exception('HTTP Error with code{}'.format(http_error.code))
            raise
        except Exception as e:
            logging.exception('urlopen_with_retry: %s' %e)
            raise


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
    logging.debug(data)
    data = data.decode('utf-8', 'ignore')
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
                td0 = row.find_all('td')[0].text.strip()         # document.write('23222.1'.substr(2) + '25.32.75')
                raw_ip = re.search(r"'([0-9.]+)'.*'([0-9.]+)'", td0)
                ip = raw_ip.group(1)[2:] + raw_ip.group(2)
                port = row.find_all('td')[1].text.strip()
                cur_proxy = "{}:{}".format(ip, port)
                all_proxies.append(cur_proxy)
            except Exception as e:                              # may raise exception when encounter google ads
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


def get_part_info(part, url, part_info):
    """
    Get the content for each video part
    :param part: The index of current part
    :param url: address to get the information
    :param part_info: a list to store the results
    :return: None
    """
    time.sleep(random.randint(0, 5))        # to get rid of the 503 error
    part_info[part] = get_content(url, 2)


def get_url_from_vid(vid, title):
    """
    Get the file urls
    :param vid: The vid of the video
    :param title: The title of the video
    :return: A dictionary with video segment info
    """
    logging.debug('get_url_from_vid(vid: {}, title: {}'.format(vid, title))
    # a json file to save temporary information in case download failed
    try:
        with open('{}.json'.format(vid), 'r') as fp:
            download_dict = json.load(fp)
            return download_dict['part_urls'], download_dict['size']
    except FileNotFoundError:
        download_dict = {'vid': vid, 'title': title}

    info_api = 'http://vv.video.qq.com/getinfo?otype=json&appver=3.2.19.333&platform=11&defnpayver=1&vid={}'.format(vid)

    info = get_content(info_api, 2)
    video_json = json.loads(re.search(r'QZOutputJson=(.*);', info).group(1))
    logging.debug(video_json)

    while video_json['exem'] == 1:
        info = get_content_through_proxy(info_api)
        video_json = json.loads(re.search(r'QZOutputJson=(.*);', info).group(1))

    if video_json['exem'] != 0:
        logging.error(video_json['msg'])

    fn_pre = video_json['vl']['vi'][0]['lnk']
    title = video_json['vl']['vi'][0]['ti']
    host = video_json['vl']['vi'][0]['ul']['ui'][0]['url']
    streams = video_json['fl']['fi']
    seg_cnt = video_json['vl']['vi'][0]['cl']['fc']

    download_dict['title'] = title
    if seg_cnt == 0:
        seg_cnt = 1

    best_quality = streams[-1]['name']
    best_quality_cname = streams[-1]['cname']
    size = streams[-1]['fs']
    part_format_id = streams[-1]['id']

    download_dict['quality'] = best_quality

    logging.debug(video_json)
    print('title: %s' % title)
    # print('type: %s' % data['type'])
    print('size: %.2f KB' % (size / 1024))
    print('quality: %s' % best_quality_cname)
    print('getting video segment urls')

    logging.debug('get_url_from_vid: {} parts'.format(seg_cnt+1))

    if download_dict.get('part_urls'):
        return download_dict

    threads = []
    part_info_dict = {}

    # get the video segment information through api
    for part in range(1, seg_cnt+1):
        filename = fn_pre + '.p' + str(part_format_id % 10000) + '.' + str(part) + '.mp4'
        key_api = "http://vv.video.qq.com/getkey?otype=json&platform=11&format={}&vid={}&filename={}&appver=3.2.19.333".format(
            part_format_id, vid, filename)

        t = threading.Thread(target=get_part_info, args=(part, key_api, part_info_dict))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    logging.debug(part_info_dict)

    part_urls = []
    for part in range(1, seg_cnt+1):
        filename = fn_pre + '.p' + str(part_format_id % 10000) + '.' + str(part) + '.mp4'
        key_json = json.loads(re.search(r'QZOutputJson=(.*);', part_info_dict[part]).group(1))
        vkey = key_json['key']
        url = '{}{}?vkey={}'.format(host, filename, vkey)
        part_urls.append(url)
    else:
        download_dict['part_urls'] = part_urls
        download_dict['size'] = size
        with open('{}.json'.format(vid), 'w') as fp:
            json.dump(download_dict, fp, sort_keys=True, indent=4)

    return part_urls, size


def script_main(script_name, **kwargs):
    logging.debug('script_main')
    url = kwargs['url']
    ffmpeg_loacation = kwargs['ffmpeg_location']
    ext = 'mp4'

    content = get_content(url, 2)

    vid = parse.parse_qs(parse.urlparse(url).query).get('vid')
    vid = vid[0] if vid else re.search(r'vid"*\s*:\s*"\s*([^"]+)"', content).group(1)
    title = re.search(r'<a.*?id\s*=\s*"%s".*?title\s*=\s*"(.+?)".*?>' % vid, content)
    title = re.search(r'title">([^"]+)</p>', content) if not title else title
    title = re.search(r'"title":"([^"]+)"', content) if not title else title
    title = vid if not title else title.group(1)
    logging.info('title: %s' % title)

    urls, size = get_url_from_vid(vid, title)

    part_files = download(vid, title, urls, **kwargs)

    # TODO try to remove dependency
    if os.path.isfile('{}.{}'.format(title, ext)):
        os.remove('{}.{}'.format(title, ext))
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

    if not kwargs['keep_tmp'] and files_size == size <= os.path.getsize('{}.{}'.format(title, ext)):
        for file in part_files:
            os.remove(file)
        os.remove('{}.json'.format(vid))
        os.remove('{}.txt'.format(vid))


def main(**kwargs):
    script_main('v_qq_dl', **kwargs)