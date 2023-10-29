from bots import xwbi
from bots import botconfig
from bots import zoterobot
import requests, time, re, json, csv
import os, glob, sys, shutil
from pathlib import Path
import pandas

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
        except Exception as ex:
            print(ex)
            print("Will retry to write to Wikibase...")
            time.sleep(2)

def propagate_mapping(zoteromapping={}, fieldtype="", fieldname="", wbprop=""):
    messages=[]
    for itemtype in zoteromapping:
        if fieldname in zoteromapping[itemtype][fieldtype]:
            if zoteromapping[itemtype][fieldtype][fieldname]['wbprop'] != wbprop:
                oldval = zoteromapping[itemtype][fieldtype][fieldname]['wbprop']
                zoteromapping[itemtype][fieldtype][fieldname]['wbprop'] = wbprop
                messages.append(f"Updated {itemtype}-{fieldname} to {wbprop}. Old value was {str(oldval)}.")
    return {'mapping': zoteromapping, 'messages':messages}

def check_config(configdata={}):
    print('Will perform zotero field and creator type mapping for the current zotero export dataset...')
    config_message = []
    status_ok = True
    for mapping in configdata:
        if type(configdata[mapping]) == str:
            if len(configdata[mapping]) == 0:
                status_ok = False
                config_message.append(f"Configuration for '{mapping}' is undefined, you have to fix that.")
        elif type(configdata[mapping]) == list:
            if len(configdata[mapping]) == 0:
                status_ok = False
                config_message.append(f"Configuration for '{mapping}' is undefined, you have to fix that.")
        elif mapping.startswith("prop_") or mapping.startswith("class_"):
            if not configdata[mapping]['wikibase']:
                status_ok = False
                config_message.append(f"Configuration for '{mapping}' is undefined, you have to fix that.")
    if status_ok:
        return {'message': ["Your basic configuration appears to be complete."], 'color': 'color:green'}
    else:
        return {'message': config_message, 'color': 'color:red'}

def check_export(zoterodata=[], zoteromapping={}):
    messages = []
    for item in zoterodata:
        itemtype = item['data']['itemType']
        missing_mapping_message = ' Fix this <a href="./zoterofields/' + itemtype + '" target="_blank">here</a> <small>(or <a href="./zoterofields/all_types">here</a> for all item types at once)</small>'
        # check item type Qid
        if not zoteromapping['mapping'][itemtype]['bibtypeqid']:
            newmsg = 'The "'+itemtype+'" item type has no Wikibase entity defined.'
            messages.append(newmsg+missing_mapping_message)
            print(newmsg)
        # check data fields
        seen_fields = []
        seen_creators = []
        fields_processed_before = ['itemType', 'creators', 'ISBN', 'extra']
        for fieldname in item['data']:
            if item['data'][fieldname] != "" and fieldname not in fields_processed_before and itemtype + fieldname not in seen_fields and fieldname in zoteromapping['mapping'][itemtype]['fields']:
                if zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'] == False:
                    print(f"Skipping {itemtype} > {fieldname} as marked for permanent omission.")
                elif zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop']:
                    print(f"Found existing mapping: {fieldname} > {zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop']}")
                else:
                    newmsg = f"<i>{itemtype}</i> '<b>{fieldname}</b>': No wikibase property defined."
                    messages.append(newmsg+missing_mapping_message)
                    print(newmsg)
            seen_fields.append(itemtype + fieldname)
        # check creator types
        if 'creators' not in item['data']:
            continue
        for creatordict in item['data']['creators']:
            creatortype = creatordict['creatorType']
            if itemtype + creatortype in seen_creators:
                continue
            if zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop'] == False:
                print(f"Skipping {itemtype}>{creatortype} as marked for permanent omission.")
                seen_creators.append(itemtype + creatortype)
                continue
            if zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop']:
                print(f"Will use existing mapping: {creatortype} > {zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop']}")
                seen_creators.append(itemtype + creatortype)
            else:
                newmsg = f"<i>{itemtype}</i> creator type '<b>{fieldname}</b>': No mapping defined."
                messages.append(newmsg+missing_mapping_message)
                print(newmsg)
    if len(messages) == 0:
        messages = ['All datafields containing data in this dataset are mapped to Wikibase properties.']
    return messages

