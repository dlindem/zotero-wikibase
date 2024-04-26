import xml.dom.minidom
from xml.etree import ElementTree
from pyalex import Works as AlexWorks
import re, os, sys, time, json
from datetime import datetime
import lxml
from bs4 import BeautifulSoup
from bots import botconfig, xwbi
import requests

def get_listbibl(doc_qid=None):
    tei_file = f"/media/david/FATdisk/GROBID/{doc_qid}.tei.xml"
    timestamp = datetime.utcfromtimestamp(os.path.getmtime(tei_file)).strftime(
        '%Y-%m-%d')
    tree = ElementTree.parse(tei_file)
    root = tree.getroot()
    for element in root.iter():

        if element.tag == "{http://www.tei-c.org/ns/1.0}listBibl":
            print(element.tag)
            listbibl = element.findall('{http://www.tei-c.org/ns/1.0}biblStruct')
            for element in listbibl:
                element.set('grobid_timestamp', timestamp)
            return listbibl

def get_strings_from_bibentry(bibentry=None):
    bibnames = []
    bibtitle = None
    bibdate = None
    for element in bibentry.iter():
        bibtitle = None
        if element.tag == "{http://www.tei-c.org/ns/1.0}title" and 'type' in element.attrib and element.text:
            if element.attrib['type'] == "main":
                bibtitle = re.sub(r'  +', ' ', re.sub(r'[^\w ]', ' ', re.sub(r'\-', ' ', element.text)))
        if element.tag == "{http://www.tei-c.org/ns/1.0}surname":
            bibnames.append(element.text)
        if element.tag == "{http://www.tei-c.org/ns/1.0}date":
            bibdate = element.attrib['when']
    if not bibtitle:  # try without attrib['type']=="main"
        for element in bibentry.iter():
            if not bibtitle and element.tag == "{http://www.tei-c.org/ns/1.0}title" and element.text:
                bibtitle = re.sub(r'  +', ' ', re.sub(r'[^\w ]', ' ', re.sub(r'\-', ' ', element.text)))
    if not bibtitle:
        bibtitle = get_soup(bibentry=bibentry)
    return {'bibtitle': bibtitle, 'bibdate':bibdate, 'bibnames':bibnames}

def get_openalex(bibentry=None, bibtitle=None, search_string=None):
    results = {}
    if bibentry:
        stringdict = get_strings_from_bibentry(bibentry=bibentry)
        bibtitle = stringdict['bibtitle']
        if bibtitle and not search_string:
            search_string = bibtitle
        print(f"\nSearching OpenAlex for... {search_string}")
    if bibtitle:
        alex = AlexWorks().search_filter(title=search_string).get()
        for result in alex:
            alex_id = result['id'].replace('https://openalex.org/','')
            doi = result['doi']
            alexauthors = []
            for authorship in result['authorships']:
                if 'raw_author_name' in authorship:
                    alexauthors.append(authorship['raw_author_name'])
            print(str(result))
            # print(str(alexauthors))
            results[alex_id] = {'complete_result':str(result)[0:2000], 'doi':doi, 'result_title': result['title'], 'result_pubyear': result['publication_year'], 'result_authors': alexauthors}
    return {'bibnames':stringdict['bibnames'], 'bibtitle':bibtitle, 'bibdate':stringdict['bibdate'], 'results':results, 'search_string':search_string}

