from bots import zoterobot, config, littlehelpers, xwbi
import json, sys

# data = zoterobot.getexport()

# with open('test.json', 'w', encoding="utf-8") as file:
#     json.dump(data, file, indent=2)

with open('test.json', 'r', encoding="utf-8") as file:
    data = json.load(file)

zoteromapping = config.load_mapping('zotero')
wikidatamapping = config.load_mapping('zotero_bibtypes')

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
            choice = input(f"\nDo you want to import that item to your Wikibase and use it to represent '{itemtype}'?\n Enter 1 for import as new item, 2 for import to a known Wikibase Qid, 0 for no.")
            print(f"\n{choice}")
        if choice == "1":
            newitem = littlehelpers.import_wikidata_entity(wikidatamapping['mapping'][itemtype], wbid=False, classqid=config.class_bibitem_type)
            zoteromapping['mapping'][itemtype]['bibtypeqid'] = newitem
            config.dump_mapping(zoteromapping)
        elif choice == "2":
            qid = input('Enter Qid to use for item import (e.g. "Q15"): ')
            newitem = littlehelpers.import_wikidata_entity(wikidatamapping['mapping'][itemtype], wbid=qid, classqid=config.class_bibitem_type)
            zoteromapping['mapping'][itemtype]['bibtypeqid'] = newitem
            config.dump_mapping(zoteromapping)
        elif choice == "0":
            print('OK. This item type will be excluded from be processed, until you define a mapping in a future run of this script.')
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
            if item['data'][fieldname] == "": # empty field, won't ask for a mapping
                continue
            if fieldname in fields_to_exclude or itemtype+fieldname in seen_fields or fieldname not in zoteromapping['mapping'][itemtype]['fields']:
                print(f"Skipping {itemtype}>{fieldname}")
                continue
            if zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'] == False:
                print(f"Skipping {itemtype}>{fieldname} as marked for permanent omission.")
                continue
            print(f"\nWe'll now define how to proceed with '{fieldname}' in item type '{itemtype}'...")
            datatype = zoteromapping['mapping'][itemtype]['fields'][fieldname]['dtype']
            if zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop']:
                print(f"Will use existing mapping: {fieldname} > {zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop']}")
            else:
                # check if same fieldname is mapped elsewhere
                print(f"Checking if a field with name {fieldname} is mapped for other item types...")
                wbprop_to_use = None
                suggested_wbprop = None
                for zoterotype in zoteromapping['mapping']:
                    if fieldname in zoteromapping['mapping'][zoterotype]['fields']:
                        if zoteromapping['mapping'][zoterotype]['fields'][fieldname]['wbprop']:
                            suggested_wbprop = zoteromapping['mapping'][zoterotype]['fields'][fieldname]['wbprop']
                            print(f"For a field with the name {fieldname}, in type {zoterotype}, '{suggested_wbprop}' is used.")
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
                        config.dump_mapping(zoteromapping)
                        print(f"OK. I won't ask any more for {fieldname} in item type {itemtype}.")
                    elif choice == "4":
                        if not suggested_wbprop:
                            print('No existing mapping to re-use.')
                            choice = ""
                            continue
                        wbprop_to_use = suggested_wbprop
                        zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'] = wbprop_to_use
                        config.dump_mapping(zoteromapping)
                        print(f"OK. Saved mapping {fieldname} > {suggested_wbprop} in item type {itemtype}.")
                    elif choice == "1":
                        # ask for datatype
                        choice3 = ""
                        choices3 = ["0", "1"]
                        while choice3 not in choices3:
                            choice3 = input(
                                f"\nDatatype for field {fieldname} in item type {itemtype} is set to {datatype}.\nInput '0' for leaving as is, '1' for editing the datatype.")
                            if choice3 == "1":
                                print(f"Possible datatypes are the following: {str(config.datatypes_mapping.keys())}")
                                datatype = None
                                while datatype not in config.datatypes_mapping.keys():
                                    input(
                                        f"\nWrite the datatype you want to set for field {fieldname} in item type {itemtype}: ")
                                zoteromapping['mapping'][itemtype]['fields'][fieldname]['dtype'] = datatype
                                config.dump_mapping(zoteromapping)
                        # ask for property defining options
                        choice2 = ""
                        choices2 = ["1", "2", "3", "4"]
                        while choice2 not in choices2:
                            choice2 = input(f"\nInput '1' for importing a Wikidata property for this as new property;\nInput '2' for overriding an existing property of datatype {datatype} with a Wikidata import;\nInput '3' for creating a new one without Wikidata import;\nInput '4' for using an existing Wikibase property with datatype {datatype}.")
                            if choice2 == "1":
                                wdprop = input("Input the wikidata property ID to import with the preceding letter, e.g. 'P121': ")
                                wbprop_to_use = littlehelpers.import_wikidata_entity(wdprop)
                            if choice2 == "2":
                                wdprop = input("Write the wikidata property ID to import with the preceding letter, e.g. 'P121': ")
                                wbprop = input("Write the ID of the wikibase property to be enriched with the Wikidata import, with the preceding letter, e.g. 'P21': ")
                                wbprop_to_use = littlehelpers.import_wikidata_entity(wdprop, wbid=wbprop)
                            if choice2 == "3":
                                wbprop_to_useentity = xwbi.wbi.property.new(datatype=config.datatypes_mapping[datatype])
                                wbprop_to_useentity.labels.set('en', fieldname)
                                print('enlabel set: ' + fieldname)
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
                                wbprop = input("Write the ID of the wikibase property to be used for this, with the preceding letter, e.g. 'P21': ")
                                wbprop_to_use = wbprop
                            zoteromapping['mapping'][itemtype]['fields'][fieldname]['wbprop'] = wbprop_to_use
                            config.dump_mapping(zoteromapping)
                            seen_fields.append(itemtype+fieldname)

