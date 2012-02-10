# Feed Class gets a bunch of words from google news xml feed

from StringIO import StringIO
import feedparser
import urllib2, re, gzip, time, os, string

ONE_HOUR = 60 * 60
cached_feeders = {}

def getFeeder(string = "Google"):
    if string in cached_feeders:
        return cached_feeders[string]

    new_feeder = None
    if string == "Digg":
        new_feeder = DiggFeeder()
    elif string == "Slashdot":
        new_feeder = SlashdotFeeder()
    else:
        new_feeder = GoogleFeeder()

    cached_feeders[string] = new_feeder
    return new_feeder

class Feeder:
    def __init__(self):
        if self.needs_redownload():
            self.download_and_cache_xml()

        parsed_feed = feedparser.parse(self.filename)

        filtered_text = self.filter(parsed_feed)
        self.words = self.good_words(filtered_text)

    def needs_redownload(self):
        try:
            lastmod = os.stat(self.filename)[8]
            return (time.time() - lastmod) > ONE_HOUR
        except OSError:
            return True

    def download_and_cache_xml(self):
        try:
            xml = self.download_xml()
        except urllib2.URLError:
            pass
        else:
            out = open(self.filename, "w")
            out.write(xml.read())
            out.close()

    encoded_tags_regex = re.compile(r'&lt;[^&]*&gt;')
    decoded_tags_regex = re.compile(r'<[^>]*>')
    space_regex = re.compile(r'\s+')
    def strip_tags(self, text):
        text = re.sub(self.encoded_tags_regex, ' ', text)
        text = re.sub(self.decoded_tags_regex, ' ', text)
        text = re.sub(self.space_regex, ' ', text)
        return text

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

    ua_string = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.6) ' + \
                'Gecko/20060728 Firefox/1.5.0.6'
    def download_xml(self):
        request = urllib2.Request(self.feed_url)
        request.add_header('User-Agent', self.ua_string)
        request.add_header('Accept-encoding', 'gzip')
        f = urllib2.urlopen(request)
        if 'Content-Encoding' in f.info():
            if f.info()['Content-Encoding'] == 'gzip':
                # Need to do a little dance to get a file-like object out of a gzipped file.
                page = gzip.GzipFile(fileobj = StringIO(f.read()))
                return StringIO(page.read())
        return f

    def filter(self, parsed_feed):
        articles = [entry['description'] for entry in parsed_feed['entries']]
        return ' '.join([self.filter_article(article) for article in articles])

    def filter_article(self, article):
        return self.strip_tags(article)

    def good_words(self, text):
        raw_words = list(set(text.split(' ')))
        return [word.lower() for word in raw_words if self.word_is_good(word)]

class GoogleFeeder(Feeder):
    short_name = "Google"
    feed_url = "http://news.google.com/?output=rss"
    filename = os.path.join('feeds', 'google.xml')

class SlashdotFeeder(Feeder):
    short_name = "Slashdot"
    feed_url = "http://rss.slashdot.org/Slashdot/slashdot"
    filename = os.path.join('feeds', 'slashdot.xml')

    def filter_article(self, article):
        text = self.strip_tags(article)

        # Most articles in the slashdot feed are enclosed within blocks of the style:
        #    user writes, "blah blah blah"
        writes_re = re.compile(r'writes "(.*)"')

        match = writes_re.search(text)
        if match:
            return match.groups()[0]
        else:
            return text

class DiggFeeder(Feeder):
    short_name = "Digg"
    feed_url = "http://digg.com/rss/index.xml"
    filename = os.path.join('feeds', 'digg.xml')
