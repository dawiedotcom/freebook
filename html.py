# Author:   Dawie de Klerk
# Contact   dawiedotcom@gmail.com


import urllib
import urllib2
import urlparse
import unittest
import os
import subprocess
import re
from BeautifulSoup import BeautifulSoup, NavigableString

from metadata import Metadata
from progressbar import ProgressBar
from test_page import *

def removeDup(xs):
    '''Remove duplicates from a list without changing the order of the list'''
    if xs == []:            return []
    elif xs[0] in xs[1:]:   return removeDup(xs[1:])
    else:                   return [xs[0]] + removeDup(xs[1:])


class Section(object):
    """
    To represent one html page of an ebook and the functionality to remove
    headers and footers.
    """

    # (no *://)(no *.*)*#*
    #relative_regex = re.compile('^(?!.*://)?(?!.*\..*\.).*#.*')
    relative_regex = re.compile('^(?!.*://).*#.*')

    def __init__(self, text):

        # Put everything in the <body> tag in a BeautifulSoup object.
        soup = BeautifulSoup(text)
        body = soup.find('body')
        body.extract()

        self.soup = BeautifulSoup()
        self.soup.contents = body.contents

        # A safe place for all the image urls.
        self.images = []
        
    def strip(self, tag, stop_condition):
        """Remove tags for which stop_condition(tag) is false."""
        while not stop_condition(tag):
            t = tag.nextSibling
            tag.extract()
            tag = t

    def removeTocHeader(self):
        '''Remove everything before the first occurence of "Content"'''
        h = self.soup.find(text=re.compile('Content'))
        if h is None: 
            return 

        while h not in self.soup.contents:
            h = h.parent

        self.strip(self.soup.contents[0], lambda tag : tag == h)
    
    def removeHeader(self, **kwargs):
        """Remove generic tags at the top of a page."""

        for i in range(5):
            h = self.soup.find('h' + str(i), kwargs)
            if not h is None: #len(h) != 0:
                break

        while h not in self.soup.contents:
            h = h.parent

        self.strip(self.soup.contents[0], lambda tag : tag == h)
    
    def removeFooter(self, tag_name, **kwargs):
        """Remove generic tags at the bottom of a page."""
        foot = self.soup.find(tag_name, kwargs)
        self.strip(foot, lambda tag : tag is None)

    def fixRelativeLinks(self):
        """Make all the relative links point to anchors in this file"""
        aTags = self.soup.findAll(href=self.relative_regex) 
        for tag in aTags:
            #print tag['href'] + " -> " + '#' + tag['href'].split('#')[1]
            tag['href'] = '#' + tag['href'].split('#')[1]

    def getImages(self, meta):
        '''Download all the images and change img tags accordingly.'''
        imgTags = self.soup.findAll('img')
        #parsed = list(urlparse.urlparse(meta['url']))

        for tag in imgTags:
            # Keep the web location of the image and change the source to the local
            # copy.
            self.images.append(tag['src'])
            filename = tag['src'].split('/')[-1]
            tag['src'] = os.path.join(meta.filename(dir_='', ext=''), filename)

        return self.images
 