creatorcheck = None
while creatorcheck != "1" and creatorcheck != "0":
    creatorcheck = input(f"\nDo you want to check the creatorTypes mapping of the ingested dataset? '1' for yes, '0' for no.")
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
            if itemtype+creatortype in seen_creators:
                continue
            print(f"\nWe'll now define how to proceed with '{creatortype}' in item type '{itemtype}'...")
            if zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop'] == False:
                print(f"Skipping {itemtype}>{creatortype} as marked for permanent omission.")
                seen_creators.append(itemtype + creatortype)
                continue
            if zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop']:
                print(
                    f"Will use existing mapping: {creatortype} > {zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop']}")
            else:
                # check if same creatortype is mapped elsewhere
                print(f"Checking if a creatorType with name {creatortype} is mapped for other item types...")
                wbprop_to_use = None
                suggested_wbprop = None
                for zoterotype in zoteromapping['mapping']:
                    if creatortype in zoteromapping['mapping'][zoterotype]['creatorTypes']:
                        if zoteromapping['mapping'][zoterotype]['creatorTypes'][creatortype]['wbprop']:
                            suggested_wbprop = zoteromapping['mapping'][zoterotype]['creatorTypes'][creatortype]['wbprop']
                            print(f"For a creatorType with the name {creatortype}, in type {zoterotype}, '{suggested_wbprop}' is used.")
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
                        config.dump_mapping(zoteromapping)
                        print(f"OK. I won't ask any more for {fieldname} in item type {itemtype}.")
                    elif choice == "4":
                        if not suggested_wbprop:
                            print('No existing mapping to re-use.')
                            choice = ""
                            continue
                        wbprop_to_use = suggested_wbprop
                        zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop'] = wbprop_to_use
                        config.dump_mapping(zoteromapping)
                        print(f"OK. Saved mapping {creatortype} > {suggested_wbprop} in item type {itemtype}.")
                    elif choice == "1":
                        # ask for property defining options
                        choice2 = ""
                        choices2 = ["1", "2", "3", "4"]
                        while choice2 not in choices2:
                            choice2 = input(f"\nInput '1' for importing a Wikidata property of type WikibaseItem for this as new property;\nInput '2' for overriding an existing property of datatype WikibaseItem with a Wikidata import;\nInput '3' for creating a new one without Wikidata import;\nInput '4' for using an existing Wikibase property with datatype WikibaseItem.")
                            if choice2 == "1":
                                wdprop = input("Input the wikidata property ID to import with the preceding letter, e.g. 'P121': ")
                                wbprop_to_use = littlehelpers.import_wikidata_entity(wdprop)
                            if choice2 == "2":
                                wdprop = input("Write the wikidata property ID to import with the preceding letter, e.g. 'P121': ")
                                wbprop = input("Write the ID of the wikibase property to be enriched with the Wikidata import, with the preceding letter, e.g. 'P21': ")
                                wbprop_to_use = littlehelpers.import_wikidata_entity(wdprop, wbid=wbprop)
                            if choice2 == "3":
                                wbprop_to_useentity = xwbi.wbi.property.new(datatype=config.datatypes_mapping[WikibaseItem])
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
                                wbprop = input("Write the ID of the wikibase property to be used for this, with the preceding letter, e.g. 'P21': ")
                                wbprop_to_use = wbprop
                            zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop'] = wbprop_to_use
                            config.dump_mapping(zoteromapping)
                            seen_creators.append(itemtype+creatortype)

