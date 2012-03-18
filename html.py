# Author:   Dawie de Klerk
# Contact   dawiedotcom@gmail.com


import urllib2
import unittest
import os
from BeautifulSoup import BeautifulSoup, NavigableString

from metadata import Metadata
from test_page import *




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
    
    def removeFooter(self, *args, **kwargs):
        foot = self.soup.find(args, kwargs)
        #print foot, kwargs
        self.strip(foot, lambda tag : tag is None)



class Request(object):
    def __init__(self, url):
        self.url = url

    def retrieve(self, metadata):

        index_page = self.retrieveURL(self.url)
        section = Section(index_page)
        section.removeHeader()
        section.removeFooter(metadata['footer-tag'], **metadata['footer-attrs'])
        index_page = str(section.soup)
        #print index_page

        toc = self.parseRelativeLinks(index_page)
        pages = []

        url_base = '/'.join(self.url.split('/')[:-1])
        for i, page in enumerate(toc):
            #if i == 3:
            #    break

            full_url = url_base + '/' + page
            print "retrieving page: %s (%i/%i)" %(full_url, i, len(toc)) 
            pages.append(self.retrieveURL(full_url))

        return pages       

    def retrieveURL(self, url):
        p = urllib2.urlopen(url)
        content = p.read()
        p.close()

        return content       

    def parseRelativeLinks(self, html):

        HTML = html.upper()
        a_tag = HTML.find('CONTENTS')
        href = 0
        urls = []

        while (True):
            a_tag = HTML.find('<A ', a_tag + 1)
            if (a_tag == -1):
                break
            href  = HTML.find('HREF=', a_tag)
            quote = HTML[href + len('HREF=')]

            open_quote = HTML.find(quote, href) + 1
            close_quote = HTML.find(quote, open_quote + 1)
            
            u = html[open_quote:close_quote]
            if not u in urls:
                urls.append(u)
        
        urls = filter(lambda u: u.find('/') == -1, urls)
        urls = filter(lambda u: u[0] != '#', urls)
        urls = map(lambda s: s.split('#')[0], urls)
        urls_ = []
        for u in urls:
            if not u in urls_:
                urls_.append(u)
        urls = urls_
        print(urls)
        return urls

class Book(object):
    def __init__(self, url):
        self.url = url
        self.content = ''
        self.meta = Metadata(url)

    def make(self): #, filename):

        request = Request(self.url)
        pages = request.retrieve(self.meta)

        sections = []
        for page in pages:
            section = Section(page)
            section.removeHeader()
            section.removeFooter(self.meta['footer-tag'], **self.meta['footer-attrs'])

            self.content += section.soup.prettify() #.append(section)

        self.content = '<html><head><title>Programming in Lua</title></head><body>' + self.content
        self.content += '</body></html>'

        filename = self.meta.filename(ext = '.html')

        f = open(filename, 'w')
        f.write(self.content)
        f.close()

    def convert(self, format_):
        command = """ebook-convert 
            %s %s 
            --authors \"%s\" 
            --level1-toc //h:h1 
            --level2-toc //h:h2""" % (  self.meta.filename(ext='.html'), 
                                        self.meta.filename(ext=format_), 
                                        self.meta['author'])

        command = command.replace('\n', '')
        os.system(command)



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
        section.removeFooter('hr')
        self.assertEqual(section.soup, BeautifulSoup(preface_no_header_footer.replace('\n','')))

class RequestTest(unittest.TestCase):
    def setUp(self):
        self.request = Request("")
    def test_parseLinks(self):
        self.assertEqual(
                self.request.parseRelativeLinks("""
                    <a href='some_index.html'>Google</a>
                    <A href=\"second_index.html\">hi</a>
                    <a href='http://www.google.com'>Google</a>"""),
                ['some_index.html', 'second_index.html'])


if __name__ == '__main__':
    unittest.main()
