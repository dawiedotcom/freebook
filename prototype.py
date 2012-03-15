# Author:   Dawie de Klerk
# Contact   dawiedotcom@gmail.com
#
# This is a prototype for convirting free online books in
# HTML format to .mobi format, by giving only the URL of the
# table of content.

import urllib2
import time
import struct
import mobi
from test_page import *
from BeautifulSoup import BeautifulSoup, NavigableString

test_url = 'http://www.lua.org/pil/index.html'

def mac_time():
    return int(time.time()) + secondsTo1970


class HTMLBook(object):

    front = '<html><head><guide><reference type="toc" title="Table of Contents" filepos=0002369035 /></guide></head><body>'
    end = '</body></head>'


    def __init__(self, url):
        
        self.toc_url = url
        self.toc = []
        self.text = ''

    def retrieve(self):

        index_page = self.request(self.toc_url)
        toc = self.parseLinks(index_page)
        pages = []

        url_base = '/'.join(self.toc_url.split('/')[:-1])
        for i, page in enumerate(toc):
            if i == 3:
                break

            full_url = url_base + '/' + page
            print "retrieving page: %s (%i/%i)" %(full_url, i, len(toc)) 
            pages.append(self.request(full_url))

        return pages

    def make(self):

        pages = self.retrieve()
        print 'Striping bodies.'
        
        
        pages = map(self.getBody, pages)
        pages = map(self.stripToHeading, pages)
        pages = map(self.stripFooter, pages)

        text = ''.join(pages)
        
        self.text = self.front + self.makeTOC(text) + text + self.end



    def request(self, url):
        
        f = urllib2.urlopen(url)
        content = f.read()
        f.close()
        
        return content
    
    def getBody(self, html):

        HTML = html.upper()
        body_open = HTML.find('<BODY>')
        body_close = HTML.find('</BODY>')

        return html[body_open + len('<body>'):body_close]

    def makeTOC(self, book, toc_level=1):

        entries = []
        h_tag = 0

        # Find all headers that need to go into the toc
        while (True):
            h_tag = book.find('<h1>', h_tag+1)
            if (h_tag == -1):
                break

            ref = {}
            ref['filepos'] = h_tag
            
            tag_close = book.find('</h1>', h_tag)
            ref['text'] = book[h_tag+4:tag_close]

            entries.append(ref)
        # Calculate the size of the toc
        atag = '<a filepos=%0.10i><u>%s</u></a><br/>\n'

        lengths = [len(atag % (0, entry['text'])) for entry in entries]
        toc_size = sum(lengths)

        # Make the toc
        toc = ''
        for entry in entries:
            toc += atag % (entry['filepos']+toc_size, entry['text'])

        return toc

    def stripToHeading(self, page):

        soup = BeautifulSoup(page)
        headings = ['h1', 'h2', 'h3', 'h4']

        for i in range(5):
            h = soup.findAll('h' + str(i))
            if len(h) != 0:
                break

        h = h[0]
        while h not in soup.contents:
            h = h.parent

        h = h.previousSibling
        while not h is None:
            h_ = h.previousSibling
            h.extract()
            h = h_
            
        return soup.prettify()

    def stripForward(self, soup, tag):
        while not tag is None:
            t = tag.nextSibling
            tag.extract()
            tag = t


    def stripFooter(self, page):
        soup = BeautifulSoup(page)

        hr = soup.findAll('hr')
        
        self.stripForward(soup, hr[0])

        return soup.prettify()


    def parseLinks(self, html):

        HTML = html.upper()
        a_tag = 0
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
        #print(urls)
        return urls
        
    
#class Struct(object):
class Field(object):
    def __init__(self, pos, fmt, value):
        self.pos = pos
        self.fmt = fmt
        self.value = value

class Header(object):
    def __init__(self):
        self.fields = {}
        self.next_pos = 0

    def addField(self, name, fmt, val):
        self.fields[name] = Field(self.next_pos, fmt, val)
        self.next_pos += 1

    def pack(self):
        f_values = self.fields.values()
        f_values.sort(lambda a, b: a.pos - b.pos)

        result = ''
        for fld in f_values:
            result += struct.pack(fld.fmt, fld.value)

        return result

    def __str__(self):
        f_values = zip(self.fields.values(), self.fields.keys())
        f_values.sort(lambda a, b: a[0].pos - b[0].pos)

        fmt = ''
        res = ''
        for fld in f_values:
            res += str(hex(struct.calcsize('>' + fmt))) + '\t' + fld[1][:15] + '\t' + str(fld[0].value) + '\n'
            fmt += fld[0].fmt[1:]

        return res


    def __len__(self):
        fmt_str = ''
        f_values = self.fields.values()

        for fld in f_values:
            fmt_str += fld.fmt[1:]
        
        fmt_str = '>' + fmt_str #.replace('>', '')
        return struct.calcsize(fmt_str)

    def __getitem__(self, key):
        return self.fields[key]
    def __setitem__(self, key, value):
        self.fields[key].value = value


