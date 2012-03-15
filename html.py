# Author:   Dawie de Klerk
# Contact   dawiedotcom@gmail.com


import urllib2
import unittest
from test_page import *
from BeautifulSoup import BeautifulSoup, NavigableString

def retrieveURL(self, url):
    p = urllib2.urlopen(url)
    content = p.read()
    p.close()

    return content


class Section(object):

    def __init__(self, text):
        #self.url = url
        
        #text = seld._retrieve(url)
        soup = BeautifulSoup(text)
        body = soup.find('body')
        body.extract()

        self.soup = BeautifulSoup()
        self.soup.contents = body.contents
        
    def strip(self, tag, stop_condition):
        while not stop_condition(tag):
            t = tag.nextSibling
            tag.extract()
            tag = t

    def removeHeader(self):
        headings = ['h1', 'h2', 'h3', 'h4']

        for i in range(5):
            h = self.soup.findAll('h' + str(i))
            if len(h) != 0:
                break

        h = h[0]
        while h not in self.soup.contents:
            h = h.parent

        self.strip(self.soup.contents[0], lambda tag : tag == h)
    
    def removeFooter(self):
        hr = self.soup.find('hr')
        self.strip(hr, lambda tag : tag is None)




class SectionTest(unittest.TestCase):
    def setUp(self):
        pass
    def test_init1(self):
        section = Section(test_record2)
        self.assertEqual(section.soup, BeautifulSoup("This is a test, lets see if it works. I really hope it does!"));
    def test_init2(self):
        section = Section(preface_html)
        self.assertEqual(section.soup, BeautifulSoup(preface_body))
    def test_removeHeader1(self):
        section = Section("<body><p>hi</p><p><h1>heading</h1></p><p>some text</p><p>some more text</p></body>")
        section.removeHeader()
        self.assertEqual(section.soup, BeautifulSoup("<p><h1>heading</h1></p><p>some text</p><p>some more text</p>"))
    def test_removeHeader2(self):
        section = Section(preface_html)
        section.removeHeader()
        self.assertEqual(section.soup, BeautifulSoup(preface_no_header))
    def test_removeFooter2(self):
        section = Section(preface_html.replace('\n', ''))
        section.removeHeader()
        section.removeFooter()
        self.assertEqual(section.soup, BeautifulSoup(preface_no_header_footer.replace('\n','')))

if __name__ == '__main__':
    unittest.main()
