#!/usr/bin/env python3

import logging
import argparse

def _real_main(**kwargs):

    parser = argparse.ArgumentParser(description='Download videos from v.qq.com', prog='v_qq_dl')
    parser.add_argument('url')
    parser.add_argument('--ffmpeg_location', action='store')
    parser.add_argument('--aria2_location', action='store')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--keep_tmp', action='store_true')
    args = parser.parse_args()
    print(args)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    kwargs.update(vars(args))

    from .common import main
    main(**kwargs)

def main(**kwargs):
    logging.basicConfig(format='%(levelname)s:\t%(message)s')
    try:
        _real_main(**kwargs)
    except Exception as e:
        logging.debug(e)

