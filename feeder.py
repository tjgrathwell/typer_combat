# Feed Class gets a bunch of words from google news xml feed

from StringIO import StringIO
import feedparser
import urllib2, re, gzip, time, os, string

def getFeeder(string = "Google"):
    if string == "Digg":
        return DiggFeeder()
    elif string == "Slashdot":
        return SlashdotFeeder()
    else:
        return GoogleFeeder()
    
class Feeder:
    def __init__(self):            
        stale = False
        try: # Try to get the last modified date of the retrieved XML file, if it exists
            lastmod = os.stat(self.filename)[8]
            stale = (time.time() - lastmod) > 3600 # one hour
        except OSError:
            stale = True

        if stale:
            self.download_and_cache_xml()

        xml = open(self.filename)
        parsed_feed = feedparser.parse(xml)
        textblob = self.filtered(parsed_feed)
        self.save_words(textblob)

    def download_and_cache_xml(self):
        try:
            xml = self.download_xml(self.feed_url)
        except urllib2.URLError:
            pass
        else:
            out = open(self.filename, "w")
            out.write(xml.read())
            out.close()

    def fudge_sentence(self, sentence):
        sentence = sentence.replace("&quot;", "")
        sentence = sentence.replace("&amp;", "and")
        sentence = sentence.replace("nbsp;", " ")
        sentence = sentence.replace("mdash;", "")
        return sentence.strip() + "."

    br_regex = re.compile(r'&lt;[bB][rR]&gt;|&lt;[bB][rR] /&gt;')
    def strip_tags(self, text):
        text = re.sub(self.br_regex, ' ', text)

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
                    text = text[stop + 4:]
        parsed.append(text)
        return ''.join(parsed)

    acronym_regex = re.compile('[A-Z]{2}')
    def word_is_good(self, word):
        if len(word) < 4: return False
        for char in word.lower():
            if char not in string.lowercase:
                return False
            acronym = self.acronym_regex.search(word)
            if acronym:
                return False
        return True

    ua_string = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.6) Gecko/20060728 Firefox/1.5.0.6'
    def download_xml(self, url):
        request = urllib2.Request(url)
        request.add_header('User-Agent', self.ua_string)
        request.add_header('Accept-encoding', 'gzip')
        f = urllib2.urlopen(request)
        if 'Content-Encoding' in f.info():
            if f.info()['Content-Encoding'] == 'gzip':
                # Need to do a little dance to get a file-like object out of a gzipped file.
                page = gzip.GzipFile(fileobj = StringIO(f.read()))
                return StringIO(page.read())
        return f 
        
    def save_words(self, textblob):
        words = textblob.split(' ')
        self.sentences = [self.fudge_sentence(sentence) for sentence in textblob.split('. ')]
        self.words = [word.lower() for word in words if self.word_is_good(word)]
        print self.type + " returned " + str(len(self.words)) + " words."
        
class GoogleFeeder(Feeder):
    def __init__(self):
        self.type = "Google"
        self.feed_url = "http://news.google.com/?output=rss"
        self.filename = os.path.join('feeds', 'google.xml')
        Feeder.__init__(self)

    def filtered(self, parsed_feed):
        # Google description texts end with '<b>...</b>', escaped.
        texts = [entry['description'] for entry in parsed_feed['entries']]
        choppedtext = []
        for text in texts:
            choppedtext.append(text[:text.find("&lt;b&gt;...")])
        cleantexts = [self.strip_tags(text) for text in choppedtext]
        return ' '.join(cleantexts)

class SlashdotFeeder(Feeder):
    def __init__(self):
        self.type = "Slashdot"
        self.feed_url = "http://rss.slashdot.org/Slashdot/slashdot"
        self.filename = os.path.join('feeds', 'slashdot.xml')
        Feeder.__init__(self)

    def filtered(self, parsed_feed):
        # Most articles in slashdot are enclosed within blocks of the style: User Writes, "blah blah blah"
        texts = [entry['description'] for entry in parsed_feed['entries']]
        cleantexts = [self.strip_tags(text) for text in texts]
            
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
        self.feed_url = "http://digg.com/rss/index.xml"
        self.filename = os.path.join('feeds', 'digg.xml')
        Feeder.__init__(self)

    def filtered(self, parsed_feed):
        return ' '.join([entry['description'] for entry in parsed_feed['entries']])
