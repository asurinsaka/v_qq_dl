#!/usr/bin/env python3

from subprocess import call
import threading
import requests
import os
import logging
import sys
import time
from collections import namedtuple

# TODO Resume broken downloads
# TODO maybe create a class?


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
    '''
    generate a progress bar while downloading

    :param files:
        A list of file names to download
    :param size:
        The total size of the final file.
    :return:
        void
    '''
    # TODO add changes to progress_bar
    bar_size = 40
    char = ['-', '\\', '|', '/']
    pre = 0
    i = 0
    while True:

        # calculate size
        file_size = 0
        for file in files:
            if os.path.isfile(file + '.aria2'):
                file_size += os.path.getsize(file)
            elif os.path.isfile(file + '.download'):
                file_size += os.path.getsize(file + '.download')
            elif os.path.isfile(file):
                file_size += os.path.getsize(file + '.aria2')

        # generate the bar
        progress = int(file_size * bar_size / size)
        percent = int(file_size * 100 / size)
        sys.stdout.write("\r")
        sys.stdout.write("[")
        sys.stdout.write('-' * (progress - 1))
        if pre == progress:
            i += 1
            i %= char.__len__()
        else:
            i = 0
            pre = progress
        sys.stdout.write(char[i])
        sys.stdout.write(' ' * (bar_size - progress))
        sys.stdout.write(']\t{}/{} \t{} %  '.format(file_size, size, percent))
        sys.stdout.flush()
        if file_size == size:
            break
        time.sleep(1)
    sys.stdout.write('\n')


def download_with_aria2(location, url, out_file):
    call([location, "-x", '16', url, '-o', out_file])
    pass


# Different for different downloaders
Downloader = namedtuple('Downloader', ['location', 'downloader', 'workers'])
'''
a struct for information of Downloader

location: location of the binary file
downloader: function to call
workers: number of threads per partial file
'''


def download(vid, title, urls, size, **kwargs):

    logging.debug('download(vid={}, title={}, urls={}, size={}'.format(vid, title, urls, size))
    ext = 'mp4'
    files = []
    threads = []

    if kwargs.get('aria2_location'):
        my_downloader = Downloader(kwargs['aria2_location'], download_with_aria2, 1)
    else:
        my_downloader = Downloader(None, direct_downloader, 10)

    # TODO seperate direct downloader and aria2
    print('Begin download: ')
    for i, url in enumerate(urls):
        filename = '{}[{}].{}'.format(title, i, ext)
        files.append(filename)
        for _ in range(my_downloader.workers):
            t = threading.Thread(target=my_downloader.downloader, args=(my_downloader.location, url, filename))
            threads.append(t)

    t = threading.Thread(target=progress_bar, args=(files, size), daemon=True)
    threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    if my_downloader.downloader == direct_downloader:
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