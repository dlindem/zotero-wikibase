from bots import zoterobot, botconfig, zotwb_functions, xwbi
import json, sys, re

config = botconfig.load_mapping("config")

data = zoterobot.getexport()

print(f"\nGot a dataset consisting of {str(len(data))} Zotero items (tag '{config['mapping']['zotero_export_tag']}').")

with open('test.json', 'w', encoding="utf-8") as file:
    json.dump(data, file, indent=2)

# with open('test.json', 'r', encoding="utf-8") as file:
#     data = json.load(file)

zoteromapping = botconfig.load_mapping('zotero')
wikidatamapping = botconfig.load_mapping('zotero_bibtypes')

# check if ItemTypes are mapped to Wikibase items
print('\n\nWill now check bibitem types to be imported:')
excluded_types = []
seen_types = []
for item in data:
    itemtype = item['data']['itemType']
    if itemtype in excluded_types or itemtype in seen_types:
        continue
    if itemtype not in zoteromapping['mapping']:
        print(f"Very strange. the item type '{itemtype}' is not found in zotero.json mapping.")
        sys.exit()

    if not zoteromapping['mapping'][itemtype]['bibtypeqid']:
        print(f"The bibliographical item type '{itemtype}' is not mapped to a Wikibase Q-item.")
        print(f"The suggested Wikidata item for '{itemtype}' is {wikidatamapping['mapping'][itemtype]}.")
        choices = ["0", "1", "2"]
        choice = None
        while choice not in choices:
            choice = input(
                f"\nDo you want to import that item to your Wikibase and use it to represent '{itemtype}'?\n Enter 1 for import as new item, 2 for import to a known Wikibase Qid, 0 for no.")
            print(f"\n{choice}")
        if choice == "1":
            newitem = zotwb_functions.import_wikidata_entity(wikidatamapping['mapping'][itemtype], wbid=False,
                                                           classqid=config['mapping']['class_bibitem_type']['wikibase'])
            zoteromapping['mapping'][itemtype]['bibtypeqid'] = newitem
            botconfig.dump_mapping(zoteromapping)
        elif choice == "2":
            qid = input('Enter Qid to use for item import (e.g. "Q15"): ')
            newitem = zotwb_functions.import_wikidata_entity(wikidatamapping['mapping'][itemtype], wbid=qid,
                                                           classqid=config['mapping']['class_bibitem_type']['wikibase'])
            zoteromapping['mapping'][itemtype]['bibtypeqid'] = newitem
            botconfig.dump_mapping(zoteromapping)
        elif choice == "0":
            print(
                'OK. This item type will be excluded from be processed, until you define a mapping in a future run of this script.')
            excluded_types.append(itemtype)
    else:
        print(f"Will use existing mapping: {itemtype} > {zoteromapping['mapping'][itemtype]['bibtypeqid']}")
    seen_types.append(itemtype)

fieldcheck = None
while fieldcheck != "1" and fieldcheck != "0":
    fieldcheck = input(
        f"\nDo you want to check the fields mapping of the ingested dataset? '1' for yes, '0' for no.")
