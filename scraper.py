#!/usr/bin/python

import scraperwiki
import lxml.html
import uuid
import datetime
import re
import sys
import requests

def main(argv):

    if len(argv) != 2:
       print("Wrong number of arguments ({}), should be 2 (search-term and number-of-results)".format(str(len(argv))))
       sys.exit(2)

    search_term = argv[0]
    search_result_count = argv[1]

    bingurl = "https://www.bing.com/search?q=" + search_term + "+site:amazon.co.uk&count=" + str(search_result_count)
    binghtml = scraperwiki.scrape(bingurl)

    bingroot = lxml.html.fromstring(binghtml)

    bingresults = bingroot.xpath("//h2/a/@href")
    asinregex = re.compile("^[A-Z0-9]{10}$")

    ASINS = []

    for result in bingresults:
        urlparts = result.split('/')
        qasin = urlparts[-1]
        if asinregex.match(qasin):
            ASINS.append(qasin)
            #print(result, qasin)

    summary = ""

    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
        }

    item_price_list = []

    for asin in ASINS:

        item_price = ["", ""]

        url = "https://www.amazon.co.uk/dp/" + asin

        #print("[{}]".format(url))
        page = requests.get(url, headers=headers)
        #html = scraperwiki.scrape(url)
        html = page.text
        #print(html)
        amazonroot = lxml.html.fromstring(html)

        amazontitle = amazonroot.xpath("//span[@id='productTitle']")
        strtitle = ""
        for title in amazontitle:
            strtitle = title.text.strip()
            if strtitle != "":
                item_price[0] = strtitle
            break

        amazonprice = amazonroot.xpath("//span[@id='priceblock_ourprice']")
        strprice = ""
        for price in amazonprice:
            strprice = price.text.strip()
            if strprice != "" and item_price[0] != "":
                item_price[1] = strprice
            break

        if item_price[0] != "" and item_price[1] != "":
            item_price_list.append(item_price)
            print(item_price[1] + " - " + item_price[0])

            now = datetime.datetime.now()
            data = {
                'link': url,
                'uuid' : str(uuid.uuid1()),
                'title': "Price Monitoring " + str(now),
                'description': item_price[0] + ": " + item_price[1],
                'pubDate': str(now),
            }

            scraperwiki.sqlite.save(unique_keys=['link'],data=data)
            #print("Saved to sqlite DB: [{}]".format(data))
        #print("------")



if __name__ == "__main__":
    main(sys.argv[1:])
