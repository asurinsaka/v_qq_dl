#!/usr/bin/env python3

from subprocess import call
from pathos.threading import ThreadPool
from multiprocessing import Pool
import threading
import requests
import os
import logging
import sys
import time
from random import randint
import pickle
from collections import namedtuple

# TODO Resume broken downloads
# TODO maybe create a class?

FileInfo = namedtuple('FileInfo', 'url filename size')
lock = threading.Lock()


def read_data(filepath):
    with open(filepath, 'rb') as fin:
        return pickle.load(fin)


def write_data(filepath, data):
    with open(filepath, 'wb') as fout:
        return pickle.dump(data, fout)


# def direct_downloader(url, out_file, info_file, headers):
#     if os.path.isfile(out_file):
#         return
#     else:
#         out_file += '.download'
#         try:
#             r = requests.get(url, stream=True, headers=headers)
#             with open(out_file, 'ab') as f:
#                 try:
#                     for chunk in r.iter_content(1024*1024):
#                         if chunk:
#                             f.write(chunk)
#                             f.flush()
#                 except Exception as e:
#                     logging.exception(e)
#                     with open(info_file, 'ab') as fp:
#                         fp.write(str(size))
#         except Exception as e:
#             logging.exception(e)
#             raise


def get_size(url):
    logging.debug('get_size: %s' % url)
    time.sleep(randint(0, 5))
    r = requests.head(url)
    size = int(r.headers['content-length'])
    return size


# def support_continue(url):
#     headers = {
#         'Range': 'bytes=0-4'
#     }
#     try:
#         r = requests.head(url, headers=headers)
#         crange = r.headers['content-range']
#         size = int(re.match(r'^bytes 0-4/(\d+)$', crange).group(1))
#         return True
#     except:
#         logging.exception('support_continue: dose not support continuous download')
#         return False


def direct_download(urls, title, ext):

    logging.debug('direct_download: %s' % title)
    print('Begin download: ')
    files = []
    results = {}
    info_files = []
    block_size = 2048 * 1024
    buffer_size = 512 * 1024
    thread_count = 10 if len(urls) > 10 else len(urls)

    pool = Pool(processes=thread_count)
    for i, url in enumerate(urls):
        filename = '{}[{}].{}'.format(title, i, ext)
        info_file = '{}[{}].info'.format(title, i)
        files.append(filename)
        info_files.append(info_file)
        results[i] = pool.apply_async(get_size, [url],)

    pool.close()
    pool.join()
    sizes = {i: result.get() for i, result in results.items()}
    logging.debug('direct_download: sizes: {}'.format(sizes))
    sizes = [sizes[i] for i in range(len(sizes))]
    logging.debug('direct_download: sizes: {}'.format(sizes))

    total_size = sum(sizes)
    thread_count = 100
    args = []
    fps = []

    for i, (url, filename, info_file, size) in enumerate(zip(urls, files, info_files, sizes)):
        if os.path.isfile(filename):
            continue

        workname = filename + '.download'

        if os.path.isfile(info_file):
            _x, blocks = read_data(info_file)
        else:
            block_count, remain = divmod(size, block_size)

            blocks = [[i * block_size, i * block_size, (i+1) * block_size - 1] for i in range(block_count)]
            blocks[-1][-1] += remain

            with open(workname, 'wb') as fp:
                fp.write(b'')

        file_info = FileInfo(url, filename, size)

        threading.Thread(target=_monitor, args=(file_info, blocks, info_file)).start()

        fp = open(workname, 'rb+')
        fps.append(fp)
        args.extend((url, blocks[i], fp, buffer_size) for i in range(len(blocks)) if blocks[i][1] < blocks[i][2])

    if thread_count > len(args):
        thread_count = len(args)

    if thread_count == 0:
        return files

    threading.Thread(target=_progress_bar, args=(files, total_size)).start()
    pool = ThreadPool(thread_count)
    pool.map(_worker, args)
    pool.close()
    pool.join()

    for fp in fps:
        fp.close()
    for i, (url, filename, info_file, size) in enumerate(zip(urls, files, info_files, sizes)):

        if not os.path.exists(filename):
            workname = filename + '.download'
            os.rename(workname, filename)

        if os.path.exists(info_file):
            os.remove(info_file)

        assert os.path.exists(filename) and os.path.getsize(filename) >= size, \
            '%s did not finish, %s / %s' % (filename, os.path.getsize(filename), size)
        # assert all([block[1] >= block[2] for block in blocks]) is True

    return files


def _worker(args):
    url, block, fp, buffer_size = args
    headers = {'Range': 'bytes=%s-%s' % (block[1], block[2])}
    r = requests.get(url, stream=True, headers=headers)
    for chunk in r.iter_content(buffer_size):
        with lock:
            fp.seek(block[1])
            fp.write(chunk)
            block[1] += len(chunk)
        # print(block)


def _monitor(file_info, blocks, info_file):
    while True:
        with lock:
            percent = sum([block[1] - block[0] for block in blocks]) * 100 / file_info.size
            if percent >= 100:
                break
            write_data(info_file, (file_info, blocks))
        time.sleep(2)
        # print(blocks)


def _progress_bar(files, size):
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

        count = 0
        # calculate size
        file_size = 0
        for file in files:
            if os.path.isfile(file + '.aria2'):
                file_size += os.path.getsize(file)
            elif os.path.isfile(file + '.download'):
                file_size += os.path.getsize(file + '.download')
            elif os.path.isfile(file):
                file_size += os.path.getsize(file)
                count += 1

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
        sys.stdout.write(']\t{}/{} \t{} %  parts completed: {} / {}'.format(file_size, size, percent, count, len(files)))
        sys.stdout.flush()
        if file_size >= size:
            break
        else:
            time.sleep(1)
    # sys.stdout.write("\r")
    # sys.stdout.write("[")
    # sys.stdout.write('-' * (bar_size))
    # sys.stdout.write(']\t{}/{} \t{} %  parts completed: {} / {}'.format(file_size, size, 100))
    sys.stdout.write('\n')


# TODO: maybe not allocate space before download, add progress bar
def download_with_aria2(location, urls, title, ext):
    """
    use aria2 to download the video segments
    :param location:  The location of the aria2 program
    :param urls:  The urls of the video segments to download
    :param title:  The title of the video
    :param ext:  The extension of the video file
    :return:  The names of the file downloaded
    """
    files = []
    threads = []
    for i, url in enumerate(urls):
        filename = '{}[{}].{}'.format(title, i, ext)
        files.append(filename)
        t = threading.Thread(target=call, args=([location,  "-x", '16', url, '-o', filename], ))
        threads.append(t)
        t.start()

    threads.append(t)

    for t in threads:
        t.join()

    return files


def download(vid, title, urls, **kwargs):

    logging.debug('download(vid={}, title={}, urls={}'.format(vid, title, urls))
    ext = 'mp4'

    if kwargs.get('aria2_location'):
        files = download_with_aria2(kwargs['aria2_location'], urls, title, ext)
    else:
        files = direct_download(urls, title, ext)

    with open('{}.txt'.format(vid), 'w') as fp:
        for filename in files:
            fp.write("file '{}'\n".format(filename))

    return files
