#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020,  Magic Fang, magicfang@gmail.com
#
# Distributed under terms of the GPL-3 license.

import argparse, re, time
from bs4 import SoupStrainer, BeautifulSoup
from selenium import webdriver


"""
%HERE%
"""
class GoogleCitations:
    citation_url = 'https://scholar.google.com/citations'
    wait_secs = 30
    sleep_secs = 5
    def __init__(self, infile='', id='', hl='en'):
        self.fn = infile
        self.id = id
        self.hl = hl
        pagesrc = ''
        if self.fn:
            with open(self.fn, 'r') as fh:
                for ln in fh:
                    pagesrc += ln
        elif self.id:
            url = self.citation_url+'?user={}&hl={}'.format(self.id, self.hl)
            driver = webdriver.Chrome()
            driver.implicitly_wait(self.wait_secs)
            driver.get(url)
            try:
                button = driver.find_element_by_id('gsc_bpf_more')
                page = driver.find_element_by_id('gsc_a_nn')
            except:
                driver.close()
            last = 0
            res = re.search(r'(\d+)\–(\d+)$', page.text)
            if res:
                current = int(res.group(2))
                while last != current:
                    button.click()
                    time.sleep(self.sleep_secs)
                    last = current
                    res = re.search(r'(\d+)\–(\d+)$', page.text)
                    if res:
                        current = int(res.group(2))
                    else:
                        break
                pagesrc = driver.page_source
            driver.close()
        if pagesrc:
            self.soup = BeautifulSoup(pagesrc, 'html.parser')
    
    def _trimtags(self, tstr):
        rstr = re.sub(r'\<[^\>]+\>', '', tstr)
        rstr = re.sub(r'\<\/[^\>]+\>', '', rstr)
        return rstr

    def coauthors(self):
        ul = self.soup.find('ul', class_='gsc_rsb_a')
        if ul:
            for li in ul.find_all('li'):
                author = {}
                a = li.find('a')
                author['name'] = a.string
                author['url'] = a['href']
                aid = re.search(r'user=(.{12})', a['href'])
                if aid:
                    author['id'] = aid.group(1)
                else:
                    author['id'] = ''
                span = li.find('span', class_='gsc_rsb_a_ext')
                author['affi'] = span.string
                yield author
        else:
            return []

    def stat(self):
        table = self.soup.find('table', id='gsc_rsb_st')
        cit = {}
        tags = ('t', 't5', 'h', 'h5', 'i', 'i10')
        counter = 0
        for tr in table.tbody.find_all('tr'):
            for td in tr.find_all('td', class_='gsc_rsb_std'):
                cit[tags[counter]] = td.string
                counter += 1
        return cit


    def byyear(self):
        div = self.soup.find('div', class_='gsc_g_hist_wrp')
        ydiv = div.find('div', class_='gsc_md_hist_b')
        dist = {}
        dist['year'] = []
        dist['cits'] = []
        for yspan in ydiv.find_all('span', class_='gsc_g_t'):
            dist['year'].append(yspan.string)
        for ca in div.find_all('a', class_='gsc_g_a'):
            dist['cits'].append(ca.string)
        return dist
        

    def author(self):
        author = {}
        adiv = self.soup.find('div', id='gsc_prf_i')
        author['name'] = adiv.find('div', id='gsc_prf_in').string
        affa = adiv.find('a', class_='gsc_prf_ila') 
        author['aff'] = affa.string
        author['affurl'] = affa['href']
        author['focus'] = []
        for a in adiv.find_all('a', class_='gsc_prf_inta'):
            author['focus'].append({'key':a.string, 'url': a['href']})
        return author

    def pubs(self):
        table = self.soup.find('table', id='gsc_a_t')
        if not table:
            return []
        for tr in table.tbody.find_all('tr'):
            row = {}
            ttd = tr.find('td', class_='gsc_a_t')
            ctd = tr.find('td', class_='gsc_a_c')
            ytd = tr.find('td', class_='gsc_a_y')
            row['title'] = ttd.a.string
            divs = ttd.find_all('div', class_='gs_gray')
            row['authors'] = divs[0].string
            row['journal'] = self._trimtags(str(divs[1]))
            row['citations'] = ctd.a.string
            row['year'] = ytd.span.string
            yield row
        


if __name__ == '__main__':
    parser = argparse.ArgumentParser();
    parser_group = parser.add_mutually_exclusive_group(required=True)
    parser_group.add_argument("-i", "--infile", help = "input file")
    parser_group.add_argument("-d", "--id", help = "author id")
    args = parser.parse_args()
    if args.infile:
        gc = GoogleCitations(infile=args.infile)
    else:
        gc = GoogleCitations(id=args.id)
    print(gc.author())
    print(gc.stat())
    print(gc.byyear())
    for pub in gc.pubs():
        print(pub)
    for au in gc.coauthors():
        print(au)