def lookup_doi(doi):
    config = botconfig.load_mapping('config')
    query = 'select * where {bind (UCASE("' + doi + '") as ?doi) ?item wdt:P356 ?doi.}'
    bindings = xwbi.wbi_helpers.execute_sparql_query(query=query, endpoint='https://query.wikidata.org/sparql',
                                                     user_agent=config['mapping']['wikibase_name'] + ' Wikibase user script')['results']['bindings']
    print('Found ' + str(len(bindings)) + ' matching Wikidata items (via DOI) to process.\n')
    if len(bindings) > 1:
        print('This is strange: Found more than one matching Wikidata item for DOI: '+doi)
        time.sleep(3)
        return False
    elif len(bindings) == 1:
        return bindings[0]['item']['value'].replace('http://www.wikidata.org/entity/','')
    else:
        return False

def get_creators(qid=None):
    if not qid:
        return {}
    print(f"Getting existing creator statements for {qid}...")
    config = botconfig.load_mapping('config')
    query = """select ?prop (group_concat(distinct ?listpos;SEPARATOR=",") as ?list)
       
    where {bind (xwb:"""+qid+""" as ?item)
      ?prop xdp:"""+config['mapping']['prop_instanceof']['wikibase']+""" xwb:"""+config['mapping']['class_creator_role']['wikibase']+""" .      
      ?prop wikibase:claim ?prop_cl .
      ?item ?prop_cl [xpq:"""+config['mapping']['prop_series_ordinal']['wikibase']+""" ?listpos].
    } group by ?prop ?list
    """
    creators = {}
    bindings = xwbi.wbi_helpers.execute_sparql_query(query=query, prefix=config['mapping']['wikibase_sparql_prefixes'])['results']['bindings']
    print('Found ' + str(len(bindings)) + ' creator roles on the existing wikibase item to process.\n')
    for item in bindings:
        creatorprop = item['prop']['value'].replace(config['mapping']['wikibase_entity_ns'],'')
        creators[creatorprop] = item['list']['value'].split(',')
    return creators

