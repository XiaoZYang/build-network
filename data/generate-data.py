#!/usr/bin/env python
#-*-coding: utf8-*-
# vim: set fenc=utf8:
# vim: set tw=100 ts=4 sts=4 sw=4 ai ci:
#
# @description:
# @author: xiaozongyang
# @create: 2018-04-10 (Tuesday)
# @modified: 2018-04-10 (Tuesday)
import sys

def process(source):
    with open(source) as handle:
        for line in handle:
            item, count = line.split('\t')
            for i in range(int(count)):
                print(item)


if __name__ == '__main__':
    process(sys.argv[1])
