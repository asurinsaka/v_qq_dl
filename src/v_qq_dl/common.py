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
from importlib import import_module
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


# def url_info(url):
#     try:
#         response = urlopen_with_retry(2, request.Request(url))
#     except Exception as e:
#         logging.debug('url_info: %s %s' % (e, url))
#
#     headers = response.headers
#
#     type = headers['content-type']
#     type_mapping = {
#         'video/3gpp': '3gp',
#         'video/f4v': 'flv',
#         'video/mp4': 'mp4',
#         'video/MP2T': 'ts',
#         'video/quicktime': 'mov',
#         'video/webm': 'webm',
#         'video/x-flv': 'flv',
#         'video/x-ms-asf': 'asf',
#         'audio/mp4': 'mp4',
#         'audio/mpeg': 'mp3',
#         'audio/wav': 'wav',
#         'audio/x-wav': 'wav',
#         'audio/wave': 'wav',
#         'image/jpeg': 'jpg',
#         'image/png': 'png',
#         'image/gif': 'gif',
#         'application/pdf': 'pdf',
#     }
#     if type in type_mapping:
#         ext = type_mapping[type]
#     else:
#         type = None
#
#     if headers['transfer-encoding'] != 'chunked':
#         size = headers['content-length'] and int(headers['content-length'])
#     else:
#         size = None
#
#     return type, ext, size


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


def script_main(script_name, **kwargs):
    logging.debug('script_main')
    url = kwargs['url']
    ffmpeg_loacation = kwargs['ffmpeg_location']

    netloc = parse.urlparse(url).netloc

    if 'qq' in netloc:
        m = import_module('.qq', 'v_qq_dl')
        vid, title = m.get_info(url)
        urls, size, title = m.get_url_from_vid(vid, title)
        ext = 'mp4'
    elif 'iqiyi' in netloc:
        m = import_module('.iqiyi', 'v_qq_dl')
        vid, title = m.get_info(url)
        urls, title = m.get_url_from_vid(vid, title)
        for url in urls:
            call([ffmpeg_loacation, '-y', '-i', url, '-c', 'copy', '-bsf:a', 'aac_adtstoasc', title+'.mp4'])
        return

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