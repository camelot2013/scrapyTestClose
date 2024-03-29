# -*- coding: utf-8 -*-
import scrapy
import re
import json
from scrapyTest.items import TlCygItem
import sqlite3

menpaidict = {0: u'少林', 1: u'明教', 2: u'丐帮', 3: u'武当', 4: u'峨眉', 5: u'星宿', 6: u'天龙', 7: u'天山', 8: u'逍遥', 10: u'慕容',
              11: u'唐门', 12: u'鬼谷'}
sexdict = {0: u'女', 1: u'男'}


class TlCygSpider(scrapy.Spider):
    name = 'tl.cyg'
    allowed_domains = ['tl.cyg.changyou.com']
    start_urls = ['http://tl.cyg.changyou.com/goods/selling']
    # start_urls = [
    #     'http://tl.cyg.changyou.com/?area_name=%25E8%2587%25B3%25E5%25B0%258A%25E7%2594%25B5%25E4%25BF%25A1&world_id=3079&world_name=%25E9%259B%25AA%25E8%2588%259E%25E7%2587%2583%25E6%2583%2585#goodsTag']
    url_set = set()
    __conn = sqlite3.connect('scrapyTest/roleinfo.sqlite')
    __c = __conn.cursor()
    __c.execute("SELECT * FROM {}".format('cyg_roleinfo'))
    col_name_list = [tuple[0] for tuple in __c.description]
    __conn.close()

    def detail_parse(self, response):
        goodsinfo = response.css('div.goods-info .info-list .ui-money-color::text').extract()[0]
        item = TlCygItem()
        item['url'] = response.url
        item['price'] = re.findall('\d+', goodsinfo)[0]

        scriptinfo = response.css('script')
        a1 = scriptinfo[25].css('::text').extract()[0]
        sjson = a1.partition('var charObj = ')[2]
        # 字符串尾部可能有多余字符，去除最后一个}之后的所有多余字符
        sjson = "".join([sjson.strip().rsplit("}", 1)[0], "}"])
        pjson = json.loads(sjson)
        for column in TlCygSpider.col_name_list:
            if column in pjson:
                item[column] = pjson[column]
        item['wh_growRate'] = 0
        item['wh_compandLevel'] = ''
        item['wg_wuHunExtLanNum'] = ''
        if 'items' in pjson:
            items = pjson['items']
            if 'equip' in items:
                equip = items['equip']
                if '15' in equip:
                    wuhun = equip['15']
                    item['wh_growRate'] = re.findall('\d+', wuhun['growRate'])[0]
                    item['wh_compandLevel'] = wuhun['compandLevel']
                    item['wg_wuHunExtLanNum'] = wuhun['wuHunExtLanNum']

        yield item

    def parse_baseinfo(self, baseinfo):
        infos = baseinfo.css('::text').extract()
        if len(infos) > 1:
            return infos[0] + infos[1]
        else:
            return infos[0]

    def parse(self, response):
        goodslist = response.css('div.jGoodsList .pg-goods-list a::attr(href)').extract()
        for goods in goodslist:
            if goods not in TlCygSpider.url_set:
                TlCygSpider.url_set.add(goods)
                yield scrapy.http.Request(goods, callback=self.detail_parse, dont_filter=True)

        pagealist = response.css('div.jGoodsList .ui-pagination a::attr(href)').extract()
        if len(pagealist) > 1:
            if pagealist[-1] <> 'javascript:void(0)':
                next_url = pagealist[-1]
                yield scrapy.Request(next_url, callback=self.parse)
