# freebook

Freebook is a simple script to convert freely available ebooks from html 
to mobi.

_Disclaimer_ This is a personal project and there is still a lot to be done
before this will be in a proper working order.


## Usage

### Existing books

If the book already has a `.yaml` file in the `books` directory, simply run 
`./freebook.py` and the books title or the url of the index page as the first
argument. For example

```bash
./freebook 'programming in lua' 
./freebook http://mitpress.mit.edu/sicp/full-text/book/book-Z-H-4.html
```

### Adding a new book

_Step 1_ Add a `.yaml` file for your book with at least the following fields

```yaml
url: <url to the table of content page>
author: <author>
title: <title>
```

To remove headers and footers that are not part of the book's content, you can 
specify the following 

```yaml
header-attrs:
    <attribute1> : <value1>
    <attribute2> : <value2>

footer-tag: <tag>
footer-attrs: 
    <attribute1> : <value1>
    <attribute2> : <value2>
```
	
_Step 2_ You also need to add an entry in 'books/catalog.yaml' to map command line arguments
to the `.yaml` file for the new book.

_Step 3_ Send me a pull request. Someone else might want to read the book on their Kindle 
too.