if fieldcheck == "1":
    # check mapping of zotero fields (of those that contain data in the ingested set of records)
    print('\n\nWill now check fields used in the ingested datasets...')
    fields_to_exclude = ['itemType', 'creators']
    seen_fields = []
    for item in data:
        itemtype = item['data']['itemType']
        for fieldname in item['data']:
            if item['data'][fieldname] == "":  # empty field, won't ask for a mapping
                continue
            if fieldname in fields_to_exclude or itemtype + fieldname in seen_fields or fieldname not in zoteromapping['mapping'][itemtype]['fields']:
                print(f"Skipping {itemtype}>{fieldname}")
                continue
            if zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'] == False:
                print(f"Skipping {itemtype}>{fieldname} as marked for permanent omission.")
                continue
            print(f"\nWe'll now define how to proceed with '{fieldname}' in item type '{itemtype}'...")
            datatype = zoteromapping['mapping'][itemtype]['fields'][fieldname]['dtype']
            if zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop']:
                print(
                    f"Will use existing mapping: {fieldname} > {zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop']}")
            else:
                # check if same fieldname is mapped elsewhere
                print(f"Checking if a field with name {fieldname} is mapped for other item types...")
                wbprop_to_use = None
                suggested_wbprop = None
                for zoterotype in zoteromapping['mapping']:
                    if fieldname in zoteromapping['mapping'][zoterotype]['fields']:
                        if zoteromapping['mapping'][zoterotype]['fields'][fieldname]['wbprop']:
                            suggested_wbprop = zoteromapping['mapping'][zoterotype]['fields'][fieldname]['wbprop']
                            print(
                                f"For a field with the name {fieldname}, in type {zoterotype}, '{suggested_wbprop}' is used.")
                choice = ""
                choices = ["1", "2", "3", "4"]
                while choice not in choices:
                    choicestring = f"\nInput '1' for defining a new property mapping,\n'2' for not mapping this field and not use its data in this run,\n'3' for not mapping it and never being asked again."
                    if suggested_wbprop:
                        choicestring += f"\nInput '4' for using {str(suggested_wbprop)} for '{fieldname}' also in type '{itemtype}',"
                    choice = input(choicestring)
                    if choice == "2":
                        fields_to_exclude.append(fieldname)
                    if choice == "3":
                        fields_to_exclude.append(fieldname)
                        zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'] = False
                        botconfig.dump_mapping(zoteromapping)
                        print(f"OK. I won't ask any more for {fieldname} in item type {itemtype}.")
                    elif choice == "4":
                        if not suggested_wbprop:
                            print('No existing mapping to re-use.')
                            choice = ""
                            continue
                        wbprop_to_use = suggested_wbprop
                        zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'] = wbprop_to_use
                        botconfig.dump_mapping(zoteromapping)
                        print(f"OK. Saved mapping {fieldname} > {suggested_wbprop} in item type {itemtype}.")
                    elif choice == "1":
                        # # ask for datatype
                        # choice3 = ""
                        # choices3 = ["0", "1"]
                        # while choice3 not in choices3:
                        #     choice3 = input(
                        #         f"\nDatatype for field {fieldname} in item type {itemtype} is set to {datatype}.\nInput '0' for leaving as is, '1' for editing the datatype.")
                        #     if choice3 == "1":
                        #         print(f"Possible datatypes are the following: {str(botconfig.datatypes_mapping.keys())}")
                        #         datatype = None
                        #         while datatype not in botconfig.datatypes_mapping.keys():
                        #             input(
                        #                 f"\nWrite the datatype you want to set for field {fieldname} in item type {itemtype}: ")
                        #         zoteromapping['mapping'][itemtype]['fields'][fieldname]['dtype'] = datatype
                        #         botconfig.dump_mapping(zoteromapping)
                        # ask for property defining options
                        choice2 = ""
                        choices2 = ["1", "2", "3", "4"]
                        while choice2 not in choices2:
                            choice2 = input(
                                f"\nInput '1' for importing a Wikidata property for this as new property;\nInput '2' for overriding an existing property of datatype {datatype} with a Wikidata import;\nInput '3' for creating a new one without Wikidata import;\nInput '4' for using an existing Wikibase property with datatype {datatype}.")
                            if choice2 == "1":
                                wdprop = input(
                                    "Input the wikidata property ID to import with the preceding letter, e.g. 'P121': ")
                                wbprop_to_use = zotwb_functions.import_wikidata_entity(wdprop)
                            if choice2 == "2":
                                wdprop = input(
                                    "Write the wikidata property ID to import with the preceding letter, e.g. 'P121': ")
                                wbprop = input(
                                    "Write the ID of the wikibase property to be enriched with the Wikidata import, with the preceding letter, e.g. 'P21': ")
                                wbprop_to_use = zotwb_functions.import_wikidata_entity(wdprop, wbid=wbprop)
                            if choice2 == "3":
                                wbprop_to_useentity = xwbi.wbi.property.new(datatype=config['mapping']['datatypes_mapping'][datatype])
                                wbprop_to_useentity.labels.set('en', fieldname)
                                print('enlabel set: ' + fieldname)
                                wbprop_to_use = zotwb_functions.write_property(wbprop_to_useentity)

                            if choice2 == "4":
                                wbprop = input(
                                    "Write the ID of the wikibase property to be used for this, with the preceding letter, e.g. 'P21': ")
                                wbprop_to_use = wbprop
                            zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'] = wbprop_to_use
                            botconfig.dump_mapping(zoteromapping)
                            seen_fields.append(itemtype + fieldname)

