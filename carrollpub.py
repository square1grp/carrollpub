import requests
from lxml import etree
import pdb
from urllib.request import urlopen
import json
import csv
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time

options = Options()
# options.headless = True
driver = webdriver.Chrome('./chromedriver', chrome_options=options)
driver.get('http://www.carrollpub.com/Subscribers/login.asp')

driver.find_element_by_css_selector('#contentArea input[name=UserID]').clear()
driver.find_element_by_css_selector('#contentArea input[name=UserID]').send_keys('******************')

driver.find_element_by_css_selector('#contentArea input[name=Password]').clear()
driver.find_element_by_css_selector('#contentArea input[name=Password]').send_keys('******************')

driver.find_element_by_css_selector('#contentArea input[name=_submitButton]').click()

time.sleep(5)

cookies = {}
cookie_string = []
for cookie in driver.get_cookies():
	cookies[cookie['name']] = cookie['value']
	cookie_string.append('%s=%s' % (cookie['name'], cookie['value']))

cookie_string = '; '.join(cookie_string)
logging.basicConfig(filename='error.log',level=logging.DEBUG)
logging.warning(cookie_string)

driver.close()

us_states = {}

with open('states.json', 'r') as f:
	us_states = json.loads(f.read())

input_file = csv.DictReader(open("queries.csv"))

queries = []
for row in input_file:
    queries.append(row)


session = requests.Session()
with open('results.csv', 'w+') as result_file:

	head_line = 'LastName, Salutation, FirstName, MiddleInit, Title, OfficeName, Within Office(1), WithinOffice(2), In Headquarters, Street1, Street2, Room Number, City, State, ZipCode, Phone, Fax, Email, Population, County, CP Data Source'

	result_file.write(head_line + '\n')

	def run_search_query(state_abbr, muniName):
		response = session.get('http://www.carrollpub.com/Subscribers/personresults.asp?biDirect=99&countSubmits=0&Level=16&orgStateList=%s&Branch=1&muniName=%s&pop_startRange=25000&whichCensus=Decennial&resultsType=Positions&AllRecs1Page=1&PlumType=65536' % (state_abbr, muniName), cookies=cookies)
		try:
			res_tree = etree.HTML(response.text.encode('utf8'))

			PositionIDs = ', '.join(res_tree.xpath('//input[@name="PositionIDs"]/@value'))

			data='bAllSelected=true&MakeList=true&PositionIDs=%s&ListFormat=1' % PositionIDs
			response = session.post(
				'http://www.carrollpub.com/Subscribers/personresults.asp',
				data=data,
				headers={
					'Content-Type': 'application/x-www-form-urlencoded',
					'Cookie': cookie_string
				}
			)

			res_tree = etree.HTML(response.text.encode('utf8'))

			js_text = res_tree.xpath('//script/text()')[0].strip()
			js_text = js_text.replace('window.location=\'', '')
			js_text = js_text.replace('\'', '') # file name

			with urlopen('http://www.carrollpub.com/Subscribers/%s' % js_text) as f:
				for line in f:
					line = line.strip().decode('utf8')

					if head_line != line:
						print(line)
						result_file.write(line + '\n')
		except:
			print('=========== Exception (%s, %s) ================' % (state_abbr, muniName))
			logging.error('%s, %s\n' % (state_abbr, muniName))
			pass


	for query in queries:
		state_abbr = ''

		for abbr, state in us_states.items():
			if query['state'].strip() == state.strip():
				state_abbr = abbr.strip()
				break

		muniName = query['target'].replace(query['city'], '').replace(query['city'].lower(), '').replace(query['state'], '').replace(query['state'].lower(), '').replace('CDP', '').replace(',', '')

		run_search_query(state_abbr.strip(), muniName.strip())