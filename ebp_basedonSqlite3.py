#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.dom import minidom
import codecs
import sqlite3


def downloadXML():
    import urllib

    XML_URL = 'http://ebookpoint.pl/plugins/new/xml/lista.cgi'
    dlFile = 'ebookpoint_ebooks.xml'

    opener = urllib.FancyURLopener()
    try:
        f = opener.open(XML_URL)
    except IOError:
        print 'Failed to open "%s"' % XML_URL
    else:
        print 'Downloading XML from %s' % XML_URL
        outputFile = open(dlFile, "wb")
        while True:
            data = f.read(8192)
            if not data:
                print 'Done'
                break
            print('.'),
            outputFile.write(data)
        f.close()
        outputFile.close()


def convertfile():
    print 'Convert to UTF-8'
    blocksize = 1048576
    sourcefilename = 'ebookpoint_ebooks.xml'
    targetfilename = 'nowy.xml'

    with codecs.open(sourcefilename, "r", 'iso-8859-2') as sourceFile:
        with codecs.open(targetfilename, "w", 'utf-8') as targetFile:
            while True:
                contents = sourceFile.read(blocksize)
                if not contents:
                    break
                targetFile.write(contents)
    targetFile.close()


def preprocessing():
    print 'XML Preprocessing'
    input_file = codecs.open('nowy.xml', "r", 'utf-8')
    output_file = codecs.open('tmp_ebookpoint_ebooks.xml', "w", 'utf-8')
    reDict = {';': '', '&': '', '"WAJLORD" ': '', 'iso-8859-2': 'utf-8'}
    fo = input_file.read()
    for k, v in reDict.items():
        fo = fo.replace(k, v)
    output_file.write(fo)
    output_file.close()


def makeCSV():
    print 'Minidom Processing'
    burl = 'http://ebookpoint.pl/add/8387.'
    header = """
    <!doctype html>
    <head>
        <meta charset="utf-8">
        <title>EBOOKI PROMOCJE</title>
        <meta name="viewport" content="width=device-width, height=device-height, initial-scale=1.0, user-scalable=yes">
        <style>
                table {
                        border-collapse: collapse;
                }

                th, td {
                        padding: 8px;
                        text-align: left;
                        border-bottom: 1px solid #ddd;
                        text-align: center;
                }

                th {
                        background-color: #4CAF50;
                        color: white;
                        text-align: center;
                }

                tr:hover{background-color:#f5f5f5}
                tr:nth-child(even){background-color: #f2f2f2}
        </style>
</head>
<body>
        <table>
                <tr>
                        <th>Autor</th>
                        <th>Tytuł</th>
                        <th>Cena promocyjna</th>
                        <th>Cena normalna</th>
                        <th>Zniżka</th>
                        <th>Oszczędzasz</th>
                </tr>
    """

    footer = """
    </table>
</body>
</html>
"""
    zl = ' zł'.decode('utf-8')
    xmldoc = minidom.parse('tmp_ebookpoint_ebooks.xml')
    dNodes = xmldoc.firstChild

    parent = dNodes.getElementsByTagName("item")
    csvFile = codecs.open('promocja.html', "w", 'utf-8')
    csvFile.write(header.decode('utf-8'))

    # Sqlite3
    connection = sqlite3.connect(':memory:')
    connection.text_factory = str
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE ebookpoint'
                   '(author TEXT, title TEXT, identifier TEXT, bargain REAL, price REAL, discount REAL, yousave REAL)')
    sql = "INSERT INTO ebookpoint VALUES(?, ?, ?, ?, ?, ?, ?)"

    for element in parent:
        typ = element.getAttribute('typ')
        status = element.getAttribute('status')
        if typ == '2' and status == '1':  # typ: ebook i status: dostepny
            discount = element.getAttribute('znizka')
            if discount != '0':  # ebooki tylko ze znizka
                author = element.getAttribute('autor')
                title = element.getAttribute('tytul')
                bargain = element.getAttribute('cena')
                price = element.getAttribute('cenadetaliczna')
                identifier = element.getAttribute('ident')
                yousave = str(round(float(price), 2) - round(float(bargain), 2))
                if author == '':
                    author = 'Praca zbiorowa'
                cursor.execute(sql, (author, title, identifier, bargain, price, discount, yousave))
    print 'Reading'
    sql = 'SELECT author, title, identifier, bargain, price, discount, yousave FROM ebookpoint ORDER BY yousave DESC'
    cursor.execute(sql)
    for author, title, identifier, bargain, price, discount, yousave in cursor.fetchall():
        csvFile.write('<tr><td>%s</td><td><a href="%s/%s" target="_blank">%s</a></td><td>%s%s</td><td>%s%s</td><td>%s%%</td><td>%s%s</td></tr>'
                      % (author.decode('utf-8'), burl, identifier, title.decode('utf-8'), bargain, zl, price, zl, discount, yousave, zl))
    csvFile.write(footer)
    csvFile.close()
    print 'Done'

if __name__ == "__main__":
    downloadXML()
    convertfile()
    preprocessing()
    makeCSV()