creatorcheck = None
while creatorcheck != "1" and creatorcheck != "0":
    creatorcheck = input(
        f"\nDo you want to check the creatorTypes mapping of the ingested dataset? '1' for yes, '0' for no.")
if creatorcheck == "1":
    # check mapping of zotero creators
    creators_to_exclude = []
    seen_creators = []
    for item in data:
        itemtype = item['data']['itemType']
        if 'creators' not in item['data']:
            continue
        for creatordict in item['data']['creators']:
            creatortype = creatordict['creatorType']
            if itemtype + creatortype in seen_creators:
                continue
            print(f"\nWe'll now define how to proceed with '{creatortype}' in item type '{itemtype}'...")
            if zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop'] == False:
                print(f"Skipping {itemtype}>{creatortype} as marked for permanent omission.")
                seen_creators.append(itemtype + creatortype)
                continue
            if zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop']:
                print(
                    f"Will use existing mapping: {creatortype} > {zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop']}")
                seen_creators.append(itemtype + creatortype)
            else:
                # check if same creatortype is mapped elsewhere
                print(f"Checking if a creatorType with name {creatortype} is mapped for other item types...")
                wbprop_to_use = None
                suggested_wbprop = None
                for zoterotype in zoteromapping['mapping']:
                    if creatortype in zoteromapping['mapping'][zoterotype]['creatorTypes']:
                        if zoteromapping['mapping'][zoterotype]['creatorTypes'][creatortype]['wbprop']:
                            suggested_wbprop = zoteromapping['mapping'][zoterotype]['creatorTypes'][creatortype][
                                'wbprop']
                            print(
                                f"For a creatorType with the name {creatortype}, in type {zoterotype}, '{suggested_wbprop}' is used.")
                choice = ""
                choices = ["1", "2", "3", "4"]
                while choice not in choices:
                    choicestring = f"\nInput '1' for defining a new property mapping,\n'2' for not mapping this filed and not use its data in this run,\n'3' for not mapping it and never being asked again."
                    if suggested_wbprop:
                        choicestring += f"\nInput '4' for using {str(suggested_wbprop)} for '{creatortype}' also in type '{itemtype}',"
                    choice = input(choicestring)
                    if choice == "2":
                        creators_to_exclude.append(creatortype)
                    if choice == "3":
                        creators_to_exclude.append(fieldname)
                        zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop'] = False
                        botconfig.dump_mapping(zoteromapping)
                        print(f"OK. I won't ask any more for {fieldname} in item type {itemtype}.")
                    elif choice == "4":
                        if not suggested_wbprop:
                            print('No existing mapping to re-use.')
                            choice = ""
                            continue
                        wbprop_to_use = suggested_wbprop
                        zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop'] = wbprop_to_use
                        botconfig.dump_mapping(zoteromapping)
                        print(f"OK. Saved mapping {creatortype} > {suggested_wbprop} in item type {itemtype}.")
                    elif choice == "1":
                        # ask for property defining options
                        choice2 = ""
                        choices2 = ["1", "2", "3", "4"]
                        while choice2 not in choices2:
                            choice2 = input(
                                f"\nInput '1' for importing a Wikidata property of type WikibaseItem for this as new property;\nInput '2' for overriding an existing property of datatype WikibaseItem with a Wikidata import;\nInput '3' for creating a new one without Wikidata import;\nInput '4' for using an existing Wikibase property with datatype WikibaseItem.")
                            if choice2 == "1":
                                wdprop = input(
                                    "Input the wikidata property ID to import with the preceding letter, e.g. 'P121': ")
                                wbprop_to_use = zotwb_functions.import_wikidata_entity(wdprop)
                            if choice2 == "2":
                                wdprop = input(
                                    "Write the wikidata property ID to import with the preceding letter, e.g. 'P121': ")
                                wbprop = input(
                                    "Write the ID of the wikibase property to be enriched with the Wikidata import, with the preceding letter, e.g. 'P21': ")
                                wbprop_to_use = zotwb_functions.import_wikidata_entity(wdprop, wbid=wbprop)
                            if choice2 == "3":
                                wbprop_to_useentity = xwbi.wbi.property.new(
                                    datatype=config['mapping']['datatypes_mapping']['WikibaseItem'])
                                wbprop_to_useentity.labels.set('en', creatortype)
                                print('enlabel set: ' + creatortype)
                                d = False
                                while d == False:
                                    try:
                                        print('Writing to xwb wikibase...')
                                        r = wbprop_to_useentity.write(is_bot=1, clear=False)
                                        d = True
                                        wbprop_to_use = wbprop_to_useentity.id
                                        print('Successfully written data to item: ' + wbprop_to_use)
                                    except Exception:
                                        ex = traceback.format_exc()
                                        print(ex)
                                        presskey = input('Press key for retry.')
                            if choice2 == "4":
                                wbprop = input(
                                    "Write the ID of the wikibase property to be used for this, with the preceding letter, e.g. 'P21': ")
                                wbprop_to_use = wbprop
                            zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop'] = wbprop_to_use
                            botconfig.dump_mapping(zoteromapping)
                            seen_creators.append(itemtype + creatortype)