class RecordHeader(Header):
    def __init__(self):
        super(RecordHeader, self).__init__()

        self.records = []

    def addRecord(self, name, record):
        self.records.append(record)

    def pack(self):
        res = super(RecordHeader, self).pack()

        for r in self.records:
            res += r.pack()

        return res

    def __len__(self):
        _len = super(RecordHeader, self).__len__()

        for r in self.records:
            _len += len(r)

        return _len


def align_block(raw, multiple=4, pad='\0'):
    extra = len(raw) % multiple
    if extra == 0: return raw
    return raw + pad*(multiple - extra)


class MobiBook(object):
    
    def _make_headers(self):

        ## HEADER
        header = RecordHeader()
        header.addField("name",                ">32s",  "")
        header.addField("attributes",          ">h",    0)
        header.addField("version",             ">h",    0)
        header.addField("created",             ">I",    0)
        header.addField("modified",            ">I",    0)
        header.addField("backup",              ">I",    0)
        header.addField("modnum",              ">I",    0)
        header.addField("appInfoId",           ">I",    0)
        header.addField("sortInfoID",          ">I",    0)
        header.addField("type",                ">4s",   "BOOK")
        header.addField("creator",             ">4s",   "MOBI")
        header.addField("uniqueIDseed",        ">I",    6)
        header.addField("nextRecordListID",    ">I",    0)
        header.addField("number of records",   ">H",    0)
        
        self.header = header

        ## RECORD0 
        ## PALM DOC HEADER
        palmDOC_header = Header()
        palmDOC_header.addField("Compression",     '>H',   1)
        palmDOC_header.addField("Unused",          '>H',   0)
        palmDOC_header.addField("text length",     '>I',   0)
        palmDOC_header.addField("record count",    '>H',   0)
        palmDOC_header.addField("record size",     '>H',   4096)
        #palmDOC_header.addField("current position", '>I',   0)
        palmDOC_header.addField("Encryption Type", '>H',   0)
        palmDOC_header.addField("Unknown",         '>H',   0)

        self.palmDOC = palmDOC_header

        ## MOBI HEADER
        mobi_header = Header()
        mobi_header.addField("identifier",              '>4s',  'MOBI')
        mobi_header.addField("header length",           '>I',   0)     # Set
        mobi_header.addField("Mobi type",               '>I',   2)
        mobi_header.addField("text Encoding",           '>I',   65001)

        mobi_header.addField("Unique-ID",               '>I',  1337)
        mobi_header.addField("Generator version",       '>I',  6)

        mobi_header.addField("-Reserved",               '>40s',  '\xFF'*40)

        mobi_header.addField("First Non-book index",    '>I',  1)     # Set
        mobi_header.addField("Full Name Offset",        '>I',  0)     # Set
        mobi_header.addField("Full Name Length",        '>I',  0)     # Set

        mobi_header.addField("Language",                '>I',  1033)
        mobi_header.addField("Input Language",          '>I',  0)
        mobi_header.addField("Output Language",         '>I',  0)
        mobi_header.addField("Format version",          '>I',  6)
        mobi_header.addField("First Image index",       '>I',  0)     # Set

        mobi_header.addField("First Huff Record",       '>I',  0)
        mobi_header.addField("Huff Record Count",       '>I',  0)
        mobi_header.addField("First DATP Record",       '>I',  0)
        mobi_header.addField("DATP Record Count",       '>I',  0)

        mobi_header.addField("EXTH flags",              '>I',  0x40) #0b10101000)

        mobi_header.addField("-36 unknown bytes, if Mobi is long enough", '>32s', '')

        mobi_header.addField("DRM Offset",              '>I',  0xFFFFFFFF)
        mobi_header.addField("DRM Count",               '>I',  0xFFFFFFFF)
        mobi_header.addField("DRM Size",                '>I',  0)
        mobi_header.addField("DRM Flags",               '>I',  0)

        mobi_header.addField("-Usually Zeros, unknown 12 bytes", '>12s', '')

        mobi_header.addField("First Content Record",    '>H',  1)
        mobi_header.addField("Last Content Record",     '>H',  0)     # Set
        mobi_header.addField("Unknown1",                '>I',  1)

        mobi_header.addField("FCIS record",             '>I',  0xffffffff)
        mobi_header.addField("Unknown2",                '>I',  1)
        mobi_header.addField("FLIS record",             '>I',  0xffffffff)
        mobi_header.addField("Unknown3",                '>I',  1)

        mobi_header.addField("Unknown4",                 '>8s', '')
        mobi_header.addField("Unknown5",                 '>I',  0xFFFFFFFF)
        mobi_header.addField("Unknown6",                 '>I',  0)
        mobi_header.addField("Unknown7",                 '>I',  0xFFFFFFFF)
        mobi_header.addField("Unknown8",                 '>I',  0xFFFFFFFF)

        mobi_header.addField("Extra record data",       '>I',  0b1)
        mobi_header.addField("Primary index record",    '>I',  0xFFFFFFFF)

        self.mobi = mobi_header

        ## EXTH HEADER
        exth_header = RecordHeader()
        exth_header.addField('identifier',              '>4s', 'EXTH')
        exth_header.addField('header length',           '>I',  0)
        exth_header.addField('record count',            '>I',  0)

        self.exth = exth_header


    def __init__(self, title, text, author, url):
        
        self._make_headers()

        record_size = 0x1000
        text_size = len(text)

        self.title = title
        self.text = text
        self.records = [text[i:i+record_size] for i in range(0, text_size, record_size)] 

        num_text_records = len(self.records)
        self.records.append('\xe9\x8e\r\n')
        num_records = num_text_records + 2
        ## Update record 0 

        #self.record_size = self.palmDOC['record size'].value
        #num_records = len(text)/self.record_size + 2

        # Set up the header info
        self.header['name'] = title[:30]
        self.header['created'] = int(time.time())
        self.header['modified'] = int(time.time())
        self.header['number of records'] = num_records

        # Create an entry in the record info list for each record.
        # Extra records for:
        #   - record0
        for i in range(num_records):
            record_info = Header()
            record_info.addField('offset',      '>I',  0)
            record_info.addField('uniqueID',    '>I',  i)
            self.header.addRecord(str(i), record_info) 


        header_offset = len(self.header)

        # Update the palm DOC header
        self.palmDOC['text length'] = len(text)
        self.palmDOC['record count'] = num_text_records

        # Update the exth header.
        self.addExthRecord(100, author)
        self.addExthRecord(503, title)
        self.addExthRecord(112, url)
        self.addExthRecord(201, 0)
        self.addExthRecord(204, 300)

         # Update the mobi header
        self.mobi['header length'] = len(self.mobi)
        self.mobi['First Non-book index'] = num_text_records + 1
        self.mobi['Full Name Offset'] = len(self.palmDOC) + len(self.mobi) + len(self.exth)
        self.mobi['Full Name Length'] = len(title)
        self.mobi['First Image index'] = 0 #num_records + 1
        self.mobi['Last Content Record'] = num_text_records 

        #print self.mobi
        record0 = self.palmDOC.pack() + self.mobi.pack() + self.exth.pack() + align_block(title + '\0\0')

        self.records.insert(0, record0)
        
        offset = header_offset
        for i in range(len(self.records)):
            self.header.records[i]['offset'] = offset
            offset += len(self.records[i])


    def addExthRecord(self, rType, value):
        record = Header()
        record.addField("type",    '>I',    rType)
        record.addField("length",  '>I',    0)

        if isinstance(value, str):
            record.addField("value",   '>'+str(len(value)) + 's', value)
        elif isinstance(value, int):
            record.addField("value",   '>I', value)

        record['length'].value = len(record)
        self.exth.addRecord(str(rType), record)
        self.exth['header length'].value = len(self.exth)
        self.exth['record count'].value += 1

    def write(self, filename):


        #try:
        content = self.header.pack() 
        
        for r in self.records:
            content += r

        f = open(filename, 'w')
        f.write(content)
        f.close()

if __name__ == '__main__':

    
    book = HTMLBook(test_url)
    book.make()

    f = open('books/pil_test2', 'w')
    text = f.write(book.text)
    f.close()
    

    """
    book1 = MobiBook('this is a test', test_record2, 'ddk', 'www.example.com')
    book1.write('books/test.mobi')
    """
    
    
    '''
    f = open('books/pil_test2')
    text = f.read()
    f.close()

    book2 = MobiBook('Programming in Lua', text, 'Roberto Ierusalimschy', 'http://www.lua.org/pil/index.html')
    book2.write('books/pil.mobi')
    '''
