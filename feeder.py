# Feed Class gets a bunch of words from google news xml feed
from xml.dom import minidom
from StringIO import StringIO
import urllib2, re, gzip, time, os
from string import lower, lowercase
import feedparser

# TODO more feeds/better scraping of feeds

def FudgeSentence(sentence):
    sentence = sentence.replace("&quot;","")
    sentence = sentence.replace("&amp;","and")
    sentence = sentence.replace("nbsp;", " ")
    sentence = sentence.replace("mdash;", "")
    return sentence.strip() + "."

br_regex = re.compile(r'&lt;[bB][rR]&gt;|&lt;[bB][rR] /&gt;')
def StripTags(text):
    text = re.sub(br_regex, ' ', text)

    finished = 0
    parsed = []
    while not finished:
        finished = 1
        # check if there is an open tag left
        start = text.find("&lt;")
        if start >= 0:
            # if there is, check if the tag gets closed
            stop = text.find("&gt;")
            if stop >= 0:
                # if it does, strip it, and continue loop
                finished = 0
                parsed.append(text[:start])
                text = text[stop+4:]
    parsed.append(text)
    return ''.join(parsed)
    
acronym_destroyer = re.compile('[A-Z]{2}')
def GoodWord(word):
    if len(word) < 4: return False
    for char in lower(word):
        if char not in lowercase:
            return False
    acronym = acronym_destroyer.search(word)
    if acronym: return False
    return True
    
def GetFeeder(string="Google"):
    if string == "Digg":
        return DiggFeeder()
    elif string == "Slashdot":
        return SlashdotFeeder()
    else:
        return GoogleFeeder()
    
class Feeder:
    def __init__(self):            
        old = False
        try: # Try to get the last modified date of the retrieved XML file, if it exists
            lastmod = os.stat(self.filename)[8]
            old = (time.time() - lastmod) > 3600 # one hour
        except OSError:
            old = True

        if old:
            xml = self.getxml(self.feedurl)
            out = open(self.filename,"w")
            out.write(xml.read())
            out.close()
        xml = open(self.filename)
        try:
            parsed_feed = feedparser.parse(xml)
            textblob = self.filter(parsed_feed)
            self.finish(textblob)
        except:
            self.words = []
            print self.type + " produced parse error."
        
    def getxml(self,url):
        request = urllib2.Request(url)
        request.add_header('User-Agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.6) Gecko/20060728 Firefox/1.5.0.6')
        request.add_header('Accept-encoding', 'gzip')
        f = urllib2.urlopen(request)
        if 'Content-Encoding' in f.info():
            if f.info()['Content-Encoding'] == 'gzip':
                # Need to do a little dance to get a file-like object out of a gzipped file. A very weird dance.
                page = gzip.GzipFile(fileobj=StringIO(f.read()))
                return StringIO(page.read())
        return f 
        
    def finish(self,textblob):
        words = textblob.split(' ')
        self.sentences = [FudgeSentence(sentence) for sentence in textblob.split('. ')]
        self.words = [word.lower() for word in words if GoodWord(word)]
        print self.type + " returned " + str(len(self.words)) + " words."
        
    def getWords(self):
        return self.words
        
    def getSentences(self):
        return self.sentences
        
class GoogleFeeder(Feeder):
    def __init__(self):
        self.type = "Google"
        self.feedurl = "http://news.google.com/?output=rss"
        self.filename = 'google.xml'
        Feeder.__init__(self)

    def filter(self,parsed_feed):
        # Google description texts end with '<b>...</b>', escaped.
        texts = [entry['description'] for entry in parsed_feed['entries']]
        choppedtext = []
        for text in texts:
            choppedtext.append(text[:text.find("&lt;b&gt;...")])
        cleantexts = [StripTags(text) for text in choppedtext]
        return ' '.join(cleantexts)

class SlashdotFeeder(Feeder):
    def __init__(self):
        self.type = "Slashdot"
        self.feedurl = "http://rss.slashdot.org/Slashdot/slashdot"
        self.filename = 'slashdot.xml'
        Feeder.__init__(self)

    def filter(self,parsed_feed):
        # Most articles in slashdot are enclosed within blocks a-la: User Writes, "blah blah blah"
        texts = [entry['description'] for entry in parsed_feed['entries']]
        cleantexts = [StripTags(text) for text in texts]
            
        writes = re.compile(r"writes &quot")
        inquotes = re.compile(r"&quot;(.*?)&quot;")
        justtexts = []
        for text in cleantexts:
            match = writes.search(text)
            if match:
                justtexts.append(inquotes.search(text).groups()[0])
            else:
                justtexts.append(text)
        return ' '.join(justtexts)
    
class DiggFeeder(Feeder):
    def __init__(self):
        self.type = "Digg"
        self.feedurl = "http://digg.com/rss/index.xml"
        self.filename = 'digg.xml'
        Feeder.__init__(self)

    def filter(self,parsed_feed):
        return ' '.join([entry['description'] for entry in parsed_feed['entries']])