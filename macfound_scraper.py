##Edwin Gavis and Mike Gu
##03-12-18

import bs4
import urllib3
import csv
import warnings


warnings.filterwarnings("ignore", module='urllib3')
pm = urllib3.PoolManager()

def loot_mac_page(soup):
	'''
	Takes a soup object and returns a list containing grant information and 
	organization description.
	'''
	block = soup.find_all("ul", class_="grant-list")
	rv = []
	try:
		grants = block[0].find_all("li")
	except IndexError:
		return []
	grant_links = []
	for grant in grants:
		grant_info = []
		grant_info.append(grant.h2.text)
		grant_info.append(grant.div.div.text.replace("$", "").replace(",",""))
		descrip = ""
		for link in grant.h2.find_all("a"):
			try:
				url = link["href"]
			except KeyError:
				continue
			if url[0] == "/":
				url = "https://www.macfound.org" + url
				l_soup = get_page_soup(url)
				des = l_soup.find_all("p", "grant-description")
				descrip = des[0].text.replace("\n", "").replace(",","").replace(".","").replace("\t","")
		for date in grant.p.text.replace("\n", "").split(" ", 1):
			grant_info.append(date.replace("  ", ""))		
		grant_info.append(descrip[50:])
		rv.append(grant_info)
	return rv		

def get_page_soup(url):
	'''
    Takes a url and returns the soub object for that url.
	'''
	html = pm.urlopen(url=url, method="GET").data	
	soup = bs4.BeautifulSoup(html, "lxml")
	return soup

def crawl_mac_pages(pages):
	'''
	Crawls through the Macarthur website for their list of grants. Takes a number
	of pages to crawl and writes to a csv the grant information for each page.  
	'''
	start_url = 'http://www.macfound.org/grants/?amount_range=0&year_approved__min=2016&year_approved__max=2017&chicago_area=filtered'
	print("Starting crawl")
	soups_list = []
	count = 1
	while count < pages:
		soups_list.append(get_page_soup(start_url + "&amp;page={}".format(count)))
		count += 1
	grants_list =[]
	print("Pulling data...")
	for soup in soups_list:
		grants_list += loot_mac_page(soup)
	print("Writing to mac_orgs.txt")
	with open("mac_grants+descriptions.csv", 'w', newline='\n') as csvfile:
		mac_writer = csv.writer(csvfile, delimiter='|', quoting=csv.QUOTE_MINIMAL)
		for grant in grants_list:
			mac_writer.writerow(grant)
	csvfile.close()

if __name__ == "__main__":
	crawl_mac_pages(171)
