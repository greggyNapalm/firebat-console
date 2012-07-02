#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
from ammo.lunapark.generator import make_get_req

def main():
    PATH = [
        '/fire.yaml',
        '/simple.ammo',
        '/some/nonexistent/path',
    ]
    for p in PATH:
        sys.stdout.write(make_get_req(p, context_up={'User-Agent': 'phantom v.14'}))
    
    sys.stdout.write('0\n')

if __name__ == '__main__':
    main()
