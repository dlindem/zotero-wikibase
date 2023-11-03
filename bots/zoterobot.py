import requests, time, re, json
from bots import botconfig
from pyzotero import zotero
import urllib.error
config = botconfig.load_mapping("config")
with open('bots/config_private.json', 'r', encoding="utf-8") as jsonfile:
    config_private = json.load(jsonfile)
pyzot = zotero.Zotero(int(config['mapping']['zotero_group_id']), 'group', config_private['zotero_api_key'])  # Zotero LexBib group
try:
    print(f"**** Zotero API key groups access: {str(pyzot.key_info()['access']['groups'])}. ****")
except Exception as ex:
    if 'Invalid Authorization' in str(ex):
        print('**** Zotero API key not accepted, zotero bot cannot be loaded. ****')
    else:
        raise
# citations_cache = {}
# with open('bots/data/citations_cache.jsonl') as jsonlfile:
#     jsonl = jsonlfile.read().split('\n')
#     for line in jsonl:
#         if line.startswith("{"):
#             jsonline = json.loads(line)
#             citations_cache[jsonline['zotitemid']] = jsonline['citation']
#
#
# def getcitation(zotitemid):
#     global citations_cache
#     if zotitemid in citations_cache:
#         print(f"Will take citation from cache: {zotitemid}")
#         return citations_cache[zotitemid]
#     print(f'Will now get citation for Zotero ID {zotitemid}')
#     zotapid = 'https://api.zotero.org/groups/' + config['mapping']['zotero_group_id'] + '/items/' + zotitemid
#     attempts = 0
#     while attempts < 5:
#         attempts += 1
#         params = {'format': 'json', 'include': 'bib', 'linkwrap': 1, 'locale': 'eu_ES',
#                   'style': 'modern-language-association'}
#         r = requests.get(zotapid, params=params)
#         if "200" in str(r):
#             zotitem = r.json()
#             # print(zotitemid + ': got zotitem data')
#             # print(zotitem['bib'])
#             bib = re.search('<div class="csl-entry">(.*)</div>', zotitem['bib']).group(1)
#             # convert Lexbib link (from "archive location" - needs mla style)
#             bib = re.sub(r'https?://lexbib.elex.is/entity/(Q[0-9]+)', r'([[Item:\1|\1]])', bib)
#             # convert remaining links
#             bib = re.sub(r'<a href="(https?://)([^/]+)([^"]+)">[^<]+</a>', r'[\1\2\3 \2]', bib)
#             print(bib)
#             citations_cache[zotitemid] = bib
#             with open('data/citations_cache.jsonl', 'a', encoding='utf-8') as jsonlfile:
#                 jsonlfile.write(json.dumps({'zotitemid': zotitemid, 'citation': bib}) + '\n')
#             return (bib)
#
#         if "400" or "404" in str(r):
#             print('*** Fatal error: Item ' + zotitemid + ' got ' + str(r) + ', does not exist on Zotero. Will skip.')
#             time.sleep(5)
#             break
#         print('Zotero API GET request failed (' + zotitemid + '), will repeat. Response was ' + str(r))
#         time.sleep(2)


# testitem = "HERCJU9P"
# print(getcitation(testitem))

def getzotitem(zotitemid):
    pass


def getexport(save_to_file=False):
    rawitems = pyzot.items(tag=config['mapping']['zotero_export_tag'])
    exportitems = []
    for rawitem in rawitems:
        regex = re.search(rf"{config['mapping']['wikibase_entity_ns']}(Q[0-9]+)", rawitem['data']['extra'])
        if regex:
            rawitem['wikibase_entity'] = regex.group(1)
        else:
            rawitem['wikibase_entity'] = False
        exportitems.append(rawitem)
    if save_to_file:
        with open('data/zoteroexport.json', 'w', encoding='utf-8') as jsonfile:
            json.dump(exportitems, jsonfile, indent=2)
    return exportitems


def getchildren(zotitemid):
    children = pyzot.children(zotitemid)
    return children


def patch_item(qid=None, zotitem=None, children=[]):
    # communicate with Zotero, write Wikibase entity URI to "extra" and attach URI as link attachment
    needs_update = False
    if config['mapping']['store_qid_in_attachment']:
        attachment_present = False
        for child in children:
            if 'url' not in child['data']:
                continue
            if child['data']['url'].startswith(config['mapping']['wikibase_entity_ns']):
                if child['data']['url'].endswith(qid):
                    print('Correct link attachment already present.')
                    attachment_present = True
                else:
                    print('Fatal error: Zotero item was linked before to this other Q-id:\n'+child['data']['url'])
                    input('Press enter to continue or CTRL+C to abort.')
        if not attachment_present:
            attachment = [
                {
                    "itemType": "attachment",
                    "parentItem": zotitem['data']['key'],
                    "linkMode": "linked_url",
                    "title": config['mapping']['wikibase_name'],
                    "accessDate": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "url": config['mapping']['wikibase_entity_ns'] + qid,
                    "note": '<p>See this item as linked data at <a href="' + config['mapping']['wikibase_url'] + '/wiki/Item:' + qid + '">' + config['mapping']['wikibase_entity_ns'] + qid + '</a>',
                    "tags": [],
                    "collections": [],
                    "relations": {},
                    "contentType": "",
                    "charset": ""
                }
            ]
            r = requests.post('https://api.zotero.org/groups/' + config['mapping']['zotero_group_id'] + '/items',
                              headers={"Zotero-API-key": config_private['zotero_api_key'],
                                       "Content-Type": "application/json"}, json=attachment)
            if "200" in str(r):
                print(f"Link attachment successfully attached to Zotero item {zotitem['data']['key']}.")
                needs_update = True

    if config['mapping']['store_qid_in_extra']:
        if config['mapping']['wikibase_entity_ns']+qid in zotitem['data']['extra']:
            print('This item already has its Wikibase item URI stored in EXTRA.')
        else:
            zotitem['data']['extra'] = config['mapping']['wikibase_entity_ns'] + qid + "\n" + zotitem['data']['extra']
            print('Successfully written Wikibase item URI to EXTRA.')
            needs_update = True
    tagpresent = False
    tagpos = 0
    while tagpos < len(zotitem['data']['tags']):
        if zotitem['data']['tags'][tagpos]['tag'] == config['mapping']['zotero_on_wikibase_tag']:
            tagpresent = True
        # remove export tag
        if zotitem['data']['tags'][tagpos]['tag'] == config['mapping']['zotero_export_tag']:
            del zotitem['data']['tags'][tagpos]
            needs_update = True
        tagpos += 1
    if not tagpresent:
        zotitem['data']['tags'].append({'tag': config['mapping']['zotero_on_wikibase_tag']})
        needs_update = True
    if needs_update:
        del zotitem['wikibase_entity'] # raises zotero api error if left in item
        try:
            pyzot.update_item(zotitem, last_modified=None)
            return True
        except Exception as err:
            if "Item has been modified since specified version" in str(err):
                return "Versioning_Error"
            else:
                return False

print('zoterobot load finished.')