input(f"\nPress Enter for starting to process the ingested dataset of {str(len(data))} items.')
# iterate through items / zotero fields and produce wikibase upload
iso3mapping = botconfig.load_mapping('iso-639-3')
iso1mapping = botconfig.load_mapping('iso-639-1')
language_literals = botconfig.load_mapping('language-literals')
count = 0
for item in data:
    count += 1
    print(f"\n[{str(count)}] Now processing item '{item['links']['alternate']['href']}'...")
    qid = False
    newitem = True
    # instance of and bibItem type
    itemtype = item['data']['itemType']
    statements = [
        {'type': 'WikibaseItem', 'prop_nr': config['mapping']['prop_instanceof']['wikibase'], 'value': config['mapping']['class_bibitem}']['wikibase'],
        {'type': 'WikibaseItem', 'prop_nr': config['mapping']['prop_itemtype']['wikibase'],
         'value': zoteromapping['mapping'][itemtype]['bibtypeqid']}
    ]
    # fields with special meaning / special procedure
    ## Zotero ID and Fulltext PDF attachment(s)
    attqualis = []
    if item['meta']['numChildren'] > 0:
        children = zoterobot.getchildren(item['data']['key'])
        for child in children:
            if 'contentType' not in child['data']: # these are notes attachments
                continue
            if child['data']['contentType'] == "application/pdf":
                attqualis.append(
                    {'prop_nr': config['mapping']['prop_zotero_PDF']['wikibase'], 'type': 'ExternalId', 'value': child['data']['key']})
            if config['mapping']['store_qid_in_attachment'] and child['data']['contentType'] == "" and child['data'][
                'url'].startswith(config['mapping']['wikibase_entity_ns']):
                qid = child['data']['url'].replace(config['mapping']['wikibase_entity_ns'], "")
                print('Found link attachment: This item is linked to ' + config['mapping']['wikibase_entity_ns'] + qid)
                newitem = False
    else:
        children = []
    statements.append({'prop_nr': config['mapping']['prop_zotero_item']['wikibase'], 'type': 'ExternalId', 'value': item['data']['key'],
                       'qualifiers': attqualis})

    ## archiveLocation (special for items stemming from LexBib)
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
            languageqid = zotwb_functions.import_wikidata_entity(languagewdqid, classqid=config['mapping']['class_language']['wikibase'])
            iso3mapping['mapping'][item['data']['language']]['wbqid'] = languageqid
            botconfig.dump_mapping(iso3mapping)
        if languageqid and zoteromapping['mapping'][itemtype]['fields']['language']['wbprop']:
            statements.append(
                {'prop_nr': zoteromapping['mapping'][itemtype]['fields']['language']['wbprop'], 'type': 'WikibaseItem',
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

    ## ISBN
    if 'ISBN' in item['data']:
        val = item['data']['ISBN'].replace("-", "")  # normalize ISBN
        valsearch = re.search(r'^\d+', val)  # only take the first block of digits (i.e., only the first ISBN listed)
        if valsearch:
            val = valsearch.group(0)
            if len(val) == 10:
                statements.append({"prop_nr": config['mapping']['prop_isbn_10']['wikibase'], "type": "ExternalId", "value": val})
            elif len(val) == 13:
                statements.append({"prop_nr": config['mapping']['prop_isbn_13']['wikibase'], "type": "ExternalId", "value": val})
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
                newitem = False
                print('This BibItem already exists on the wikibase as ' + qid)
            else:
                qid = False  # a new BibItem will be created on the Wikibase
                newitem = True
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
    listpos = {}
    for creator in item['data']['creators']:
        if creator['creatorType'] not in listpos:
            listpos[creator['creatorType']] = 1
        else:
            listpos[creator['creatorType']] += 1
        if zoteromapping['mapping'][itemtype]['creatorTypes'][creator['creatorType']]['wbprop']:
            creatorprop = zoteromapping['mapping'][itemtype]['creatorTypes'][creator['creatorType']]['wbprop']

            # if "non-dropping-particle" in creator:
            #     creator["family"] = creator["non-dropping-particle"] + " " + creator["family"]
            # if creator["family"] == "Various":
            #     creator["given"] = "Various"
            ### TODO: non dropping particles / middle names

            creatorqualis = [{"prop_nr": config['mapping']['prop_series_ordinal']['wikibase'], "type": "string",
                              "value": str(listpos[creator['creatorType']])}]
            if 'name' in creator:
                creatorqualis.append(
                    {"prop_nr": config['mapping']['prop_source_literal']['wikibase'], "type": "string", "value": creator['name']})
            elif 'firstName' in creator:
                if creator['firstName'] != "":
                    creatorqualis += [{"prop_nr": config['mapping']['prop_source_literal']['wikibase'], "type": "string",
                                       "value": creator["firstName"] + " " + creator["lastName"]},
                                      {"prop_nr": config['mapping']['prop_given_name_source_literal']['wikibase'], "type": "string",
                                       "value": creator["firstName"]},
                                      {"prop_nr": config['mapping']['prop_family_name_source_literal']['wikibase'], "type": "string",
                                       "value": creator["lastName"]}]
                else:
                    creatorqualis.append(
                        {"prop_nr": config['mapping']['prop_source_literal']['wikibase'], "type": "string", "value": creator["lastName"]})
            else:
                creatorqualis.append(
                    {"prop_nr": config['mapping']['prop_source_literal']['wikibase'], "type": "string", "value": creator["lastName"]})
            statements.append({
                "prop_nr": creatorprop,
                "type": "item",
                "value": False,  # this produces an "UNKNOWN VALUE" statement
                "qualifiers": creatorqualis
            })

    # Other fields
    fields_to_exclude = ['language', 'creators', 'ISBN', 'extra', 'abstractNote', 'date']
    for fieldname in item['data']:
        if fieldname in fields_to_exclude or fieldname not in zoteromapping['mapping'][itemtype]['fields']:
            continue
        if item['data'][fieldname] == "":  # no empty strings
            continue
        if zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop']:
            if zoteromapping['mapping'][itemtype]['fields'][fieldname]['dtype'] == "String":
                statements.append({
                    'prop_nr': zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'],
                    'type': "String",
                    'value': item['data'][fieldname].strip()
                })
            elif zoteromapping['mapping'][itemtype]['fields'][fieldname]['dtype'] == "WikibaseItem":
                statements.append({
                    'prop_nr': zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'],
                    'type': "WikibaseItem",
                    'value': False,
                    'qualifiers': [{'type': 'String', 'prop_nr': config['mapping']['prop_source_literal']['wikibase'],
                                    'value': item['data'][fieldname].strip()}]
                })
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
    if qid: # if writing was successful (if not, qid is still False)
        zoterobot.patch_item(qid=qid, zotitem=item, children=children)

print(
    f"\nFinished exporting the dataset of {str(len(data))} items marked with the tag '{config['mapping']['zotero_export_tag']}'.\nSuccessfully exported items should now have the tag '{config['mapping']['zotero_on_wikibase_tag']}' instead.")
