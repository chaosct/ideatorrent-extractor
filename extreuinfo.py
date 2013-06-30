# -*- coding: utf-8 -*-

import re
import requests
from bs4 import BeautifulSoup
from unipath import Path
import json

reRaonament = re.compile("Raonament")
reData = re.compile(
    r'el (?P<dia>\d+) (?P<mes>\w+) (?P<any>\d+) a les (?P<hora>\d\d:\d\d)')


def sanitize(s, multiline=False):
    s = s.replace('\r', '\n').strip()
    if not multiline:
        s = s.replace('\n', '')
    return s


def urlgenerator(begin=0,end=300):
    urlbase = "https://xifrat.pirata.cat/ideatorrent/idea/{}"
    for n in range(begin, end):
        url = urlbase.format(n)
        yield n, url


def walkweb():
    session = requests.session()
    for n, url in urlgenerator(begin=0, end=300):
        req = session.get(url)
        print req.status_code, url
        if req.status_code == 200:
            entry = analyze(req.content, n, url)
            savejson(entry)


def analyze(cont, n, url):
    doc = BeautifulSoup(cont)

    titol = doc.find('div', text=re.compile("Idea #{}:".format(n))).text
    titol = sanitize(titol)
    desc = doc.find('div', text=reRaonament).parent("div")[1].text
    desc = sanitize(desc, multiline=True)
    status = doc.find(id='status_string').text
    status = sanitize(status)

    entry = dict(titol=titol, desc=desc,
                 status=status, id=n, solutions=[], url=url)

    data = reData.search(doc.find(class_="authorlink").parent.text)
    entry['any'] = int(data.group('any'))
    entry['mes'] = data.group('mes')
    entry['dia'] = int(data.group('dia'))
    entry['hora'] = data.group('hora')

    solutions = [int(sid['value']) for sid in doc.find_all(
        attrs={'name': "solution-id"})]
    for sid in solutions:
        vup = int(doc.find(id='voteupcount-{}'.format(sid)).text)
        vequal = int(doc.find(id='voteequalcount-{}'.format(sid)).text)
        vdown = int(doc.find(id='votedowncount-{}'.format(sid)).text)
        title = sanitize(doc.find(
            id='solution-title-{}'.format(sid)).parent.text)
        desc = sanitize(doc.find(
            id="solution-description-{}".format(sid)).text)
        dsol = dict(id=sid, up=vup, equal=vequal,
                    down=vdown, title=title, desc=desc)
        entry['solutions'].append(dsol)

    return entry


def savejson(d):
    status = d['status']
    if status.startswith('Pendent'):
        status = 'Pendent'
    carpeta = Path(status, d['any'], d['mes'])
    carpeta.mkdir(parents=True)
    fpath = carpeta.child('{}.json'.format(d['id']))
    with open(fpath, 'w') as f:
        json.dump(d, f, sort_keys=True, indent=4, separators=(',', ': '))


def main():
    walkweb()

if __name__ == '__main__':
    main()
