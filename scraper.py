#!/usr/bin/python

'''
Created on 3 Nov 2016

@author: incidentnormal
'''

import requests
import lxml.html
import scraperwiki
import datetime
import re
import sys

class G:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    googxpath = "//h3[@class='r']/a/@href"
    asinregex = re.compile("^[A-Z0-9]{10}$")
    traktxpath_price = "//span[@class='price']"
    traktxpath_name = "//div[@id='product_title']"

class azProduct:
    def __init__(self, asin=None, url=None, productName=None, productPrice=None):
        self.timeStamp = datetime.datetime.now()
        self.asin = asin
        self.url = url
        self.productName = productName
        self.productPrice = productPrice
        self.scrap = False
    def getSqliteDatagram(self):
        data = {
                'url': self.url,
                'asin': self.asin,
                'name': self.productName,
                'price': self.productPrice,
                'timestamp':self.timeStamp,
                }
        return data
    def selfDestruct(self):
        self.scrap = True

def parseArgs(argv):

    script_name = argv[0]

    search_term = None
    search_result_count = 10

    if len(argv) == 1:
        print("Wrong number of arguments ({}), should be:\n {} search terms... <number-of-results>".format(str(len(argv)-1), script_name))
        sys.exit(2)
    elif len(argv) == 2:
        search_term = argv[-1]
    else:
        if not argv[-1].isdigit():
            search_term = argv[1:]
        else:
            search_term = argv[1:-1]
            search_result_count = int(argv[-1])

        if len(search_term) > 1:
            search_term = "%20".join(search_term)
        else:
            search_term = search_term[0]

    return search_term, search_result_count

def getGoogResults(searchTerm, resultCount):
    googurl = "https://www.google.co.uk/search?q={site:www.amazon.co.uk " + searchTerm + "}&num=" + str(resultCount)
    return runScrape(googurl, G.googxpath)
    
def runScrapeRequest(url):
    resp = requests.get(url, headers=G.headers)
    root = lxml.html.fromstring(resp.text)
    return root

def parseXpath(root, xpath):
    return root.xpath(xpath)

def runScrape(url, xpath):
    root = runScrapeRequest(url)
    return parseXpath(root, xpath)

def splitUrl(url, iSect):
    return url.split('/')[iSect]

def checkAsin(qasin):
    if G.asinregex.match(qasin):
        return qasin
    return None

def getAsin(url):
    return checkAsin(splitUrl(url, -1))

def runTraktorScrape(azp):
    trakturl = "https://thetracktor.com/detail/" + azp.asin + "/uk/"
    traktroot = runScrapeRequest(trakturl)
    
    traktprodnames = parseXpath(traktroot, G.traktxpath_name)
    traktprices = parseXpath(traktroot, G.traktxpath_price)
    
    if traktprices and traktprodnames:
        price = traktprices[0].text_content().strip()
        if not price:
            azp.selfDestruct()
        elif price[0] == "$":
            price = unichr(163) + price[1:]        
        azp.productPrice = price
        
        name = traktprodnames[0].text_content().strip()
        if not name:
            azp.selfDestruct()
        else:
            azp.productName = name
    else:
        azp.selfDestruct()
    

def main(argv):

    searchTerm, resultCount = parseArgs(argv)
    
    googresults = getGoogResults(searchTerm, resultCount)
    
    azProducts = [] # Currently unused

    for res in googresults:
        asin = getAsin(res)
        if asin != None:
            azp = azProduct(asin=asin, url=res)
            runTraktorScrape(azp)
            if not azp.scrap:
                azProducts.append(azp)
                print(str(azp.getSqliteDatagram()))
                scraperwiki.sqlite.save(unique_keys=['asin'], data=azp.getSqliteDatagram())

if __name__ == "__main__":
    main(sys.argv)
