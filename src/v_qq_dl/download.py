#!/usr/bin/env python

from subprocess import call
import threading
import requests
import os
import logging
import sys
import time


# TODO Resume broken downloads

def direct_downloader(location, url, out_file):
    if os.path.isfile(out_file):
        return
    else:
        out_file += '.download'
    r = requests.get(url, stream=True)
    with open(out_file, 'wb') as f:
        for chunk in r.iter_content(1024):
            if chunk:
                f.write(chunk)


def progress_bar(files, size):
    bar_size = 40

    while True:
        file_size = 0
        for file in files:
            if os.path.isfile(file):
                file_size += os.path.getsize(file)
            elif os.path.isfile(file + '.download'):
                file_size += os.path.getsize(file + '.download')
            elif os.path.isfile(file + '.aria2'):
                file_size += os.path.getsize(file + '.aria2')


        progress = int(file_size * bar_size / size)
        percent = int(file_size * 100 / size)
        sys.stdout.write("\r")
        sys.stdout.write("[")
        sys.stdout.write('-' * progress)
        sys.stdout.write(' ' * (bar_size - progress))
        sys.stdout.write(']\t{} %'.format(percent))
        sys.stdout.flush()
        if file_size == size:
            break
        time.sleep(1)
    sys.stdout.write('\n')


def download_with_aria2(location, url, out_file):
    call([location, "-x", '16', url, '-o', out_file])
    pass


def download(data, **kwargs):
    urls = data['part_urls']
    title = data['title']
    ext = data['ext']
    size = data['total_size']
    vid = data['vid']
    files = []
    threads = []
    location = None
    downloader = direct_downloader
    workers = 10    # number of thread for each part

    if kwargs.get('aria2_location'):
        downloader = download_with_aria2
        location = kwargs['aria2_location']
        workers = 1

    print('Begin download: ')
    for i, url in enumerate(urls):
        filename = '{}[{}].{}'.format(title, i, ext)
        files.append(filename)
        for _ in range(workers):
            t = threading.Thread(target=downloader, args=(location, url, filename))
            threads.append(t)

    t = threading.Thread(target=progress_bar, args=(files, size))
    threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    if downloader == direct_downloader:
        for file in files:
            if os.path.isfile(file + '.download'):
                os.rename(file + '.download', file)
            elif os.path.isfile(file):
                continue
            else:
                logging.error('failed to download file %s' % file)
                sys.exit(1)

    with open('{}.txt'.format(vid), 'w') as fp:
        for filename in files:
            fp.write("file '{}'\n".format(filename))

    return files