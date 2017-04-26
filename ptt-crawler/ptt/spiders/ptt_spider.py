import logging
from datetime import datetime
import scrapy
#from scrapy.http import Request,FormRequest
from ptt.items import PostItem


class PTTSpider(scrapy.Spider):
    name = 'ptt'
    allowed_domains = ['ptt.cc']
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'}
    start_urls = ('https://www.ptt.cc/bbs/Gossiping/index.html', )

    _pages = 0
    MAX_PAGES = 2
    
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url,cookies={'over18':'1'}, callback=self.parse, headers=self.headers)


    def parse(self, response):
        self._pages += 1
        for href in response.css('.r-ent > div.title > a::attr(href)'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, callback=self.parse_post, headers=self.headers)

        if self._pages < PTTSpider.MAX_PAGES:
            next_page = response.xpath(
                '//div[@id="action-bar-container"]//a[contains(text(), "上頁")]/@href')
            if next_page:
                url = response.urljoin(next_page[0].extract())
                logging.warning('follow {}'.format(url))
                yield scrapy.Request(url, callback=self.parse , headers=self.headers)
            else:
                logging.warning('no next page')
        else:
                logging.warning('max pages reached')

    def parse_post(self, response):
        item = PostItem()
        item['author'] = response.xpath(
            '//div[@class="article-metaline"]/span[text()="作者"]/following-sibling::span[1]/text()')[0].extract().split(' ')[0]
        #Tittle in article-metaline is trancated, so we tage title in og:title
        item['title'] = response.xpath('//meta[@property="og:title"]/@content')[0].extract()
        datetime_str = response.xpath(
            '//div[@class="article-metaline"]/span[text()="時間"]/following-sibling::span[1]/text()')[0].extract()
        item['date'] = datetime.strptime(datetime_str, '%a %b %d %H:%M:%S %Y')
        item['content'] = response.xpath('//div[@id="main-content"]/text()')[0].extract()
        item['ip'] = response.xpath(
            '//div[@id="main-content"]/span[contains(text(),"發信站: 批踢踢實業坊(ptt.cc)")]/text()')[0].extract().rstrip().split(' ')[-1:][0]
        comments = []
        total_score = 0
        for comment in response.xpath('//div[@class="push"]'):
            push_tag = comment.css('span.push-tag::text')[0].extract()
            push_user = comment.css('span.push-userid::text')[0].extract()
            push_content = comment.css('span.push-content::text')[0].extract()

            if '推' in push_tag:
                score = 1
            elif '噓' in push_tag:
                score = -1
            else:
                score = 0

            total_score += score
            comments.append({'user': push_user,
                             'content': push_content,
                             'score': score})

        item['comments'] = comments
        item['score'] = total_score
        item['url'] = response.url
        print ( "%s  %-4s %-14s %s" % (item['date'],item['score'],item['author'],item['title']) )
        print (item['content'])
        yield item