class Request(object):
    """For making http requests."""
    
    relative_regex = re.compile('^(?!.*://).*html')

    def __init__(self, url):
        self.url = url

    def retrieve(self, metadata):
        """Get all the html pages that belongs to an ebook."""
        index_page = self.retrieveURL(self.url)
        section = Section(index_page)

        section.removeTocHeader()
        section.removeFooter(metadata['footer-tag'], **metadata['footer-attrs'])

        toc = self.parseRelativeLinks(section.soup)
        #print toc
        pages = []
        
        progress = ProgressBar(len(toc), message='Retrieving HTML:\t')

        #url_base = '/'.join(self.url.split('/')[:-1])
        for i, page in enumerate(toc):
            #if i == 2:
            #    break
            progress.update(i+1)    

            full_url = metadata.fullURL(page) #url_base + '/' + page
            #print "retrieving page: %s (%i/%i)" %(page, i+1, len(toc)) 
            pages.append(self.retrieveURL(full_url))

        return pages       

    def retrieveURL(self, url):
        """Request an html page over http."""
        p = urllib2.urlopen(url)
        content = p.read()
        p.close()

        return content       

    def parseRelativeLinks(self, soup):
        """Find all the relative links in a web page."""
        urls = [tag['href'] for tag in soup.findAll(href=self.relative_regex)]
        urls = map(lambda u: u.split('#')[0], urls)
        return removeDup(urls)

    def retrieveImages(self, meta, imageSrc):
        '''Download all the images.'''

        # Parse url
        parsed = list(urlparse.urlparse(meta['url']))

        # Create a folder for the images.
        if not os.path.exists(meta.filename(ext='')):
            os.makedirs(meta.filename(ext=''))

        progress = ProgressBar(len(imageSrc), 'Retrieving images:\t')
        for i, src in enumerate(imageSrc):
            progress.update(i+1)

            # Get the filename, output path and web location.
            filename = src.split('/')[-1]
            outpath = os.path.join(meta.filename(ext=''), filename)
            parsed[2] = src

            # Get the image based on how the url was given.
            if not os.path.exists(outpath):
                if src.lower().startswith('http'):
                    urllib.urlretrieve(src, outpath)
                elif src[0] == '/':
                    #print(urlparse.urlunparse(parsed) + ' -> ' +  outpath)
                    urllib.urlretrieve(urlparse.urlunparse(parsed), outpath)
                else:
                    #print(meta.fullURL(src) + ' -> ' +  outpath)
                    urllib.urlretrieve(meta.fullURL(src), outpath)

            #src = os.path.join(meta.filename(dir_='', ext=''), filename)



class Book(object):
    """Represtents an ebook in html format."""
    def __init__(self, title):

        self.meta = Metadata(title)
        self.url = self.meta['url']

        print('%(title)s from %(url)s' % self.meta)
        self.content = ''

    def make(self): #, filename):
        """Retrieve a book from the given url."""

        # Get all the html content of the book
        request = Request(self.url)
        pages = request.retrieve(self.meta)

        # Remove headers, footers, fix relative links
        content = ''
        images = []
        progress = ProgressBar(len(pages), message='Removing non content:\t')
        for i, page in enumerate(pages):
            progress.update(i+1)

            section = Section(page)
            section.removeHeader(**self.meta['header-attrs'])
            section.removeFooter(self.meta['footer-tag'], **self.meta['footer-attrs'])
            section.fixRelativeLinks()

            #section.getImages(self.meta)
            images += section.getImages(self.meta)

            content += section.soup.prettify() #.append(section)

        # Get all the images in the book.
        request.retrieveImages(self.meta, removeDup(images))

        # Make a local copy of the html book.
        self.content = '<html><head><title>%s</title></head><body>' % self.meta['title']
        self.content += content
        self.content += '</body></html>'

        filename = self.meta.filename(ext='.html')

        f = open(filename, 'w')
        f.write(self.content)
        f.close()

    def convert(self, format_):
        """Convert the book from html to another format."""
        print('Converting from html to %s' % format_)

        command = ['ebook-convert',
                self.meta.filename(ext='.html'), 
                self.meta.filename(ext=format_),
                ' --authors \"%(author)s\"' % self.meta,
                ' --level1-toc //h:h1',
                ' --level2-toc //h:h2'
            ]
        output_dir = self.meta.filename(ext='')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        log = open(os.path.join(output_dir, 'ebook-convert.log'), 'w')

        subprocess.call(command, stdout=log)
        log.close()

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
        section = Section('''<body><a id='test1'>test</a> <a id='test2' href='hi.html#test1'>test</a><a href='http://www.some.com/page#anchor'>there</a><a href='http://www.some.com/hi#tag'>there again</a><a href="getting-started.html#starting.calc.precedence"></body>''')
        section.fixRelativeLinks()
        self.assertEqual(section.soup, BeautifulSoup('''<a id='test1'>test</a> <a id='test2' href='#test1'>test</a><a href='http://www.some.com/page#anchor'>there</a><a href='http://www.some.com/hi#tag'>there again</a><a href="#starting.calc.precedence">'''))


class RequestTest(unittest.TestCase):
    def setUp(self):
        self.request = Request("")
    def test_parseLinks(self):
        self.assertEqual(
                self.request.parseRelativeLinks(BeautifulSoup("""
                    <a href='some_index.html'>Google</a>
                    <A href=\"second_index.html\">hi</a>
                    <A href='third.html#here'>hi</a>
                    <A href='third.html#there'>hi</a>
                    <a href='http://www.google.com'>Google</a>""")),
                ['some_index.html', 'second_index.html', 'third.html'])


if __name__ == '__main__':
    unittest.main()
