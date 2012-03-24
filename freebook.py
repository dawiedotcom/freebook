#!/usr/bin/python

# Author:   Dawie de Klerk
# Contact   dawiedotcom@gmail.com

import sys

import html

if __name__ == '__main__':
    book = html.Book(sys.argv[1])
    book.make()
    book.convert('.mobi')
