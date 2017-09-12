#!/usr/bin/env python
import json
import logging
import re
import threading
from .common import get_content_through_proxy, get_part_info, get_content
from urllib import parse


def get_info(url):
    content = get_content(url, 2)

    print(content)
    vid = parse.parse_qs(parse.urlparse(url).query).get('vid')
    vid = vid[0] if vid else re.search(r'vid"*\s*:\s*"\s*([^"]+)"', content).group(1)
    title = re.search(r'<a.*?id\s*=\s*"%s".*?title\s*=\s*"(.+?)".*?>' % vid, content)
    title = re.search(r'title">([^"]+)</p>', content) if not title else title
    title = re.search(r'"title":"([^"]+)"', content) if not title else title
    title = vid if not title else title.group(1)
    logging.info('title: %s' % title)
    return vid, title


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

    return part_urls, size, title