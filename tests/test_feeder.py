#!/usr/bin/env python

import unittest
import feeder
import feedparser
import os

def sample_xml_content(filename):
  tests_dir = os.path.dirname(os.path.realpath(__file__))
  return open(os.path.join(tests_dir, filename)).read()

class testFeeder (unittest.TestCase):
    def setUp(self):
        self.feeder = feeder.getFeeder('Google')

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
        google_sample_xml = sample_xml_content('google_sample.xml')
        filtered_text = self.feeder.filter(feedparser.parse(google_sample_xml))

        good_words = self.feeder.good_words(filtered_text)
        self.assertEqual(set(good_words), 
                         set([u'help', u'abusive', u'philadelphia', u'homeowner', u'agreed', u'reuters', u'over', u'have', u'ailing', u'mail', u'news', u'settlement', u'worth', u'francisco', u'mortgage', u'mortgage', u'housing', u'that', u'falls', u'practices', u'five', u'bloomberg', u'news', u'chronicle', u'government', u'million', u'borrowers', u'viswanatha', u'answers', u'abuses', u'inquirer', u'magic', u'view', u'billion', u'still', u'bullet', u'globe', u'roughly', u'agree', u'aruna', u'foreclosure', u'accused', u'questions', u'banks', u'reached', u'settlement', u'businessweek']))

    def testSlashdot(self):
        slashdot_sample_xml = sample_xml_content('slashdot_sample.xml')

        filtered_text = feeder.getFeeder('Slashdot').filter(feedparser.parse(slashdot_sample_xml))

        good_words = self.feeder.good_words(filtered_text)
        self.assertEqual(set(good_words),
                         set([u'attorney', u'alleging', u'violation', u'agreed', u'some', u'general', u'have', u'settlement', u'corporation', u'there', u'only', u'state', u'does', u'ever', u'complaint', u'full', u'that', u'terminate', u'company', u'million', u'allegations', u'includes', u'most', u'york', u'filed', u'press', u'november', u'lawsuit', u'payment', u'incurred', u'deny', u'intel', u'antitrust', u'require', u'official', u'cover', u'admit', u'costs', u'changes', u'laws']))

    def testDigg(self):
        digg_sample_xml = sample_xml_content('digg_sample.xml')

        filtered_text = feeder.getFeeder('Digg').filter(feedparser.parse(digg_sample_xml))

        good_words = self.feeder.good_words(filtered_text)
        self.assertEqual(set(good_words),
                         set([u'town', u'search', u'made', u'mythical', u'that', u'writer', u'returns', u'beast', u'state', u'jersey', u'native']))

    def testWordIsGood(self):
        # too short
        self.assertFalse(self.feeder.word_is_good('hat'))
        # characters other than string.lower
        self.assertFalse(self.feeder.word_is_good('border="0"'))

        self.assertTrue(self.feeder.word_is_good('hats'))
        self.assertTrue(self.feeder.word_is_good('abracadabra'))

if __name__ == '__main__':
    unittest.main()
