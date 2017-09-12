#!/usr/bin/env python
from .common import get_content_through_proxy, get_part_info, get_content
import re
import logging
import json
import time
import hashlib


def get_info(url):
    content = get_content(url, 2)

    match = re.search(r'#curid=(.+)_', url) or re.search(r'tvId:(.+),', content)
    vid = match.group(1) if match else None

    title = re.search(r'tvName:"(.+)",', content)
    title = title.group(1) if title else None
    print(content)
    return vid, title


def get_vms(tvid, vid):
    t = int(time.time() * 1000)
    src = '76f90cbd92f94a2e925d83e8ccd22cb7'
    key = 'd5fb4bd9d50c4be6948c97edd7254b0e'
    sc = hashlib.new('md5', bytes(str(t) + key  + vid, 'utf-8')).hexdigest()
    vmsreq= url = 'http://cache.m.iqiyi.com/tmts/{0}/{1}/?t={2}&sc={3}&src={4}'.format(tvid,vid,t,sc,src)
    return json.loads(get_content(vmsreq, 2))


def get_quality(info):
    vd_2_id = {10: '4k', 19: '4k', 5:'BD', 18: 'BD', 21: 'HD_H265', 2: 'HD', 4: 'TD', 17: 'TD_H265', 96: 'LD', 1: 'SD', 14: 'TD'}
    stream_sort = ['BD', 'TD', 'TD_265', 'HD', 'HD_H265']
    for stream in info['data']['vidl']:
        if stream['vd'] == 4:
            return stream


def get_url_from_vid(vid, title):
    logging.debug('get_url_from_vid(vid: {}, title: {}'.format(vid, title))

    # a json file to save temporary information in case download failed
    try:
        with open('{}.json'.format(vid), 'r') as fp:
            download_dict = json.load(fp)
            return download_dict['part_urls'], download_dict['size']
    except FileNotFoundError:
        download_dict = {'vid': vid, 'title': title}

    info_api = 'http://mixer.video.iqiyi.com/jp/mixin/videos/{}'.format(vid)
    info = get_content(info_api, 2)
    video_json = json.loads(re.search(r'tvInfoJs=(.*)', info).group(1))
    print(json.dumps(video_json, indent=4, sort_keys=True))
    vid = video_json['vid']
    tvid = video_json['tvId']
    info = get_vms(tvid, vid)
    stream = get_quality(info)
    print(stream)
    return [stream['m3u']], title


