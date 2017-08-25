#!/usr/bin/env python3

import logging
import argparse


# TODO write test
def _real_main(**kwargs):
    logging.debug('_real_main')
    parser = argparse.ArgumentParser(description='Download videos from v.qq.com', prog='v_qq_dl')
    parser.add_argument('url')
    parser.add_argument('--ffmpeg_location', default='ffmpeg', action='store', help='Location of the ffmpeg binary')
    parser.add_argument('--aria2_location', action='store', help='Location of the aria2 binary')
    parser.add_argument('-v', '--verbose', '--debug', dest='verbose', action='store_true', help='Print various debugging information')
    parser.add_argument('--keep_tmp', action='store_true', help='Keep temporary files')
    args = parser.parse_args()
    logging.debug(args)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    kwargs.update(vars(args))

    from .common import main
    main(**kwargs)


def main(**kwargs):
    logging.basicConfig(format='%(levelname)s:\t%(message)s')
    try:
        _real_main(**kwargs)
    except Exception as e:
        logging.exception(e)
        raise

