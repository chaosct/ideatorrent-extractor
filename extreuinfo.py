# -*- coding: utf-8 -*-

import re
import requests
from bs4 import BeautifulSoup
from unipath import Path
import json
import sys

exportpath = Path('export')

reRaonament = re.compile("Raonament")
reData = re.compile(
    r'el (?P<dia>\d+) (?P<mes>\w+) (?P<any>\d+) a les (?P<hora>\d\d:\d\d)')
reFinData = re.compile(
    r"ha finalitzat el (?P<dia>\d+) (?P<mes>\w+) (?P<any>\d+)")
reDevel = re.compile(
    r"in development the (?P<dia>\d+) (?P<mes>\w+) (?P<any>\d+)")
reImpl = re.compile(r"implemented the (?P<dia>\d+) (?P<mes>\w+) (?P<any>\d+)")
reDup = re.compile(r"This idea is a duplicate")

monthnames = {
'Jan': 1,
'Feb': 2,
'Mar': 3,
'Apr': 4,
'May': 5,
'Jun': 6,
'Jul': 7,
'Aug': 8,
'Sep': 9,
'Oct': 10,
'Nov': 11,
'Dec': 12,
}

monthnames2 = {
'January': 1,
'February': 2,
'March': 3,
'April': 4,
'May': 5,
'June': 6,
'July': 7,
'August': 8,
'September': 9,
'October': 10,
'November': 11,
'December': 12,
}


def flush():
    sys.stdout.flush()


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
    for n, url in urlgenerator(begin=11, end=300):
        print url,
        flush()
        repeat = True
        while repeat:
            try:
                req = session.get(url)
                repeat = False
            except requests.exceptions.ConnectionError:
                print "Retry...",
                flush()
        print req.status_code
        if req.status_code == 200:
            entry = analyze(req.content, n, url)
            savejson(entry)
        elif req.status_code == 404:
            break


def extractdate(gr, hour=False, monthdict=None):
    ddate = {}
    ddate['any'] = int(gr.group('any'))
    ddate['mes'] = gr.group('mes')
    if monthdict:
        ddate['mes'] = monthdict[ddate['mes']]
    ddate['dia'] = int(gr.group('dia'))
    if hour:
        ddate['hora'] = gr.group('hora')
    return ddate


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
    entry.update(extractdate(data, hour=True, monthdict=monthnames))

    # Finalization Date
    if status == "Finalitzada":
        datafin = doc.find(
            'div', class_='notice_div_main').find('span', text=reFinData)
        if datafin:
            datafin = reFinData.search(datafin.text)
            fdata = extractdate(datafin, monthdict=monthnames2)
            entry['final'] = fdata
    if status == "In development":
        datafin = doc.find(
            'div', class_='notice_div_main').find('span', text=reDevel)
        if datafin:
            datafin = reDevel.search(datafin.text)
            fdata = extractdate(datafin, monthdict=monthnames2)
            entry['final'] = fdata
    if status == "Ja portades a terme":
        datafin = doc.find(
            'div', class_='notice_div_main').find('span', text=reImpl)
        if datafin:
            datafin = reImpl.search(datafin.text)
            fdata = extractdate(datafin, monthdict=monthnames2)
            entry['final'] = fdata

    # duplicate?
    dup = doc.find('div', class_='notice_div_main')
    dup = dup and dup.find(text=reDup)
    if dup:
        dupurl = dup.parent.find('a')['href']
        entry['duplicate_url'] = dupurl

    # Solutions
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

    # Sort Solutions
    entry['solutions'].sort(key=lambda i: i['id'])

    return entry


def savejson(d):
    status = d['status']
    if status.startswith('Pendent'):
        status = 'Pendent'
    carpeta = Path(exportpath, status, d['any'], d['mes'])
    carpeta.mkdir(parents=True)
    fpath = carpeta.child('{}.json'.format(d['id']))
    with open(fpath, 'w') as f:
        json.dump(d, f, sort_keys=True, indent=4, separators=(',', ': '))


def main():
    exportpath.rmtree()
    walkweb()

if __name__ == '__main__':
    main()
