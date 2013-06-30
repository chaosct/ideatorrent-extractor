# -*- coding: utf-8 -*-

import re
import requests
from bs4 import  BeautifulSoup

def sanitize(s):
    s = s.strip().replace('\r','\n')
    return s


def urlgenerator(begin=0,end=300):
    urlbase = "https://xifrat.pirata.cat/ideatorrent/idea/{}"
    for n in range(begin,end):
        url = urlbase.format(n)
        yield n, url

def walkweb():
    session = requests.session()
    for n, url in urlgenerator(end=50):
        print url
        req = session.get(url)
        print req.status_code, url
        if req.status_code == 200:
            analyze(req.content, n)

def analyze(cont, n):
    doc = BeautifulSoup(cont)
    titol = doc.find('div',text=re.compile("Idea #{}:".format(n))).text
    desc = doc.find('div',text=re.compile("Raonament")).parent("div")[1].text
    titol = sanitize(titol)
    desc = sanitize(desc)

def main():
    walkweb()

if __name__ == '__main__':
    main()