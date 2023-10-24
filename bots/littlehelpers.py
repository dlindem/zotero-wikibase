from bots import xwbi
from bots import botconfig
import requests, time, re

def check_prop_id(propstring):
    if propstring == "False" or propstring == "X":
        return False
    if re.search(r'^P[0-9]+$',propstring):
        return propstring
    return None

def build_depconfig(configdata):


    wikibase_url = configdata['mapping']['wikibase_url']
    configdata['mapping']['wikibase_site'] = re.sub(r'https?://', '', wikibase_url)
    configdata['mapping']['wikibase_entity_ns'] = wikibase_url + "/entity/"
    configdata['mapping']['wikibase_api_url'] = wikibase_url + "/w/api.php"
    configdata['mapping']['wikibase_sparql_endpoint'] = wikibase_url + "/query/sparql"
    configdata['mapping']['wikibase_rest_url'] = wikibase_url + "/w/rest.php"
    configdata['mapping']['wikibase_index_url'] = wikibase_url + "/w/index.php'"
    configdata['mapping']['wikibase_sparql_prefixes'] = ('\n').join([
        "PREFIX xwb: <" + wikibase_url + "/entity/>",
        "PREFIX xdp: <" + wikibase_url + "/prop/direct/>",
        "PREFIX xp: <" + wikibase_url + "/prop/>",
        "PREFIX xps: <" + wikibase_url + "/prop/statement/>",
        "PREFIX xpq: <" + wikibase_url + "/prop/qualifier/>",
        "PREFIX xpr: <" + wikibase_url + "/prop/reference/>",
        "PREFIX xno: <" + wikibase_url + "/prop/novalue/>"
    ])+'\n'

    return configdata

def rewrite_properties_mapping():
    properties = botconfig.load_mapping('properties')
    config = botconfig.load_mapping('config')

    query = """select ?order ?prop ?propLabel ?datatype ?wikidata_prop ?formatter_url ?formatter_uri (group_concat(str(?equiv)) as ?equivs)
    
    where {
      ?prop rdf:type <http://wikiba.se/ontology#Property> ;
             wikibase:propertyType ?dtype ;
             rdfs:label ?propLabel . filter (lang(?propLabel)="en")
             bind (strafter(str(?dtype),"http://wikiba.se/ontology#") as ?datatype)
      OPTIONAL {?prop xdp:""" + config['mapping']['prop_wikidata_entity']['wikibase'] + """ ?wikidata_prop.}
      OPTIONAL {?prop xdp:""" + config['mapping']['prop_formatterurl']['wikibase'] + """ ?formatter_url.}
      OPTIONAL {?prop xdp:""" + config['mapping']['prop_formatterurirdf']['wikibase'] + """ ?formatter_uri.}
      OPTIONAL {?prop xdp:""" + config['mapping']['prop_equivalentprop']['wikibase'] + """ ?equiv.}
      
        BIND (xsd:integer(strafter(str(?prop), "https://monumenta.wikibase.cloud/entity/P")) as ?order )
    } group by ?order ?prop ?propLabel ?datatype ?wikidata_prop ?formatter_url ?formatter_uri ?equivs order by ?order"""

    print("Waiting for SPARQL...")
    bindings = xwbi.wbi_helpers.execute_sparql_query(query=query, prefix=config['mapping']['wikibase_sparql_prefixes'])['results']['bindings']
    print('Found ' + str(len(bindings)) + ' results to process.\n')
    count = 0
    for item in bindings:
        prop_nr = item['prop']['value'].replace(config['mapping']['wikibase_entity_ns'], "")
        properties['mapping'][prop_nr] = {
            'enlabel': item['propLabel']['value'],
            'type': item['datatype']['value'],
            'wdprop': item['wikidata_prop']['value'] if 'wikidata_prop' in item else None
        }
        if 'formatter_url' in item:
            properties['mapping'][prop_nr]['formatter_url'] = item['formatter_url']['value']
        if 'formatter_uri' in item:
            properties['mapping'][prop_nr]['formatter_uri'] = item['formatter_uri']['value']
        if 'equivs' in item:
            properties['mapping'][prop_nr]['equivalents'] = item['equivs']['value'].split(' ')

    botconfig.dump_mapping(properties)

    print('\nSuccessfully stored properties mapping.')