def wikibase_upload(data=[]):
    # iterate through zotero records and do wikibase upload
    config = botconfig.load_mapping('config')
    iso3mapping = botconfig.load_mapping('iso-639-3')
    iso1mapping = botconfig.load_mapping('iso-639-1')
    zoteromapping = botconfig.load_mapping('zotero')
    language_literals = botconfig.load_mapping('language-literals')
    messages = []
    msgcolor = 'background:limegreen'
    datalen = len(data)
    count = 0
    print('\nWill now upload the currently loaded dataset to Wikibase...')
    for item in data:
        count += 1
        print(f"\n[{str(count)}] Now processing item '{item['links']['alternate']['href']}'...")
        qid = item['wikibase_entity'] # is False if zotero getexport function has not found a Wikibase Qid in 'extra'
        # instance of and bibItem type
        itemtype = item['data']['itemType']
        statements = [
            {'type': 'WikibaseItem', 'prop_nr': config['mapping']['prop_instanceof']['wikibase'],
             'value': config['mapping']['class_bibitem']['wikibase']},
             {'type': 'WikibaseItem', 'prop_nr': config['mapping']['prop_itemtype']['wikibase'],
              'value': zoteromapping['mapping'][itemtype]['bibtypeqid']}
        ]
        # fields with special meaning / special procedure
        ## Zotero ID and Fulltext PDF attachment(s)
        attqualis = []
        if item['meta']['numChildren'] > 0:
            children = zoterobot.getchildren(item['data']['key'])
            for child in children:
                if 'contentType' not in child['data']:  # these are notes attachments
                    continue
                if child['data']['contentType'] == "application/pdf":
                    attqualis.append(
                        {'prop_nr': config['mapping']['prop_zotero_PDF']['wikibase'], 'type': 'ExternalId',
                         'value': child['data']['key']})
                if child['data']['contentType'] == "" and child['data']['url'].startswith(config['mapping']['wikibase_entity_ns']):
                    qid = child['data']['url'].replace(config['mapping']['wikibase_entity_ns'], "")
                    print('Found link attachment: This item is linked to ' + config['mapping']['wikibase_entity_ns'] + qid)
        else:
            children = []
        statements.append({'prop_nr': config['mapping']['prop_zotero_item']['wikibase'], 'type': 'ExternalId',
                           'value': item['data']['key'],
                           'qualifiers': attqualis})

        ## archiveLocation (special for items stemming from LexBib) TODO - delete for generic tool
        if 'archiveLocation' in item['data']:
            if item['data']['archiveLocation'].startswith('https://lexbib.elex.is/entity/'):
                statements.append({'type': 'externalid', 'prop_nr': 'P10',
                                   'value': item['data']['archiveLocation'].replace("https://lexbib.elex.is/entity/", "")})
            if item['data']['archiveLocation'].startswith('http://lexbib.elex.is/entity/'):
                statements.append({'type': 'externalid', 'prop_nr': 'P10',
                                   'value': item['data']['archiveLocation'].replace("http://lexbib.elex.is/entity/", "")})
            item['data']['archiveLocation'] = ""

        ## title to labels
        if 'title' in item['data']:
            labels = []
            for lang in config['mapping']['wikibase_label_languages']:
                labels.append({'lang': lang, 'value': item['data']['title']})

        ## language
        if 'language' in item['data']:
            languageqid = False
            if len(item['data']['language']) == 2:  # should be a ISO-639-1 code
                if item['data']['language'].lower() in iso1mapping['mapping']:
                    item['data']['language'] = iso1mapping['mapping'][item['data']['language'].lower()]
                    languageqid = iso3mapping['mapping'][item['data']['language']]['wbqid']
                    print('Language field: Found two-digit language code, mapped to ' +
                          iso3mapping['mapping'][item['data']['language'].lower()]['enlabel'], languageqid)
            elif len(item['data']['language']) == 3:  # should be a ISO-639-3 code
                if item['data']['language'].lower() in iso3mapping['mapping']:
                    languageqid = iso3mapping['mapping'][item['data']['language'].lower()]['wbqid']
                    print('Language field: Found three-digit language code, mapped to ' +
                          iso3mapping['mapping'][item['data']['language'].lower()]['enlabel'], languageqid)
            if languageqid == False:  # Can't identify language using ISO 639-1 or 639-3
                if item['data']['language'] in language_literals['mapping']:
                    languageqid = iso3mapping['mapping'][language_literals['mapping'][item['data']['language']]]['wbqid']
                    print('Language field: Found stored language literal, mapped to ' +
                          iso3mapping['mapping'][language_literals['mapping'][item['data']['language']]]['enlabel'])
                elif len(item['data']['language']) > 1:  # if there is a string that could be useful
                    print(f"Could not match the field content '{item['data']['language']}' to any language.")
                    choice = None
                    choices = ["0", "1"]
                    while choice not in choices:
                        choice = input(
                            f"Do you want to store '{item['data']['language']}' and associate that string to a language? '1' for yes, '0' for no.")
                    if choice == "1":
                        iso3 = None
                        while iso3 not in iso3mapping['mapping']:
                            iso3 = input(
                                f"Provide the ISO-639-3 three-letter code you want to associate to '{item['data']['language']}':")
                        languageqid = iso3mapping['mapping'][iso3]['wbqid']
            if languageqid == None:  # Language item is still not on the wikibase (got 'None' from iso3mapping)
                languagewdqid = iso3mapping['mapping'][item['data']['language']]['wdqid']
                print(
                    f"No item defined for this language on your Wikibase. This language is {languagewdqid} on Wikidata. I'll import that and use it from now on.")
                languageqid = zotwb_functions.import_wikidata_entity(languagewdqid,
                                                                   classqid=config['mapping']['class_language']['wikibase'])
                iso3mapping['mapping'][item['data']['language']]['wbqid'] = languageqid
                botconfig.dump_mapping(iso3mapping)
            if languageqid and config['mapping']['prop_language']['wikibase']:
                statements.append(
                    {'prop_nr': config['mapping']['prop_language']['wikibase'], 'type': 'WikibaseItem',
                     'value': languageqid})

        ## date (write parsedDate not date to prop foreseen for date in this itemtype)
        pubyear = ""
        if 'parsedDate' in item['meta'] and zoteromapping['mapping'][itemtype]['fields']['date']['wbprop']:
            year_regex = re.search(r'^[0-9]{4}', item['meta']['parsedDate'])
            month_regex = re.search(r'^[0-9]{4}\-([0-9]{2})', item['meta']['parsedDate'])
            day_regex = re.search(r'^[0-9]{4}\-[0-9]{2}\-([0-9]{2})', item['meta']['parsedDate'])

            if year_regex:
                pubyear = year_regex.group(0)
                timestr = f"+{pubyear}"
                precision = 9
                if month_regex:
                    timestr += f"-{month_regex.group(1)}"
                    precision = 10
                else:
                    timestr += "-01"
                if day_regex:
                    timestr += f"-{day_regex.group(1)}T00:00:00Z"
                    precision = 11
                else:
                    timestr += "-01T00:00:00Z"
                statements.append(
                    {'prop_nr': zoteromapping['mapping'][itemtype]['fields']['date']['wbprop'], 'type': 'Time',
                     'value': timestr, 'precision': precision})

        ## DOI
        if 'DOI' in item['data']:
            # normalize DOI
            regex = re.search(r'(10\.\d{4,}[^&]+)', item['data']['DOI'])
            if not regex:
                print('Could not get DOI by regex from DOI field content: '+item['data']['DOI'])
            else:
                doi = regex.group(1)
                print('Found DOI')
                # lookup DOI on WD
                wdqid = lookup_doi(doi)
                if wdqid:
                    print(f"DOI matching Wikidata item {wdqid}.")
                    statements.append(
                        {"prop_nr": config['mapping']['prop_wikidata_entity']['wikibase'], "type": "ExternalId",
                         "value": wdqid})
                if zoteromapping['mapping'][itemtype]['fields']['DOI']['wbprop']:
                    statements.append(
                        {"prop_nr": zoteromapping['mapping'][itemtype]['fields']['DOI']['wbprop'], "type": "ExternalId",
                         "value": doi})
                        
        ## ISBN
        if 'ISBN' in item['data']:
            val = item['data']['ISBN'].replace("-", "")  # normalize ISBN
            valsearch = re.search(r'^\d+', val)  # only take the first block of digits (i.e., only the first ISBN listed)
            if valsearch:
                val = valsearch.group(0)
                if len(val) == 10:
                    statements.append(
                        {"prop_nr": config['mapping']['prop_isbn_10']['wikibase'], "type": "ExternalId", "value": val})
                elif len(val) == 13:
                    statements.append(
                        {"prop_nr": config['mapping']['prop_isbn_13']['wikibase'], "type": "ExternalId", "value": val})
                else:
                    print('Could not process ISBN field content: ' + item['data']['ISBN'])

        ## normalize ISSN (writing is in main field iteration below)
        if 'ISSN' in item['data']:
            if "-" not in item['data']['ISSN']:  # normalize ISSN, remove any secondary ISSN
                item['data']['ISSN'] = item['data']['ISSN'][0:4] + "-" + item['data']['ISSN'][4:9]
            else:
                item['data']['ISSN'] = item['data']['ISSN'][:9]

        ## Identifiers in EXTRA field
        if 'extra' in item['data']:
            # Qid of the Wikibase to use
            if config['mapping']['store_qid_in_extra'] and qid == False:  # if user has specified that Qid should be stored in EXTRA field (and it has not been found in a link attachment)
                qid_regex = re.search(config['mapping']['wikibase_entity_ns'] + r"(Q[0-9]+)", item['data']['extra'])
                if qid_regex:
                    qid = qid_regex.group(1)
                    print('This BibItem already exists on the wikibase as ' + qid)
                else:
                    qid = False  # a new BibItem will be created on the Wikibase
                    print('This BibItem still does not exist on the wikibase')
            # user-defined identifier patterns
            for pattern in config['mapping']['identifier_patterns']:
                try:
                    identifier_regex = re.search(rf"{pattern}", item['data']['extra'])
                    if identifier_regex:
                        print(f"Extra field: Found identifier {identifier_regex.group(0)}")
                        identifier = identifier_regex.group(1)
                        identifier_prop = config['mapping']['identifier_patterns'][pattern]
                        statements.append({'type': 'ExternalId', 'prop_nr': identifier_prop, 'value': identifier})
                except Exception as ex:
                    print(f"Failed to do EXTRA identifier regex extraction: {str(ex)}")
                    print(f"Extra field content was: {item['data']['extra']}")

        ## special operations with Zotero tags, use-case specific
        if 'tags' in item['data']:
            for tag in item['data']['tags']:
                if tag["tag"].startswith(':type '):
                    type = tag["tag"].replace(":type ", "")
                    if type == "DictionaryDistribution":
                        statements.append({"prop_nr": "P5", "type": "item", "value": "Q12"})  # LCR distribution

        # creators
        existing_creators = get_creators(qid=qid)
        listpos = {}
        for creator in item['data']['creators']:
            if creator['creatorType'] not in listpos:
                listpos[creator['creatorType']] = 1
            else:
                listpos[creator['creatorType']] += 1
            if zoteromapping['mapping'][itemtype]['creatorTypes'][creator['creatorType']]['wbprop']:
                creatorprop = zoteromapping['mapping'][itemtype]['creatorTypes'][creator['creatorType']]['wbprop']
                if creatorprop in existing_creators:
                    if str(listpos[creator['creatorType']]) in existing_creators[creatorprop]:
                        print(f"{creator['creatorType']} ({creatorprop}) with listpos {str(listpos[creator['creatorType']])} is already present - Delete it manually on the Wikibase if you want to overwrite it.")
                        continue # do not process this creator

                # if "non-dropping-particle" in creator:
                #     creator["family"] = creator["non-dropping-particle"] + " " + creator["family"]
                # if creator["family"] == "Various":
                #     creator["given"] = "Various"
                ### TODO: non dropping particles / middle names

                creatorqualis = [{"prop_nr": config['mapping']['prop_series_ordinal']['wikibase'], "type": "string",
                                  "value": str(listpos[creator['creatorType']])}]
                if 'name' in creator:
                    creatorqualis.append(
                        {"prop_nr": config['mapping']['prop_source_literal']['wikibase'], "type": "string",
                         "value": creator['name']})
                elif 'firstName' in creator:
                    if creator['firstName'] != "":
                        creatorqualis += [
                            {"prop_nr": config['mapping']['prop_source_literal']['wikibase'], "type": "string",
                             "value": creator["firstName"] + " " + creator["lastName"]},
                            {"prop_nr": config['mapping']['prop_given_name_source_literal']['wikibase'], "type": "string",
                             "value": creator["firstName"]},
                            {"prop_nr": config['mapping']['prop_family_name_source_literal']['wikibase'], "type": "string",
                             "value": creator["lastName"]}]
                    else:
                        creatorqualis.append(
                            {"prop_nr": config['mapping']['prop_source_literal']['wikibase'], "type": "string",
                             "value": creator["lastName"]})
                else:
                    creatorqualis.append(
                        {"prop_nr": config['mapping']['prop_source_literal']['wikibase'], "type": "string",
                         "value": creator["lastName"]})
                statements.append({
                    "prop_nr": creatorprop,
                    "type": "item",
                    "value": False,  # this produces an "UNKNOWN VALUE" statement
                    "qualifiers": creatorqualis
                })

        # Other fields
        fields_processed_before = ['language', 'creators', 'ISBN', 'extra', 'abstractNote', 'date', 'DOI']
        for fieldname in item['data']:
            if fieldname in fields_processed_before or fieldname not in zoteromapping['mapping'][itemtype]['fields']:
                continue
            if item['data'][fieldname] == "":  # no empty strings
                continue
            if zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop']:
                if zoteromapping['mapping']['all_types']['fields'][fieldname]['dtype'] == "String": # this will just use the Zotero literal as string value
                    statements.append({
                        'prop_nr': zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'],
                        'type': "String",
                        'value': item['data'][fieldname].strip()
                    })
                elif zoteromapping['mapping']['all_types']['fields'][fieldname]['dtype'] == "WikibaseItem": # this will produce an 'unknown value' statement
                    statements.append({
                        'prop_nr': zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'],
                        'type': "WikibaseItem",
                        'value': False,
                        'qualifiers': [{'type': 'String', 'prop_nr': config['mapping']['prop_source_literal']['wikibase'],
                                        'value': item['data'][fieldname].strip()}]
                    })
                # TODO: datatype date fields other than pubdate
        # add description
        descriptions = []
        for lang in config['mapping']['wikibase_label_languages']:
            creatorsummary = item['meta']['creatorSummary'] if 'creatorSummary' in item['meta'] else ""
            descriptions.append({'lang': lang, 'value': f"{creatorsummary} {pubyear}"})

        itemdata = {'qid': qid, 'statements': statements, 'descriptions': descriptions, 'labels': labels}
        # # debug output
        # with open(f"parking/testout_{item['data']['key']}.json", 'w', encoding="utf-8") as file:
        #     json.dump({'zotero': item, 'output': itemdata}, file, indent=2)
        # do upload
        qid = xwbi.itemwrite(itemdata, clear=False)
        if qid:  # if writing was successful (if not, qid is still False)
            patch_attempt = zoterobot.patch_item(qid=qid, zotitem=item, children=children)
            if patch_attempt == "Versioning_Error":
                messages.append(
                    f"Upload to Wikibase successful, but item <a href=\"{item['links']['alternate']['href']}\">{item['key']}</a> has been changed on Zotero since data ingest, and could not be patched. Update Zotero export data ingest.")
                msgcolor = 'background:orangered'
        else:
            messages.append(f"Upload unsuccessful: <a href=\"{item['links']['alternate']['href']}\">{item['key']}</a>.")
            msgcolor = 'background:orangered'
            datalen = datalen-1


    messages.append(f"Successfully uploaded {str(datalen)} of {str(len(data))} items marked with the tag '{config['mapping']['zotero_export_tag']}'. These should now have the tag '{config['mapping']['zotero_on_wikibase_tag']}' instead.")
    print('\n'+str(messages))
    return {'messages': messages, 'msgcolor': msgcolor}