def get_googlebooks(bibentry=None, bibtitle=None, bibnames=[], search_string=None):
    if bibentry:
        stringdict = get_strings_from_bibentry(bibentry=bibentry)
        bibtitle = stringdict['bibtitle']
        bibnames = stringdict['bibnames']
        bibdate = stringdict['bibdate']

        if bibtitle and not search_string:
            search_string = f"intitle:{bibtitle}"
        print(f"\nSearching GoogleBooks for... {search_string}")
        resp = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={search_string}")
        print(f"Google answers: {resp.status_code}")
        #print(str(resp.json()))
        if resp.status_code == 200:
            resultlist = resp.json()['items'][:30]
        else:
            resultlist = []
    results = {}
    for item in resultlist:
        result = {}
        result['result_id'] = item['id']
        result['result_title'] = item['volumeInfo']['title']
        result['result_authors'] = item['volumeInfo']['authors']
        result['result_pubyear'] = item['volumeInfo']['publishedDate'][0:4]
        for id in item['volumeInfo']['industryIdentifiers']:
            if id['type'] == 'ISBN10':
                result['result_isbn10'] = id['identifier']
            if id['type'] == 'ISBN13':
                result['result_isbn13'] = id['identifier']
        result['complete_result'] = str(item)[0:2000]
        results[item['id']] = result



    return {'bibnames': bibnames, 'bibtitle': bibtitle, 'bibdate': bibdate,
            'results': results, 'search_string':search_string}

def get_biblstruct(citations={}, doc_qid=None):
    if doc_qid not in citations:
        listbibl = get_listbibl(doc_qid)
        citations['mapping'][doc_qid] = {}
        for bibentry in listbibl:
            soup = get_soup(bibentry=bibentry)
            citations['mapping'][doc_qid][bibentry.attrib['{http://www.w3.org/XML/1998/namespace}id']] = {
                'biblStruct': ElementTree.tostring(bibentry).decode('utf-8'), 'biblSoup':soup, 'status':'unvalidated', 'grobid_timestamp':bibentry.attrib['grobid_timestamp']}
        return citations

def get_xml(str):
    return ElementTree.ElementTree(ElementTree.fromstring(str))

def get_soup(bibentry=None):
    bibentrybytes = ElementTree.tostring(bibentry)
    soup = BeautifulSoup(bibentrybytes, features="lxml")
    soup = re.sub(r'  +',' ', re.sub(r'\n', '', ' '.join(soup.find_all(text=True)))).strip()
    return soup

def lotu_zitazioa(results={}, target_doi=None, target_alexid=None, target_gbid=None, target_qid=False, source_doc=None, target_wikidata=None):
    # TODO Wikibase check https://wikibase.inguma.eus/wiki/Special:ApiSandbox#action=query&format=json&list=search&srsearch=Euskara%20Alemana&srnamespace=120&srlimit=20&srinfo=&srprop=titlesnippet%7Csnippet%7Cextensiondata%7Ccategorysnippet%7Csectionsnippet%7Csectiontitle
    # TODO Wikidata check
    configdata = botconfig.load_mapping('config')['mapping']
    if target_alexid:
        target_data = results['results'][target_alexid]
        print(f"Will write this openalex data to new item: {target_data}...")
    elif target_gbid:
        target_data = results['results'][target_gbid]
        print(f"Will write this google books data to new item: {target_data}...")
    statements = [{'type':'item', 'prop_nr':configdata['prop_instanceof']['wikibase'], 'value':configdata['class_bibitem']['wikibase']}]
    if target_alexid:
        statements.append({'type':'externalid', 'prop_nr':'P66', 'value':target_alexid})
    if target_gbid:
        statements.append({'type':'externalid', 'prop_nr':'P66', 'value':target_gbid})
    if target_wikidata:
        statements.append({'type':'externalid', 'prop_nr':configdata['prop_wikidata_entity']['wikibase'], 'value':target_wikidata})
    if target_doi:
        statements.append({'type':'externalid', 'prop_nr':configdata['prop_DOI']['wikibase'], 'value':target_doi})
    target_qid = xwbi.itemwrite({'qid': target_qid, 'labels':[{'lang':'eu', 'value':target_data['result_title']}],
                                 'statements':statements})
    references = [{'type':'externalid', 'prop_nr':'P68', 'value':f"{source_doc}.tei.xml"},
                  {'type':'string', 'prop_nr':'P67', 'value':f"openalex_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}]
    xwbi.itemwrite({'qid':source_doc, 'statements':[{'type':'item', 'prop_nr':'62', 'value':target_qid, 'references':references}]})

    return target_qid
