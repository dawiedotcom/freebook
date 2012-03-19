# Author:   Dawie de Klerk
# Contact   dawiedotcom@gmail.com

import sys

import html

if __name__ == '__main__':
    book = html.Book(sys.argv[1])
    #book = html.Book('http://book.realworldhaskell.org/read/')
    book.make()
    book.convert('.mobi')