def export_creators():
    print('Starting unreconciled creators export to CSV...')
    config = botconfig.load_mapping('config')
    query = """
    select ?bibItem ?creatorstatement ?propLabel ?listpos ?givenName ?lastName ?fullName 
    (?fullName as ?fullName_clusters) 
    (?fullName as ?fullName_recon_Wikidata)
    (?fullName as ?fullName_recon_Wikibase)
    where {
      ?prop xdp:"""+config['mapping']['prop_instanceof']['wikibase']+""" xwb:"""+config['mapping']['class_creator_role']['wikibase']+""";
            wikibase:directClaim ?prop_d;
            wikibase:claim ?prop_p;
            wikibase:statementProperty ?prop_ps.
        ?bibItem ?prop_p ?creatorstatement .
       ?creatorstatement ?prop_ps ?creatoritem. filter isBLANK(?creatoritem) # only unknown-value-statements
       ?creatorstatement xpq:""" + config['mapping']['prop_series_ordinal']['wikibase'] + """ ?listpos ;
                         xpq:""" + config['mapping']['prop_source_literal']['wikibase'] + """ ?fullName .
     optional {?creatorstatement xpq:""" + config['mapping']['prop_given_name_source_literal']['wikibase'] + """ ?givenName.}
     optional {?creatorstatement xpq:""" + config['mapping']['prop_family_name_source_literal']['wikibase'] + """ ?lastName .}
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
       } order by ?lastName ?givenName"""
    query_result = xwbi.wbi_helpers.execute_sparql_query(query=query, prefix=config['mapping']['wikibase_sparql_prefixes'])
    data = pandas.DataFrame(columns=query_result['head']['vars'])
    for binding in query_result['results']['bindings']:
        pdrow = {}
        for key in binding:
            pdrow[key] = binding[key]['value']
        data.loc[len(data)] = pdrow
        if len(data) == 0:
            message = f"SPARQL Query for unreconciled creator statements returned 0 results."
        else:
            outfilename = f"data/unreconciled_creators/wikibase_creators_{time.strftime('%Y%m%d_%H%M%S', time.localtime())}.csv"
            data.to_csv(outfilename, index=False)
            message = f"Successfully exported {str(len(data))} unreconciled creator statements to '{outfilename}'."
    print(message)
    return [message]

