import xml.dom.minidom
from xml.etree import ElementTree
from pyalex import Works as AlexWorks
import re, os, sys, time, json
from datetime import datetime
import lxml
from bs4 import BeautifulSoup
from bots import botconfig, xwbi

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

def get_openalex(bibentry=None):

    title = None
    bibsurnames = []
    results = {}

    for element in bibentry.iter():

        bibtitle = None
        if element.tag == "{http://www.tei-c.org/ns/1.0}title" and 'type' in element.attrib and element.text:
            if element.attrib['type'] == "main":
                bibtitle = re.sub(r'  +', ' ', re.sub(r'[^\w ]', ' ', re.sub(r'\-', ' ', element.text)))
        if element.tag == "{http://www.tei-c.org/ns/1.0}surname":
            bibsurnames.append(element.text)
        if element.tag == "{http://www.tei-c.org/ns/1.0}date":
            bibdate = element.attrib['when']
    if not bibtitle: # try without attrib['type']=="main"
        for element in bibentry.iter():
            if not bibtitle and element.tag == "{http://www.tei-c.org/ns/1.0}title" and element.text:
                bibtitle = re.sub(r'  +',' ',re.sub(r'[^\w ]', ' ',re.sub(r'\-',' ', element.text)))
        print(f"\nSearching OpenAlex for... {bibtitle}")
        # results = sch.search_paper(title)
    if not bibtitle:
        results = {}
    else:
        alex = AlexWorks().search_filter(title=bibtitle).get()
        for result in alex:
            alex_id = result['id'].replace('https://openalex.org/','')
            doi = result['doi']
            alexauthors = []
            for authorship in result['authorships']:
                if 'raw_author_name' in authorship:
                    alexauthors.append(authorship['raw_author_name'])
            print(str(result))
            # print(str(alexauthors))
            results[alex_id] = {'doi':doi, 'alextitle': result['title'], 'alexpubyear': result['publication_year'], 'alexauthors': alexauthors}
    # print(f"bibsurnames {bibsurnames}")

    return {'bibsurnames':bibsurnames, 'bibtitle': bibtitle, 'bibdate':bibdate, 'results':results}

def get_biblstruct(citations={}, doc_qid=None):
    if doc_qid not in citations:
        listbibl = get_listbibl(doc_qid)
        citations['mapping'][doc_qid] = {}
        for bibentry in listbibl:
            bibentrybytes = ElementTree.tostring(bibentry)
            soup = BeautifulSoup(bibentrybytes, features="lxml")
            soup = re.sub(r'\n', '', ' '.join(soup.find_all(text=True)).replace('  ', ' '))
            citations['mapping'][doc_qid][bibentry.attrib['{http://www.w3.org/XML/1998/namespace}id']] = {
                'biblStruct': bibentrybytes.decode('utf-8'), 'biblSoup':soup, 'status':'unvalidated', 'grobid_timestamp':bibentry.attrib['grobid_timestamp']}
        return citations

def get_xml(str):
    return ElementTree.ElementTree(ElementTree.fromstring(str))

def lotu_alex(alex_results={}, target_doi=None, target_alexid=None, target_qid=False, source_doc=None, target_wikidata=None):
    # TODO Wikibase check
    # TODO Wikidata check
    configdata = botconfig.load_mapping('config')['mapping']
    target_data = alex_results['results'][target_alexid]
    print(f"Will write this openalex data to new item: {target_data}...")
    statements = [{'type':'item', 'prop_nr':configdata['prop_instanceof']['wikibase'], 'value':configdata['class_bibitem']['wikibase']},
                  {'type':'externalid', 'prop_nr':'P66', 'value':target_alexid}]
    if target_wikidata:
        statements.append({'type':'externalid', 'prop_nr':configdata['prop_wikidata_entity']['wikibase'], 'value':target_wikidata})
    if target_doi:
        statements.append({'type':'externalid', 'prop_nr':configdata['prop_DOI']['wikibase'], 'value':target_doi})
    target_qid = xwbi.itemwrite({'qid': target_qid, 'labels':[{'lang':'eu', 'value':target_data['alextitle']}],
                                 'statements':statements})
    references = [{'type':'externalid', 'prop_nr':'P68', 'value':f"{source_doc}.tei.xml"},
                  {'type':'string', 'prop_nr':'P67', 'value':f"openalex_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}]
    xwbi.itemwrite({'qid':source_doc, 'statements':[{'type':'item', 'prop_nr':'62', 'value':target_qid, 'references':references}]})

    return target_qid
