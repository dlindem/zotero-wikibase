from bots import botconfig
import json

zotero = botconfig.load_mapping('zotero')
with open(f"profiles/{profile}/zotero_api_schema.json") as jsonfile:
    apischema = json.load(jsonfile)['locales']['en-GB']['fields']
    for field in apischema:
        name = apischema[field]
        if field in zotero['mapping']['all_types']['fields']:
            zotero['mapping']['all_types']['fields'][field]['name'] = name
        else:
            print(field)

botconfig.dump_mapping(zotero)

