#! /usr/bin/env python
# Written in 2011 by Qi (Raullen) Chai <https://ece.uwaterloo.ca/~q3chai/>
#

import os
import sys
import getopt
import urllib
import re
import tempfile
import shutil
from pyPdf import PdfFileWriter, PdfFileReader



# Set some kind of User-Agent
class MyURLopener(urllib.FancyURLopener):
    version = "Mozilla 5.0"

def pdfcat(fileList, magPath, magTitle):
    myoutput = PdfFileWriter()
    for f in fileList:
        myinput = PdfFileReader(file(magPath + "/" + f, "rb"))
        # add pages from myinput to output document, unchanged
        for i in range(myinput.getNumPages()):
            myoutput.addPage(myinput.getPage(i))

    #write "output" to document-output.pdf
    outputStream = file(magPath + "/" + magTitle+".pdf", "wb")
    myoutput.write(outputStream)
    outputStream.close()

    #finally, delete the single pdfs
    for f in fileList:
        os.remove(magPath + "/" + f)
        


# validate arguments and start downloading
def main(argv):

    try:
        opts, args = getopt.getopt(argv, "hv:i:n", ["help", "volume=", "issue=", "no-merge"])
    except getopt.GetoptError:
        error("Could not parse command line arguments.")

    volume = ""
    issue = ""
    merge = True
    
    try:
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit()
            elif opt in ("-v", "--volume"):
                volume = int(arg)
            elif opt in ("-i", "--issue"):
                issue = int(arg)
            elif opt in ("-n", "--no-merge"):
                merge = False
    except ValueError:
        error("-v and -i accept integers only")

    if volume=="" or issue=="":
        usage()
        sys.exit()
    
    
    link = "http://www.sciencemag.org/content/"+str(volume)+"/"+str(issue)
    chapters = list()
    loader = MyURLopener();
    curDir = os.getcwd()
    magTitle = ""

    # download page source
    try:
        print "fetching magazine information...\n\t%s" % link
        page = loader.open(link).read()
    except IOError, e:
        error("Bad link given (%s)" % e)

    if re.search(r'403 Forbidden', page):
        error("Could not access page: 403 Forbidden error.")

    # get title
    for match in re.finditer(r"<title> Table of Contents: .* </title>", page):
        magTitle = match.group(0)
        magTitle = magTitle.replace('<title> Table of Contents: ', '')
        magTitle = magTitle.replace(' </title>', '')
        magTitle = magTitle.replace(' ', '_')
        magTitle = magTitle.replace(';', '')
        magTitle = magTitle.replace('(', '')
        magTitle = magTitle.replace(')', '')
        
        magTitle = magTitle.replace('January', 'Jan')
        magTitle = magTitle.replace('February', 'Feb')
        magTitle = magTitle.replace('March', 'Mar')
        magTitle = magTitle.replace('April', 'Apr')
        magTitle = magTitle.replace('May', 'May')
        magTitle = magTitle.replace('June', 'Jun')
        magTitle = magTitle.replace('July', 'Jul')
        magTitle = magTitle.replace('August', 'Aug')
        magTitle = magTitle.replace('September', 'Sep')
        magTitle = magTitle.replace('October', 'Oct')
        magTitle = magTitle.replace('November', 'Nov')
        magTitle = magTitle.replace('December', 'Dec')
        

    # get chapters
    for match in re.finditer(r"/.*\.full\.pdf", page):
        chapterLink = "http://www.sciencemag.org" + match.group(0)
        chapters.append(chapterLink)

    print "found %d articles" % len(chapters)

    # setup; set tempDir as working directory
    tempDir = tempfile.mkdtemp()
    os.chdir(tempDir)

    i = 1
    fileList = list()

    for chapterLink in chapters:
        print "downloading article %d/%d" % (i, len(chapters))
        
        localFile, mimeType = geturl(chapterLink, "%d.pdf" % i)
        if mimeType.gettype() != "application/pdf":
            os.chdir(curDir)
            shutil.rmtree(tempDir)
            error("downloaded chapter %s has invalid mime type %s - are you allowed to download %s?" % (chapterLink, mimeType.gettype(), magTitle))
        fileList.append(localFile)
        i += 1

        
    for f in fileList:
        shutil.move(f, curDir)
    os.chdir(curDir)
    
    if merge:
        print "merging articles"
        if len(fileList) == 1:
            os.rename(fileList[0], magTitle)
        else:
            pdfcat(fileList, curDir, magTitle)

    # cleanup
    shutil.rmtree(tempDir)

    print "%s was successfully downloaded, it was saved to %s" % (magTitle, curDir)
    sys.exit()

# give a usage message
def usage():
    print """Usage:
%s [OPTIONS]

Options:
  -h, --help              Display this usage message
  -v, --volume            defines the volume of the science magazine you intend to download
  -i, --issue             defines the issue of the science magazine you intend to download
  -n, --no-merge          Only download the articles but don't merge them into a single PDF.

For example:
  To download all the articles in "http://www.sciencemag.org/content/334/6062" and merge them into a single pdf file, one may execute:
      python sciencemag.py -v 334 -i 6062
""" % os.path.basename(sys.argv[0])

# raise an error and quit
def error(msg=""):
    if msg != "":
        print "\nERROR: %s\n" % msg
    sys.exit(2)

    return None


# based on http://mail.python.org/pipermail/python-list/2005-April/319818.html
def progressbar(numblocks, blocksize, filesize, url=None):
    try:
        percent = min((numblocks*blocksize*100)/filesize, 100)
    except:
        percent = 100
    if numblocks != 0:
        sys.stdout.write("\b"*70)
    sys.stdout.write("%-66s%3d%%" % (url, percent))

def geturl(url, dst):
    downloader = MyURLopener()
    if sys.stdout.isatty():
        response = downloader.retrieve(url, dst,
                           lambda nb, bs, fs, url=url: progressbar(nb,bs,fs,url))
        sys.stdout.write("\n")
    else:
        response = downloader.retrieve(url, dst)

    return response

# start program
if __name__ == "__main__":
    main(sys.argv[1:])