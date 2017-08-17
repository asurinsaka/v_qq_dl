#!/usr/bin/env python

from subprocess import call
import threading
import requests


def direct_downloader(location, url, out_file):
    r = requests.get(url, stream=True)
    with open(out_file, 'wb') as f:
        for chunk in r.iter_content(1024):
            if chunk:
                f.write(chunk)


def download_with_aria2(location, url, out_file):
    call([location, "-x", '16', url, '-o', out_file])
    pass


def download(vid, title, urls, ext, **kwargs):
    files = []
    threads = []
    location = None
    downloader = direct_downloader
    workers = 10    # number of thread for each part

    if kwargs.get('aria2_location'):
        downloader = download_with_aria2
        location = kwargs['aria2_location']
        workers = 1

    for i, url in enumerate(urls):
        for _ in range(workers):
            filename = '{}[{}].{}'.format(title, i, ext)
            t = threading.Thread(target=downloader, args=(location, url, filename))
            files.append(filename)
            threads.append(t)
            t.start()

    for t in threads:
        t.join()

    with open('{}.txt'.format(vid), 'w') as fp:
        for filename in files:
            fp.write("file '{}'\n".format(filename))