def get_recon_pd(folder=""):
    list_of_files = glob.glob(folder + '/*.csv')  # * means all if need specific format then *.csv
    infile = max(list_of_files, key=os.path.getctime)
    print(f"Will get reconciled data from {infile}...")
    return {'data':pandas.read_csv(infile),'filename':infile}

def import_creators(data=None, infile=None, wikidata=False, wikibase=False, unrecon=False):
    from bots import xwb
    config = botconfig.load_mapping("config")
    messages = []
    # This expects a csv with the following colums:
    # bibItem [bibitem xwb Qid] / creatorstatement / listpos / fullName / Qid [reconciled person item xwb-qid] / givenName / lastName

    origfile = infile.replace('.csv', '.csv.copy')
    if not Path(origfile).is_file():
        shutil.copyfile(infile, origfile)
        messages.append(f"This CSV has not been processed before: Saved backup or original as <code>{origfile}</code>.")
    print('Starting reconciled creator import. This file will be processed: ' + infile)
    time.sleep(2)
    newitemjsonfile = infile.replace(".csv", "_newcreatorslog.json")
    if Path(newitemjsonfile).is_file():
        with open(newitemjsonfile, 'r', encoding='utf-8') as jsonfile:
            newcreators = json.load(jsonfile)
            messages.append('This CSV has been processed before; any new ...')
    else:
        newcreators = {}

    # select subset to process
    df = data
    rest = df.copy()
    if wikidata:
        df = df.dropna(subset=['Wikidata_Qid'])
        jobdesc = f"Wikidata-reconciled creators ({str(len(df))} creator statements)"
    elif not wikidata and wikibase:
        df = df.dropna(subset=['Wikibase_Qid'])
        jobdesc = f"Wikibase-reconciled creators ({str(len(df))} creator statements)"
    elif unrecon:
        df = df[df['Wikidata_Qid'].isnull() & df['Wikidata_Qid'].isnull()]
        jobdesc = f"Unreconciled creators ({str(len(df))} creator statements)"


    wikidatacreators = {}

    for rowindex, row in df.iterrows():
        newitem = False
        creatorwdqid = None
        creatorqid = False
        print('\nItem in CSV row [' + str(rowindex + 2) + ']:')
        bibItem = row['bibItem'].replace(config['mapping']['wikibase_entity_ns'], "")
        print('BibItem is ' + bibItem + '.')
        creatorstatement = re.search(r'statement/(Q.*)', row['creatorstatement']).group(1)
        print('CreatorStatement is ' + creatorstatement + '.')
        if 'Wikibase_Qid' in row and isinstance(row['Wikibase_Qid'], str) and re.search(r'^Q[0-9]+$',
                                                                                        str(row['Wikibase_Qid'])):
            print('Found Wikibase Qid, will use that.')
            creatorqid = row['Wikibase_Qid']
        elif 'Wikidata_Qid' in row and isinstance(row['Wikidata_Qid'], str) and re.search(r'^Q[0-9]+$',
                                                                                          str(row['Wikidata_Qid'])):
            creatorwdqid = row['Wikidata_Qid']
            if creatorwdqid not in wikidatacreators:
                # check whether this wikicreator is already on wikibase
                query = 'SELECT * WHERE { ?wikibase_entity xdp:' + config['mapping']['prop_wikidata_entity'][
                    'wikibase'] + ' "' + creatorwdqid + '" }'
                bindings = \
                xwbi.wbi_helpers.execute_sparql_query(query=query, prefix=config['mapping']['wikibase_sparql_prefixes'])[
                    'results']['bindings']
                if len(bindings) > 1:
                    print('Mapping error: More than one entity is linked to ' + creatorwdqid + ':\n' + str(bindings))
                    print('These entities should probably be merged to one.')
                    input('Press ENTER to continue and use the first in this list to process.')
                if len(bindings) > 0:
                    creatorqid = bindings[0]['wikibase_entity']['value'].replace(
                        config['mapping']['wikibase_entity_ns'], '')
                    print(
                        'Wikidata ' + creatorwdqid + ': This person was found via Sparql on Wikibase as ' + creatorqid + ', will use that.')
                if len(bindings) == 0:
                    print(f"Will create new person item for {row['fullName']}, Wikidata {creatorwdqid}")
                    creatorqid = xwbi.importitem(creatorwdqid, wbqid=False, process_claims=False,
                                                 classqid=config['mapping']['class_person']['wikibase'])
            else:
                creatorqid = wikidatacreators[creatorwdqid]
                print(
                    f"A person for {row['fullName']}, Wikidata {creatorwdqid} has been created in this run of the script: {creatorqid}")

        else:
            print('This row contains no Wikidata and no Wikibase Qid.')
            if (wikidata or wikibase) and not unrecon:
                continue # unreconciled items only when shown again to the user (after having processed the reconciled)
            if row['fullName_clusters'].strip() not in newcreators:
                print(
                    f"{row['fullName_clusters'].strip()} belongs to no known cluster. Will create a new creator item.")
                newitem = {"qid": False, "statements": [], "labels": [], "aliases": []}
                for language in config['mapping']['wikibase_label_languages']:
                    newitem['labels'].append({'lang': language, 'value': row['fullName']})
                    if isinstance(row['givenName'], str) and isinstance(row['lastName'], str):
                        newitem['aliases'].append(
                            {'lang': language, 'value': row['lastName'] + ', ' + row['givenName']})
                # if isinstance(row['givenName'], str):
                # 	newitem['statements'].append(
                # 		{'type': 'String', 'prop_nr': config['mapping']['prop_pref_given_name']['wikibase'],
                # 		 'value': row['givenName'].strip()})
                # if isinstance(row['lastName'], str):
                # 	newitem['statements'].append({'type': 'String',
                # 								  'prop_nr': config['mapping']['prop_pref_family_name'][
                # 									  'wikibase'], 'value': row['lastName'].strip()})
                newitemqid = xwbi.itemwrite(newitem)
                newcreators[row['fullName_clusters']] = {'creatorqid': newitemqid,
                                                         'fullName_variants': [row['fullName']]}
                xwb.setclaimvalue(creatorstatement, newitemqid, "item")
                rest = rest[
                    rest.creatorstatement != row['creatorstatement']]  # remove processed row from dataframe copy
                rest.to_csv(infile, index=False)  # save remaining rows for eventual restart of the script
                time.sleep(1)
            else:
                creatorqid = newcreators[row['fullName_clusters'].strip()]['creatorqid']
                if row['fullName'] not in newcreators[row['fullName_clusters'].strip()]['fullName_variants']:
                    newcreators[row['fullName_clusters']]['fullName_variants'].append(row['fullName'])

                print(
                    f"The full name {row['fullName_clusters']} belongs to a cluster the first member of which has been created just before as {creatorqid}. Will use that.")
            with open(newitemjsonfile, 'w', encoding='utf-8') as jsonfile:
                json.dump(newcreators, jsonfile)

        if creatorqid and not newitem:
            # Write creator statement
            xwb.setclaimvalue(creatorstatement, creatorqid, "item")
            if creatorwdqid:
                wikidatacreators[creatorwdqid] = creatorqid
            rest = rest[rest.creatorstatement != row['creatorstatement']]  # remove processed row from dataframe copy
            rest.to_csv(infile, index=False)  # save remaining rows for eventual restart of the script
            # Compare labels, names, and write variants to Wikibase creator item
            creatoritem = xwbi.wbi.item.get(entity_id=creatorqid)
            itemchange = False
            for language in config['mapping']['wikibase_label_languages']:
                existing_preflabel = creatoritem.labels.get(language)
                existing_aliases = []
                if not existing_preflabel:
                    creatoritem.labels.set(language, row['fullName'])
                    itemchange = True
                    existing_preflabel = row['fullName']
                creatoraliases = creatoritem.aliases.get(language)
                if creatoraliases:
                    existing_aliases.append(alias for alias in creatoraliases)
                name_variants = [row['fullName']]
                if isinstance(row['givenName'], str) and isinstance(row['lastName'], str):
                    name_variants.append(row['lastName'] + ', ' + row['givenName'])
                for name_variant in name_variants:
                    if name_variant != existing_preflabel and name_variant not in existing_aliases:
                        print(language + ': This is a new name variant for ' + creatorqid + ': ' + name_variant)
                        creatoritem.aliases.set(language, name_variant)
                        itemchange = True
            if itemchange:
                creatoritem.write()
                print('Writing of new name variant(s) to ' + creatorqid + ' successful.')
            else:
                print(f"No new name variant found for {creatorqid}.")

            time.sleep(1)
    message = f"Successfully processed import CSV, modality was <b>{jobdesc}</b>"
    print(message)
    messages.append(message)
    return messages