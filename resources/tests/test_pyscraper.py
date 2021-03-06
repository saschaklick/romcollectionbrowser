# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'lib'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'lib', 'pyparsing'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'lib', 'pyscraper'))

from resources.lib.pyscraper.pyscraper import PyScraper
from resources.lib.config import Config, Scraper
import resources.lib.util as util

import unittest


class TestPyScraper(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		# This is required so that readScraper() can parse the XML instruction files
		util.RCBHOME = os.path.join(os.path.dirname(__file__), '..', '..')

	def test_PrepareScraperSource(self):
		# Setup the scraper by loading the default config_template.xml distributed with RCB (see test_config_scraper.py)
		config_xml_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'config_template.xml')
		conf = Config(config_xml_file)
		conf.initXml()

		sites, msg = conf.readScrapers(conf.tree)
		scrapers = sites['giantbomb.com'].scrapers

		# Proceed with the test
		ps = PyScraper()
		# FIXME log not set to debug level - needs to be
		url = ps.prepareScraperSource(scrapers[0], scrapers[0].source, "Final Fantasy (USA)")
		self.assertEqual(url, "http://api.giantbomb.com/search/?api_key=279442d60999f92c5e5f693b4d23bd3b6fd8e868&query=Final%20Fantasy%20%28USA%29&resources=game&field_list=api_detail_url,name&format=xml", "Expected URL to be parsed correctly")

	def test_AddNewElements(self):
		ps = PyScraper()
		existingResults = {"SearchKey": ["Tekken 2"], "Publisher": []}
		newResults = {"SearchKey": ["Tekken 3"], "Description": ["Tekken 2 description &amp; history"], "Publisher": ["Namco"]}
		existingResults = ps.addNewElements(existingResults, newResults)

		self.assertIn("Description", existingResults, "Expected to add Description")
		self.assertEqual(existingResults.get("SearchKey")[0], "Tekken 2",
			"Expected existing field SearchKey to not be overwritten (now {0}".format(existingResults.get("SearchKey")[0]))
		self.assertEqual(existingResults.get("Publisher")[0], "Namco",
			"Expected existing but empty field Publisher to be overwritten")
		self.assertEqual(existingResults.get("Description")[0], "Tekken 2 description & history",
			"Expected HTML special characters to be converted")

	def test_AddNewElementsUnicode(self):
		ps = PyScraper()
		existingResults = {"SearchKey": ["Random Game"]}
		newResults = {"Description": [u"'Super Keirin (スーパー競輪, Super Keirin) is a Japan-exclusive video game"]}
		existingResults = ps.addNewElements(existingResults, newResults)

		self.assertEqual(existingResults.get("Description")[0], u"'Super Keirin (スーパー競輪, Super Keirin) is a Japan-exclusive video game",
			"Expected Unicode string to be handled when adding new search result element")

	def test_ReplaceSequelNumbers(self):
		# Tests identifying a sequel number and converting to roman numeral equivalent
		ps = PyScraper()
		x = ps.replaceSequelNumbers("Final Fantasy 9")
		self.assertEqual(x, "Final Fantasy IX", "Sequel number at end of game not replaced properly")

		x = ps.replaceSequelNumbers("Final Fantasy 9: Subtitle")
		self.assertEqual(x, "Final Fantasy IX: Subtitle", "Sequel number at end of game not replaced properly")

		x = ps.replaceSequelNumbers("Final Fantasy 9 (Subtitle)")
		self.assertEqual(x, "Final Fantasy IX (Subtitle)", "Sequel number at end of game not replaced properly")

		x = ps.replaceSequelNumbers("Final Fantasy IX")
		self.assertEqual(x, "Final Fantasy IX", "Sequel number in roman numeral form should be retained")

		# FIXME TODO An example where this doesn't work
		# x = ps.replaceSequelNumbers("Final Fantasy 11")
		# self.assertEqual(x, "Final Fantasy XI", "Multiple digits should be interpreted as a group")

		# x = ps.replaceSequelNumbers("Miner 2049er")
		# self.assertEqual(x, "Miner 2049er", "Non-sequel number should not be replaced")

	# Test matching against a result set
	def test_getBestResultsWithRomanNumerals(self):
		results = [{'SearchKey': ['Tekken 2']}, {'SearchKey': ['Tekken 3']}, {'SearchKey': ['Tekken IV']}]
		gamename = 'Tekken II'

		ps = PyScraper()
		x = ps.getBestResults(results, gamename)
		self.assertIsInstance(x, dict, "Expected a matching dict to be returned")
		self.assertTrue(x.get('SearchKey')[0] == 'Tekken 2', "Expected to match title (was {0})".format(x.get('SearchKey')[0]))

	def test_getBestResultsWithApostropheAndYear(self):
		results = [{'SearchKey': ['FIFA 98']}, {'SearchKey': ['FIFA 97']}, {'SearchKey': ['FIFA 2001']}]
		gamename = 'FIFA \'98'

		ps = PyScraper()
		x = ps.getBestResults(results, gamename)
		self.assertTrue(x.get('SearchKey')[0] == 'FIFA 98', "Expected to match title (was {0})".format(x.get('SearchKey')[0]))

	def test_getBestResultsMatchingWithUnicode(self):
		results = [{'SearchKey': [u'スーパー競輪']}]
		gamename = u'スーパー競輪'
		ps = PyScraper()
		x = ps.getBestResults(results, gamename)
		self.assertTrue(x.get('SearchKey')[0] == u'スーパー競輪', "Expected matching unicode strings to match")

	def test_getBestResultsNonMatchingWithUnicode(self):
		results = [{'SearchKey': [u'スーパー競輪']}]
		gamename = 'Super Test Game'
		ps = PyScraper()
		x = ps.getBestResults(results, gamename)
		self.assertIsNone(x, "Expected non-matching strings to not match, including unicode")

	@unittest.skip("This fails and the code needs to be fixed as this is a legitimate filename")
	def test_getBestResultsWithBrackets(self):
		results = [{'SearchKey': ['FIFA 98']}, {'SearchKey': ['FIFA 97']}, {'SearchKey': ['FIFA 2001']}]
		gamename = 'FIFA \'98 (1998) [Electronic Arts]'

		ps = PyScraper()
		x = ps.getBestResults(results, gamename)
		self.assertTrue(x.get('SearchKey')[0] == 'FIFA 98', "Expected to match title (was {0})".format(x.get('SearchKey')[0]))

	def test_checkSequelNoIsEqual(self):
		ps = PyScraper()
		self.assertTrue(ps.checkSequelNoIsEqual("Final Fantasy IX", "Final Fantasy 9"), "Expected IX to match with 9")
		self.assertTrue(ps.checkSequelNoIsEqual("Final Fantasy X", "Final Fantasy 10"), "Expected X to match with 10")
		self.assertTrue(ps.checkSequelNoIsEqual("Final Fantasy II", "Final Fantasy 2"), "Expected II to match with 2")
		self.assertTrue(ps.checkSequelNoIsEqual("Fifa 98", "FIFA 98"), "Game ending with a year should be matched")

	def test_getSequelNoIndex(self):
		ps = PyScraper()
		y = ps.getSequelNoIndex("Legend of Zelda, The - A Link to the Past (USA)")
		self.assertTrue(y == -1, "Game name with no number should return -1")
		y = ps.getSequelNoIndex("Super Mario World 2 - Yoshi's Island (USA)")
		self.assertTrue(y == 8, "Did not find sequel index for number (found {0})".format(y))
		y = ps.getSequelNoIndex("Final Fantasy XIII")
		self.assertTrue(y != -1, "Did not find sequel index for roman numeral above 10 (found {0})".format(y))

if __name__ == "__main__":
	unittest.main()
