#!/usr/bin/env python

import sys
import re


README_FILE = 'README.md'
helptext = sys.stdin.read()

with open(README_FILE, 'r') as fp:
    old_readme = fp.read()

header = old_readme[:old_readme.index('# OPTIONS')]
footer = old_readme[old_readme.index('# FAQ'):]


options = helptext[helptext.index('optional arguments:') + 20:]
options = re.sub('(?m)^', '  ', options)
# print(options)
options = '# OPTIONS\n' + options + '\n'


with open(README_FILE, 'w') as fp:
    fp.write(header)
    fp.write(options)
    fp.write(footer)


