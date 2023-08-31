from bots import xwbi
from bots import config
import requests

def rewrite_properties_mapping():
    properties = config.load_mapping('properties')

    query = """select ?order ?prop ?propLabel ?datatype ?wikidata_prop ?formatter_url ?formatter_uri
    
    where {
      ?prop rdf:type <http://wikiba.se/ontology#Property> ;
             wikibase:propertyType ?dtype ;
             rdfs:label ?propLabel . filter (lang(?propLabel)="en")
             bind (strafter(str(?dtype),"http://wikiba.se/ontology#") as ?datatype)
      OPTIONAL {?prop xdp:""" + config.prop_wikidata_entity + """ ?wikidata_prop.}
      OPTIONAL {?prop xdp:""" + config.prop_formatterurl + """ ?formatter_url.}
      OPTIONAL {?prop xdp:""" + config.prop_formatterurirdf + """ ?formatter_uri.}
        BIND (xsd:integer(strafter(str(?prop), "https://monumenta.wikibase.cloud/entity/P")) as ?order )
    } group by ?order ?prop ?propLabel ?datatype ?wikidata_prop ?formatter_url ?formatter_uri order by ?order"""

    print("Waiting for SPARQL...")
    bindings = xwbi.wbi_helpers.execute_sparql_query(query=query, prefix=config.sparql_prefixes)['results']['bindings']
    print('Found ' + str(len(bindings)) + ' results to process.\n')
    count = 0
    for item in bindings:
        prop_nr = item['prop']['value'].replace(config.entity_ns, "")
        properties['mapping'][prop_nr] = {
            'enlabel': item['propLabel']['value'],
            'type': item['datatype']['value'],
            'wdprop': item['wikidata_prop']['value'] if 'wikidata_prop' in item else None
        }
        if 'formatter_url' in item:
            properties['mapping'][prop_nr]['formatter_url'] = item['formatter_url']['value']
        if 'formatter_uri' in item:
            properties['mapping'][prop_nr]['formatter_uri'] = item['formatter_uri']['value']

    config.dump_mapping(properties)

    print('\nSuccessfully stored properties mapping.')

def import_wikidata_entity(wdid, wbid=False, process_claims=True, classqid=None):
    
    print('Will get ' + wdid + ' from wikidata...')
    apiurl = 'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=' + wdid + '&format=json'
    # print(apiurl)
    wdjsonsource = requests.get(url=apiurl)
    if wdid in wdjsonsource.json()['entities']:
        importitemjson = wdjsonsource.json()['entities'][wdid]
    else:
        print('Error: Received no valid item JSON from Wikidata.')
        return False
        
    wbitemjson = {'labels': [], 'aliases': [], 'descriptions': [],
                  'statements': [{'prop_nr': config.prop_wikidata_entity, 'type': 'ExternalId', 'value': wdid}]}
    if classqid:
        wbitemjson['statements'].append({'prop_nr': config.prop_instanceof, 'type': 'Item', 'value': classqid})
        
    # process labels
    for lang in importitemjson['labels']:
        if lang in config.label_languages:
            wbitemjson['labels'].append({'lang': lang, 'value': importitemjson['labels'][lang]['value']})
    # process aliases
    for lang in importitemjson['aliases']:
        if lang in config.label_languages:
            for entry in importitemjson['aliases'][lang]:
                wbitemjson['aliases'].append({'lang': lang, 'value': entry['value']})
    # process descriptions
    for lang in importitemjson['descriptions']:
        if lang in config.label_languages:
            wbitemjson['descriptions'].append({'lang': lang, 'value': importitemjson['descriptions'][lang]['value']})

    # process claims
    # if process_claims:
    #     for claimprop in importitemjson['claims']:
    #         if claimprop in propwd2wb:  # aligned prop
    #             wbprop = propwd2wb[claimprop]
    #             for claim in importitemjson['claims'][claimprop]:
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
    #             wbitemjson['statements'].append(statement)
    # process sitelinks
    # if 'sitelinks' in importitemjson:
    # 	for site in importitemjson['sitelinks']:
    # 		if site.replace('wiki', '') in config.label_languages:
    # 			wpurl = "https://"+site.replace('wiki', '')+".wikipedia.org/wiki/"+importitemjson['sitelinks'][site]['title']
    # 			print(wpurl)
    # 			wbitemjson['statements'].append({'prop_nr':'P7','type':'url','value':wpurl})

    wbitemjson['qid'] = wbid  # if False, then create new item
    result = xwbi.itemwrite(wbitemjson)
    # if result and result not in itemwb2wd:
    #     itemwb2wd[result] = wdid
    #     itemwd2wb[wdid] = result
    #     write_wdmapping(wdqid=wdid, wbqid=result)
    return result