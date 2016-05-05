import logging
from datetime import datetime
import scrapy
#from scrapy.http import Request,FormRequest
from ptt_boards.items import PttBoardsItem

class BoardSpider(scrapy.Spider):
    name = 'board'
    allowed_domains = ['www.ptt.cc']
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'}
    start_urls = ['https://www.ptt.cc/bbs/index.html', ]

    def parse(self, response):
        for href in response.xpath('//dl/dd/p/a'):
            link = href.xpath('@href').extract()[0]
            link = response.urljoin(link)
            if "index.html" in link:
                item = PttBoardsItem() 
                item['title']= link.split('/')[-2]
                item['link'] = link
                print (item['title'],item['link'])
                yield item
            else:
                print ("----------------" + href.xpath('text()').extract()[0] )
                yield scrapy.Request(link, callback=self.parse , headers=self.headers)
        return   
            #yield scrapy.Request(url, callback=self.parse_post, headers=self.headers)

