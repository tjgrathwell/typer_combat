#!/usr/bin/env python

import unittest
import feeder
import feedparser

class testFeeder (unittest.TestCase):
    def setUp(self):
        self.feeder = feeder.getFeeder('Google')
        self.slashdot_feeder = feeder.getFeeder('Slashdot')
        self.google_sample_xml = """
<rss version="2.0">
  <channel>
    <generator>NFE/1.0</generator>
    <title>Top Stories - Google News</title>
    <link>http://news.google.com/news?pz=1&amp;ned=us&amp;hl=en</link>
    <language>en</language>
    <webMaster>news-feedback@google.com</webMaster>
    <copyright>&amp;copy;2012 Google</copyright>
    <pubDate>Fri, 10 Feb 2012 01:18:25 GMT</pubDate>
    <lastBuildDate>Fri, 10 Feb 2012 01:18:25 GMT</lastBuildDate>
    <image>
      <title>Top Stories - Google News</title>
      <url>http://www.gstatic.com/news/img/logo/en_us/news.gif</url>
      <link>http://news.google.com/news?pz=1&amp;ned=us&amp;hl=en</link>
    </image>
    <item>
      <title>US banks agree to $25 billion in homeowner help - Reuters</title>
      <link>http://news.google.com/news/url?sa=t&amp;fd=R&amp;usg=AFQjCNFRjyUoMCCVt0-th1raD3hrYHjKcA&amp;url=http://www.reuters.com/article/2012/02/10/us-mortgage-settlement-idUSTRE81600F20120210</link>
      <guid isPermaLink="false">tag:news.google.com,2005:cluster=17593998987426</guid>
      <category>Top Stories</category>
      <pubDate>Fri, 10 Feb 2012 00:22:24 GMT</pubDate>
      <description>&lt;table border=&quot;0&quot; cellpadding=&quot;2&quot; cellspacing=&quot;7&quot; style=&quot;vertical-align:top;&quot;&gt;&lt;tr&gt;&lt;td width=&quot;80&quot; align=&quot;center&quot; valign=&quot;top&quot;&gt;&lt;font style=&quot;font-size:85%;font-family:arial,sans-serif&quot;&gt;&lt;a href=&quot;http://news.google.com/news/url?sa=t&amp;amp;fd=R&amp;amp;usg=AFQjCNGKuqJKyIDNsFX_esKCV5dwTt1nag&amp;amp;url=http://www.theglobeandmail.com/report-on-business/economy/housing/us-banks-agree-to-25-billion-deal-for-homeowners/article2332241/&quot;&gt;&lt;img src=&quot;//nt1.ggpht.com/news/tbn/bd7cvNOmxKKm5M/6.jpg&quot; alt=&quot;&quot; border=&quot;1&quot; width=&quot;80&quot; height=&quot;80&quot; /&gt;&lt;br /&gt;&lt;font size=&quot;-2&quot;&gt;Globe and Mail&lt;/font&gt;&lt;/a&gt;&lt;/font&gt;&lt;/td&gt;&lt;td valign=&quot;top&quot; class=&quot;j&quot;&gt;&lt;font style=&quot;font-size:85%;font-family:arial,sans-serif&quot;&gt;&lt;br /&gt;&lt;div style=&quot;padding-top:0.8em;&quot;&gt;&lt;img alt=&quot;&quot; height=&quot;1&quot; width=&quot;1&quot; /&gt;&lt;/div&gt;&lt;div class=&quot;lh&quot;&gt;&lt;a href=&quot;http://news.google.com/news/url?sa=t&amp;amp;fd=R&amp;amp;usg=AFQjCNFRjyUoMCCVt0-th1raD3hrYHjKcA&amp;amp;url=http://www.reuters.com/article/2012/02/10/us-mortgage-settlement-idUSTRE81600F20120210&quot;&gt;&lt;b&gt;US banks agree to $25 billion in homeowner help&lt;/b&gt;&lt;/a&gt;&lt;br /&gt;&lt;font size=&quot;-1&quot;&gt;&lt;b&gt;&lt;font color=&quot;#6f6f6f&quot;&gt;Reuters&lt;/font&gt;&lt;/b&gt;&lt;/font&gt;&lt;br /&gt;&lt;font size=&quot;-1&quot;&gt;By Aruna Viswanatha | WASHINGTON (Reuters) - Five big US banks accused of abusive mortgage practices have agreed to a $25 billion government settlement that may help roughly one million borrowers but is no magic bullet for the ailing housing market.&lt;/font&gt;&lt;br /&gt;&lt;font size=&quot;-1&quot;&gt;&lt;a href=&quot;http://news.google.com/news/url?sa=t&amp;amp;fd=R&amp;amp;usg=AFQjCNE601FdP6ugxm-eq58jqiCnCnDOUg&amp;amp;url=http://www.usatoday.com/money/economy/housing/story/2012-02-09/mortgage-settlement-what-it-means-to-you/53031990/1&quot;&gt;Questions and answers on the mortgage settlement&lt;/a&gt;&lt;font size=&quot;-1&quot; color=&quot;#6f6f6f&quot;&gt;&lt;nobr&gt;USA TODAY&lt;/nobr&gt;&lt;/font&gt;&lt;/font&gt;&lt;br /&gt;&lt;font size=&quot;-1&quot;&gt;&lt;a href=&quot;http://news.google.com/news/url?sa=t&amp;amp;fd=R&amp;amp;usg=AFQjCNFRFomnkff5CzmUg-UczG-jy68Wlg&amp;amp;url=http://www.bloomberg.com/news/2012-02-10/mortgage-foreclosure-settlement-falls-short-still-worth-the-wait-view.html&quot;&gt;Mortgage Foreclosure Settlement Falls Short, Still Worth the Wait: View&lt;/a&gt;&lt;font size=&quot;-1&quot; color=&quot;#6f6f6f&quot;&gt;&lt;nobr&gt;Bloomberg&lt;/nobr&gt;&lt;/font&gt;&lt;/font&gt;&lt;br /&gt;&lt;font size=&quot;-1&quot;&gt;&lt;a href=&quot;http://news.google.com/news/url?sa=t&amp;amp;fd=R&amp;amp;usg=AFQjCNExJzZN8LdX1RtDfWPtOD40GtaSwQ&amp;amp;url=http://abcnews.go.com/Business/wireStory/source-ny-california-sign-mortgage-settlement-15545480&quot;&gt;$25B Settlement Reached Over Foreclosure Abuses&lt;/a&gt;&lt;font size=&quot;-1&quot; color=&quot;#6f6f6f&quot;&gt;&lt;nobr&gt;ABC News&lt;/nobr&gt;&lt;/font&gt;&lt;/font&gt;&lt;br /&gt;&lt;font size=&quot;-1&quot; class=&quot;p&quot;&gt;&lt;a href=&quot;http://news.google.com/news/url?sa=t&amp;amp;fd=R&amp;amp;usg=AFQjCNHtVZjr7M9oZvkrJ0AlK6gDjxHCiQ&amp;amp;url=http://www.philly.com/philly/business/139054714.html&quot;&gt;&lt;nobr&gt;Philadelphia Inquirer&lt;/nobr&gt;&lt;/a&gt;&amp;nbsp;-&lt;a href=&quot;http://news.google.com/news/url?sa=t&amp;amp;fd=R&amp;amp;usg=AFQjCNFHTIP7ckJ7ehC3Bhf9j8hLDKidaQ&amp;amp;url=http://www.businessweek.com/news/2012-02-09/u-s-banks-face-more-costs-after-25-billion-mortgage-deal.html&quot;&gt;&lt;nobr&gt;BusinessWeek&lt;/nobr&gt;&lt;/a&gt;&amp;nbsp;-&lt;a href=&quot;http://news.google.com/news/url?sa=t&amp;amp;fd=R&amp;amp;usg=AFQjCNGlmBGjUkaC_gSE7wyCsY9PDbxKkw&amp;amp;url=http://www.sfgate.com/cgi-bin/article.cgi?f%3D/c/a/2012/02/09/BUDS1N4O2A.DTL&quot;&gt;&lt;nobr&gt;San Francisco Chronicle&lt;/nobr&gt;&lt;/a&gt;&lt;/font&gt;&lt;br /&gt;&lt;font class=&quot;p&quot; size=&quot;-1&quot;&gt;&lt;a class=&quot;p&quot; href=&quot;http://news.google.com/news/more?pz=1&amp;amp;ned=us&amp;amp;ncl=do8QBwJxdTxNxyM1UAHagn0eOCjvM&amp;amp;topic=h&quot;&gt;&lt;nobr&gt;&lt;b&gt;all 2,781 news articles&amp;nbsp;&amp;raquo;&lt;/b&gt;&lt;/nobr&gt;&lt;/a&gt;&lt;/font&gt;&lt;/div&gt;&lt;/font&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;</description>
    </item>
    <description>Google News</description>
  </channel>
</rss>
"""

        self.slashdot_sample_xml = """
<?xml version="1.0" encoding="ISO-8859-1"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/" xmlns:slash="http://purl.org/rss/1.0/modules/slash/" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:taxo="http://purl.org/rss/1.0/modules/taxonomy/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:syn="http://purl.org/rss/1.0/modules/syndication/" xmlns:admin="http://webns.net/mvcb/" xmlns:feedburner="http://rssnamespace.org/feedburner/ext/1.0">

<channel rdf:about="http://slashdot.org/">
<title>Slashdot</title>
<link>http://slashdot.org/</link>
<description>News for nerds, stuff that matters</description>
<dc:language>en-us</dc:language>
<dc:rights>Copyright 1997-2012, Geeknet, Inc.  All Rights Reserved.</dc:rights>
<dc:date>2012-02-10T02:28:10+00:00</dc:date>
<dc:publisher>Geeknet, Inc.</dc:publisher>

<dc:creator>help@slashdot.org</dc:creator>
<dc:subject>Technology</dc:subject>
<syn:updateBase>1970-01-01T00:00+00:00</syn:updateBase>
<syn:updateFrequency>1</syn:updateFrequency>
<syn:updatePeriod>hourly</syn:updatePeriod>
<items>
 <rdf:Seq>
  <rdf:li rdf:resource="http://yro.slashdot.org/story/12/02/09/238211/intel-settles-ny-antitrust-case?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://it.slashdot.org/story/12/02/09/2320247/the-gradual-death-of-the-brick-and-mortar-tech-store?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />

  <rdf:li rdf:resource="http://apple.slashdot.org/story/12/02/09/2256241/hackers-hit-apple-supplier-foxconn?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://hardware.slashdot.org/story/12/02/09/2213228/engelbarts-keyboard-available-for-touchscreens?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://science.slashdot.org/story/12/02/09/2152204/the-himalayas-and-nearby-peaks-have-lost-no-ice-in-past-10-years-study-shows?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://yro.slashdot.org/story/12/02/09/2136232/hacked-emails-reveal-russian-astroturfing-program?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://idle.slashdot.org/story/12/02/09/1937257/how-much-stuff-can-timothy-jam-into-his-new-hoodies-pockets-video?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://science.slashdot.org/story/12/02/09/2032204/mild-electric-shock-to-brain-may-boost-spatial-memory?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://entertainment.slashdot.org/story/12/02/09/195225/pink-floyd-engineer-alan-parsons-rips-audiophiles-youtube-and-jonas-brothers?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://search.slashdot.org/story/12/02/09/1857220/online-privacy-worth-less-than-marshmallow-fluff-six-pack?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://politics.slashdot.org/story/12/02/09/182245/us-approves-two-new-nuclear-reactors?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />

  <rdf:li rdf:resource="http://games.slashdot.org/story/12/02/09/1845249/double-fine-raises-700000-in-24-hours-with-crowdfunding?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://apple.slashdot.org/story/12/02/09/1659208/fbi-file-notes-steve-jobs-reality-distortion-field?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://ask.slashdot.org/story/12/02/09/1633256/ask-slashdot-where-are-the-open-source-jobs?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
  <rdf:li rdf:resource="http://hardware.slashdot.org/story/12/02/09/1629259/sponsor-a-valve-on-colossus?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed" />
 </rdf:Seq>
</items>
<image rdf:resource="http://a.fsdn.com/sd/topics/topicslashdot.gif" />
<textinput rdf:resource="http://slashdot.org/search.pl" />
<atom10:link xmlns:atom10="http://www.w3.org/2005/Atom" rel="self" type="application/rdf+xml" href="http://rss.slashdot.org/Slashdot/slashdot" /><feedburner:info uri="slashdot/slashdot" /><atom10:link xmlns:atom10="http://www.w3.org/2005/Atom" rel="hub" href="http://pubsubhubbub.appspot.com/" /></channel>
<image rdf:about="http://a.fsdn.com/sd/topics/topicslashdot.gif">
<title>Slashdot</title>

<url>http://a.fsdn.com/sd/topics/topicslashdot.gif</url>
<link>http://slashdot.org/</link>
</image>
<item rdf:about="http://yro.slashdot.org/story/12/02/09/238211/intel-settles-ny-antitrust-case?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed">
<title>Intel Settles NY Antitrust Case</title>
<link>http://rss.slashdot.org/~r/Slashdot/slashdot/~3/GL8WkhWMmoE/intel-settles-ny-antitrust-case</link>
<description>&lt;p&gt;&lt;a href="http://feedads.g.doubleclick.net/~at/TRgt55_QZ-ybcCxvLEhXIi38Gd4/0/da"&gt;&lt;img src="http://feedads.g.doubleclick.net/~at/TRgt55_QZ-ybcCxvLEhXIi38Gd4/0/di" border="0" ismap="true"&gt;&lt;/img&gt;&lt;/a&gt;&lt;br/&gt;

&lt;a href="http://feedads.g.doubleclick.net/~at/TRgt55_QZ-ybcCxvLEhXIi38Gd4/1/da"&gt;&lt;img src="http://feedads.g.doubleclick.net/~at/TRgt55_QZ-ybcCxvLEhXIi38Gd4/1/di" border="0" ismap="true"&gt;&lt;/img&gt;&lt;/a&gt;&lt;/p&gt;clustermonkey writes "Intel Corporation and the New York Attorney General have agreed to terminate the lawsuit alleging violation of U.S. and state antitrust laws that was filed by the New York Attorney General in November 2009. Intel did not have to admit any violation of law (if there ever was any) nor did it have to admit or deny that the allegations in the complaint are true. Most importantly, the settlement does not require any changes to how the company does business. The settlement includes a $6.5 million payment that is "intended only to cover some of the costs incurred by the New York Attorney General in the litigation." Here's the full settlement, and Intel's official press release."&lt;p&gt;&lt;div class="share_submission" style="position:relative;"&gt;
&lt;a class="slashpop" href="http://twitter.com/home?status=Intel+Settles+NY+Antitrust+Case%3A+http%3A%2F%2Fbit.ly%2FxSIaoP"&gt;&lt;img src="http://a.fsdn.com/sd/twitter_icon_large.png"&gt;&lt;/a&gt;
&lt;a class="slashpop" href="http://www.facebook.com/sharer.php?u=http%3A%2F%2Fyro.slashdot.org%2Fstory%2F12%2F02%2F09%2F238211%2Fintel-settles-ny-antitrust-case%3Futm_source%3Dslashdot%26utm_medium%3Dfacebook"&gt;&lt;img src="http://a.fsdn.com/sd/facebook_icon_large.png"&gt;&lt;/a&gt;

&lt;a class="nobg" href="http://plus.google.com/share?url=http://yro.slashdot.org/story/12/02/09/238211/intel-settles-ny-antitrust-case?utm_source=slashdot&amp;amp;utm_medium=googleplus" onclick="javascript:window.open(this.href,'', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=600,width=600');return false;"&gt;&lt;img src="http://www.gstatic.com/images/icons/gplus-16.png" alt="Share on Google+"/&gt;&lt;/a&gt;                                                                                                                                                                              



&lt;/div&gt;&lt;/p&gt;&lt;p&gt;&lt;a href="http://yro.slashdot.org/story/12/02/09/238211/intel-settles-ny-antitrust-case?utm_source=rss1.0moreanon&amp;amp;utm_medium=feed"&gt;Read more of this story&lt;/a&gt; at Slashdot.&lt;/p&gt;&lt;iframe src="http://slashdot.org/slashdot-it.pl?op=discuss&amp;amp;id=2663639&amp;amp;smallembed=1" style="height: 300px; width: 100%; border: none;"&gt;&lt;/iframe&gt;&lt;img src="http://feeds.feedburner.com/~r/Slashdot/slashdot/~4/GL8WkhWMmoE" height="1" width="1"/&gt;</description>

<dc:creator>samzenpus</dc:creator>
<dc:date>2012-02-10T01:23:00+00:00</dc:date>
<dc:subject>intel</dc:subject>
<slash:department>show-us-the-money</slash:department>
<slash:section>yro</slash:section>
<slash:comments>14</slash:comments>
<slash:hit_parade>14,14,11,9,1,0,0</slash:hit_parade>
<feedburner:origLink>http://yro.slashdot.org/story/12/02/09/238211/intel-settles-ny-antitrust-case?utm_source=rss1.0mainlinkanon&amp;utm_medium=feed</feedburner:origLink></item>

<textinput rdf:about="http://slashdot.org/search.pl">
<title>Search Slashdot</title>
<description>Search Slashdot stories</description>
<name>query</name>
<link>http://slashdot.org/search.pl</link>
</textinput>
</rdf:RDF>
"""

    def testStripTags(self):
        self.assertEqual(
            self.feeder.strip_tags("hello world"),
            "hello world")

        self.assertEqual(
            self.feeder.strip_tags("hello again &lt;a href bleep bloop&gt;world"),
            "hello again world")

        self.assertEqual(
            self.feeder.strip_tags("the following text &lt;b&gt;is bold"),
            "the following text is bold")

        self.assertEqual(
            self.feeder.strip_tags("many &lt;br&gt; line &lt;BR&gt; breaks &lt;br /&gt;"),
            "many line breaks ")

        self.assertEqual(
            self.feeder.strip_tags("decoded <b>tags</b> too"),
            "decoded tags too")

        self.assertEqual(
            self.feeder.strip_tags("no problem on the last char</table>"),
            "no problem on the last char ")

    def testGoogle(self):
        filtered_text = self.feeder.filter(feedparser.parse(self.google_sample_xml))

        good_words = self.feeder.good_words(filtered_text)
        self.assertEqual(set(good_words), 
                         set([u'help', u'abusive', u'philadelphia', u'homeowner', u'agreed', u'reuters', u'over', u'have', u'ailing', u'mail', u'news', u'settlement', u'worth', u'francisco', u'mortgage', u'mortgage', u'housing', u'that', u'falls', u'practices', u'five', u'bloomberg', u'news', u'chronicle', u'government', u'million', u'borrowers', u'viswanatha', u'answers', u'abuses', u'inquirer', u'magic', u'view', u'billion', u'still', u'bullet', u'globe', u'roughly', u'agree', u'aruna', u'foreclosure', u'accused', u'questions', u'banks', u'reached', u'settlement', u'businessweek']))

    def testSlashdot(self):
        filtered_text = self.slashdot_feeder.filter(feedparser.parse(self.slashdot_sample_xml))

        good_words = self.feeder.good_words(filtered_text)
        self.assertEqual(set(good_words),
                         set([u'attorney', u'alleging', u'violation', u'agreed', u'some', u'general', u'have', u'settlement', u'corporation', u'there', u'only', u'state', u'does', u'ever', u'complaint', u'full', u'that', u'terminate', u'company', u'million', u'allegations', u'includes', u'most', u'york', u'filed', u'press', u'november', u'lawsuit', u'payment', u'incurred', u'deny', u'intel', u'antitrust', u'require', u'official', u'cover', u'admit', u'costs', u'changes', u'laws']))

    def testWordIsGood(self):
        # too short
        self.assertFalse(self.feeder.word_is_good('hat'))
        # characters other than string.lower
        self.assertFalse(self.feeder.word_is_good('border="0"'))

        self.assertTrue(self.feeder.word_is_good('hats'))
        self.assertTrue(self.feeder.word_is_good('abracadabra'))

if __name__ == '__main__':
    unittest.main()
