# Author:   Dawie de Klerk
# Contact   dawiedotcom@gmail.com


import urllib2
import unittest
import os
import re
from BeautifulSoup import BeautifulSoup, NavigableString

from metadata import Metadata
from test_page import *




class Section(object):
    """
    To represent one html page of an ebook and the functionality to remove
    headers and footers.
    """

    # (no *://)(no *.*)*#*
    relative_regex = re.compile('^(?!.*://)?(?!.*\..*).*#.*')

    def __init__(self, text):

        soup = BeautifulSoup(text)
        body = soup.find('body')
        body.extract()

        self.soup = BeautifulSoup()
        self.soup.contents = body.contents
        
    def strip(self, tag, stop_condition):
        """Remove tags for which stop_condition(tag) is false."""
        while not stop_condition(tag):
            t = tag.nextSibling
            tag.extract()
            tag = t

    def removeHeader(self, **kwargs):
        """Remove generic tags at the top of a page."""
        headings = ['h1', 'h2', 'h3', 'h4']

        for i in range(5):
            h = self.soup.findAll('h' + str(i), kwargs)
            if len(h) != 0:
                break

        h = h[0]
        while h not in self.soup.contents:
            h = h.parent

        self.strip(self.soup.contents[0], lambda tag : tag == h)
    
    def removeFooter(self, tag_name, **kwargs):
        """Remove generic tags at the bottom of a page."""
        foot = self.soup.find(tag_name, kwargs)
        self.strip(foot, lambda tag : tag is None)

    def fixRelativeLinks(self):
        """Make all the relative links point to anchors in this file"""
        #aTags = self.soup.findAll(lambda tag: 'href' in [a[0] for a in tag.attrs] and tag['href'][0] == '/')
        aTags = self.soup.findAll(href=self.relative_regex) #re.compile('^/.*#,*'))
        #aTags = filter(lambda tag: tag['href']
        #print aTags
        for tag in aTags:
            tag['href'] = '#' + tag['href'].split('#')[1]



class Request(object):
    """For making http requests."""
    def __init__(self, url):
        self.url = url

    def retrieve(self, metadata):
        """Get all the html pages that belongs to an ebook."""
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
        """Request an html page over http."""
        p = urllib2.urlopen(url)
        content = p.read()
        p.close()

        return content       

    def parseRelativeLinks(self, html):
        """Find all the relative links in a web page."""
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
            u = u.split('#')[0]
            if not u in urls and u.find('/') == -1:
                urls.append(u)
        
        print(urls)
        return urls

class Book(object):
    """Represtents an ebook in html format."""
    def __init__(self, url):

        self.url = url
        self.content = ''
        self.meta = Metadata(url)

    def make(self): #, filename):
        """Retrieve a book from the given url."""
        request = Request(self.url)
        pages = request.retrieve(self.meta)

        content = ''
        for page in pages:
            section = Section(page)
            section.removeHeader(**self.meta['header-attrs'])
            section.fixRelativeLinks()
            section.removeFooter(self.meta['footer-tag'], **self.meta['footer-attrs'])

            content += section.soup.prettify() #.append(section)

        self.content = '<html><head><title>%s</title></head><body>' % self.meta['title']
        self.content += content
        self.content += '</body></html>'

        filename = self.meta.filename(ext='.html')

        f = open(filename, 'w')
        f.write(self.content)
        f.close()

    def convert(self, format_):
        """Convert the book from html to another format."""
        command = """ebook-convert 
            %s %s 
            --authors \"%s\" 
            --level1-toc //h:h1 
            --level2-toc //h:h2""" % (  self.meta.filename(ext='.html'), 
                                        self.meta.filename(ext=format_), 
                                        self.meta['author'])

        command = command.replace('\n', '')
        os.system(command)

#
# Test code.
#
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
    def test_fixLocalTags(self):
        section = Section('''<body><a id='test1'>test</a> <a id='test2' href='hi#test1'>test</a><a href='http://www.some.com/page#anchor'>there</a><a href='www.some.com/hi#tag'>there again</a></body>''')
        section.fixRelativeLinks()
        self.assertEqual(section.soup, BeautifulSoup('''<a id='test1'>test</a> <a id='test2' href='#test1'>test</a><a href='http://www.some.com/page#anchor'>there</a><a href='www.some.com/hi#tag'>there again</a>'''))


class RequestTest(unittest.TestCase):
    def setUp(self):
        self.request = Request("")
    def test_parseLinks(self):
        self.assertEqual(
                self.request.parseRelativeLinks("""
                    <a href='some_index.html'>Google</a>
                    <A href=\"second_index.html\">hi</a>
                    <A href='third.html#here'>hi</a>
                    <A href='third.html#there'>hi</a>
                    <a href='http://www.google.com'>Google</a>"""),
                ['some_index.html', 'second_index.html', 'third.html'])


if __name__ == '__main__':
    unittest.main()