def import_wikidata_entity(wdid, wbid=False, process_claims=True, classqid=None, entitytype="Item"):
    config = botconfig.load_mapping('config')

    print('Will get ' + wdid + ' from wikidata...')
    apiurl = 'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=' + wdid + '&format=json'
    # print(apiurl)
    wdjsonsource = requests.get(url=apiurl)
    if wdid in wdjsonsource.json()['entities']:
        importentityjson = wdjsonsource.json()['entities'][wdid]
    else:
        print('Error: Received no valid item JSON from Wikidata.')
        return False

    wbentityjson = {'labels': [], 'aliases': [], 'descriptions': [],
                  'statements': [{'prop_nr': config['mapping']['prop_wikidata_entity']['wikibase'], 'type': 'ExternalId', 'value': wdid}]}
    if classqid:
        wbentityjson['statements'].append({'prop_nr': config['mapping']['prop_instanceof']['wikibase'], 'type': 'Item', 'value': classqid})
    if 'datatype' in importentityjson: # this is true for properties
        newprop_datatype = importentityjson['datatype']
    else:
        newprop_datatype = None
    # process labels
    for lang in importentityjson['labels']:
        if lang in config['mapping']['wikibase_label_languages']:
            wbentityjson['labels'].append({'lang': lang, 'value': importentityjson['labels'][lang]['value']})
    # process aliases
    for lang in importentityjson['aliases']:
        if lang in config['mapping']['wikibase_label_languages']:
            for entry in importentityjson['aliases'][lang]:
                wbentityjson['aliases'].append({'lang': lang, 'value': entry['value']})
    # process descriptions
    for lang in importentityjson['descriptions']:
        if lang in config['mapping']['wikibase_label_languages']:
            wbentityjson['descriptions'].append({'lang': lang, 'value': importentityjson['descriptions'][lang]['value']})

    # process claims
    # if process_claims:
    #     for claimprop in importentityjson['claims']:
    #         if claimprop in propwd2wb:  # aligned prop
    #             wbprop = propwd2wb[claimprop]
    #             for claim in importentityjson['claims'][claimprop]:
    #                 claimval = claim['mainsnak']['datavalue']['value']
    #                 if propwbdatatype[wbprop] == "WikibaseItem":
    #                     if claimval['id'] not in itemwd2wb:
    #                         print(
    #                             'Will create a new item for ' + claimprop + ' (' + wbprop + ') object property value: ' +
    #                             claimval['id'])
    #                         targetqid = importitem(claimval['id'], process_claims=False)
    #                     else:
    #                         targetqid = itemwd2wb[claimval['id']]
    #                         print('Will re-use existing item as property value: wd:' + claimval[
    #                             'id'] + ' > eusterm:' + targetqid)
    #                     statement = {'prop_nr': wbprop, 'type': 'Item', 'value': targetqid}
    #                 else:
    #                     statement = {'prop_nr': wbprop, 'type': propwbdatatype[wbprop], 'value': claimval,
    #                                  'action': 'keep'}
    #                 statement['references'] = [{'prop_nr': 'P1', 'type': 'externalid', 'value': wdid}]
    #             wbentityjson['statements'].append(statement)
    # process sitelinks
    # if 'sitelinks' in importentityjson:
    # 	for site in importentityjson['sitelinks']:
    # 		if site.replace('wiki', '') in config.label_languages:
    # 			wpurl = "https://"+site.replace('wiki', '')+".wikipedia.org/wiki/"+importentityjson['sitelinks'][site]['title']
    # 			print(wpurl)
    # 			wbentityjson['statements'].append({'prop_nr':'P7','type':'url','value':wpurl})

    wbentityjson['qid'] = wbid  # if False, then create new item
    if wdid.startswith("Q"):
        result = xwbi.itemwrite(wbentityjson)
    elif wdid.startswith("P"):
        result = xwbi.itemwrite(wbentityjson, entitytype="Property", datatype=newprop_datatype)
    # if result and result not in itemwb2wd:
    #     itemwb2wd[result] = wdid
    #     itemwd2wb[wdid] = result
    #     write_wdmapping(wdqid=wdid, wbqid=result)
    return result

def write_property(prop_object):
    while True:
        try:
            print('Writing to xwb wikibase...')
            r = prop_object.write(is_bot=1, clear=False)
            print('Successfully written data to item: ' + prop_object.id)
            return prop_object.id
        except Exception:
            ex = traceback.format_exc()
            print(ex)
            print("Will retry to write to Wikibase...")
            time.sleep(2)