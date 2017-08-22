#!/usr/bin/env python3

import sys

if __package__ is None:
    import os.path
    path = os.path.realpath(os.path.abspath(__file__))
    print(path)
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

import v_qq_dl

if __name__ == '__main__':
    v_qq_dl.main()