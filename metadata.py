# Author:   Dawie de Klerk
# Contact   dawiedotcom@gmail.com


import yaml
import unittest
import os
from test_page import *

urlToTitle = {
        "http://www.lua.org/pil/index.html" : "Programming in Lua",
        "http://mitpress.mit.edu/sicp/full-text/book/book-Z-H-4.html" : "Structure and Interpretation of Computer Programs",
        "http://book.realworldhaskell.org/read/" : "Real World Haskell"
        }

class Metadata(object):
    _defaults = {'footer-tag':None, 'footer-attrs':None, 'header-attrs':None}

    def __init__(self, url):
       
        #self.load(urlToTitle[url])
        self.data = {}
        self.data['url'] = url
        self.data['title'] = urlToTitle[url]

        self.load(self.filename())

    def filename(self, dir_ = 'books/', ext = '.yaml'):
        """Make a file name from the title"""
        return dir_ + self.data['title'].lower().replace(' ', '.') + ext 

    def load(self, filename):
        f = open(filename)
        try:
            self.data = yaml.load(f)
        finally:
            f.close()

    def __getitem__(self, key):
        if key in self.data.keys():
            return self.data[key]
        else:
            return self._defaults[key]


class MetadataTest(unittest.TestCase):
    def setUp(self):
        self.meta = Metadata("http://www.lua.org/pil/index.html")
    def test_filename1(self):
        self.assertEqual(
                self.meta.filename(), 
                "books/programming.in.lua.yaml")
    def test_load(self):
        self.meta.load("books/programming.in.lua.yaml")
        self.assertEqual(
                self.meta.data,
                pil_meta_dict)


if __name__ == '__main__':
    unittest.main()
