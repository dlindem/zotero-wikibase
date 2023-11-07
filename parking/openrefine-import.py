import csv
import json
import re
import time
import os, glob
import sys, shutil
from pathlib import Path
from bots import xwb, xwbi, botconfig
import pandas

config = botconfig.load_mapping("config")

# This expects a csv with the following colums:
# bibItem [bibitem xwb Qid] / creatorstatement / listpos / fullName / Qid [reconciled person item xwb-qid] / givenName / lastName

list_of_files = glob.glob('data/creators_reconciled/*.csv') # * means all if need specific format then *.csv
infile = max(list_of_files, key=os.path.getctime)
origfile = infile.replace('.csv','.csv.copy')
if not Path(origfile).is_file():
	shutil.copyfile(infile, origfile)
print('This file will be processed: '+infile)
time.sleep(2)
newitemjsonfile = infile.replace(".csv", "_newcreatorslog.json")
if Path(newitemjsonfile).is_file():
	with open(newitemjsonfile, 'r', encoding='utf-8') as jsonfile:
		newcreators = json.load(jsonfile)
else:
	newcreators = {}

df = pandas.read_csv(infile)
rest = df.copy()

wikidatacreators = {}

for rowindex, row in df.iterrows():
	creatorwdqid = None
	creatorqid = False
	print('\nItem in CSV row ['+str(rowindex+2)+']:')
	bibItem = row['bibItem'].replace(config['mapping']['wikibase_entity_ns'], "")
	print('BibItem is '+bibItem+'.')
	creatorstatement = re.search(r'statement/(Q.*)', row['creatorstatement']).group(1)
	print('CreatorStatement is '+creatorstatement+'.')
	if 'Wikibase_Qid' in row and isinstance(row['Wikibase_Qid'], str) and re.search(r'^Q[0-9]+$',str(row['Wikibase_Qid'])):
		print('Found Wikibase Qid, will use that.')
		creatorqid = row['Wikibase_Qid']
	elif 'Wikidata_Qid' in row and isinstance(row['Wikidata_Qid'], str) and re.search(r'^Q[0-9]+$',str(row['Wikidata_Qid'])):
		creatorwdqid = row['Wikidata_Qid']
		if creatorwdqid not in wikidatacreators:
			# check whether this wikicreator is already on wikibase
			query = 'SELECT * WHERE { ?wikibase_entity xdp:'+config['mapping']['prop_wikidata_entity']['wikibase']+' "'+creatorwdqid+'" }'
			bindings = xwbi.wbi_helpers.execute_sparql_query(query=query, prefix=config['mapping']['sparql_prefixes'])['results']['bindings']
			if len(bindings) > 1:
				print('Mapping error: More than one entity is linked to '+creatorwdqid+':\n'+str(bindings))
				print('These entities should probably be merged to one.')
				input('Press ENTER to continue and use the first in this list to process.')
			if len(bindings) > 0:
				creatorqid = bindings[0]['wikibase_entity']['value'].replace(config['mapping']['wikibase_entity_ns'], '')
				print('Wikidata '+creatorwdqid+': This person was found via Sparql on Wikibase as '+creatorqid+', will use that.')
			if len(bindings) == 0:
				print(f"Will create new person item for {row['fullName']}, Wikidata {creatorwdqid}")
				creatorqid = xwbi.importitem(creatorwdqid, wbqid=False, process_claims=False, classqid=config['mapping']['class_person']['wikibase'])
		else:
			creatorqid = wikidatacreators[creatorwdqid]
			print(f"A person for {row['fullName']}, Wikidata {creatorwdqid} has been created in this run of the script: {creatorqid}")

	else:
		print('This row contains no Wikidata and no Wikibase Qid.')
		if row['fullName_clusters'].strip() not in newcreators:
			print(f"{row['fullName_clusters'].strip()} belongs to no known cluster. Will create a new creator item.")
			newitem = {"qid": False, "statements": [], "labels": [], "aliases": []}
			for language in config['mapping']['wikibase_label_languages']:
				newitem['labels'].append({'lang': language, 'value': row['fullName']})
				if isinstance(row['givenName'], str) and isinstance(row['lastName'], str):
					newitem['aliases'].append({'lang': language, 'value': row['lastName'] + ', ' + row['givenName']})
			# if isinstance(row['givenName'], str):
			# 	newitem['statements'].append(
			# 		{'type': 'String', 'prop_nr': config['mapping']['prop_pref_given_name']['wikibase'],
			# 		 'value': row['givenName'].strip()})
			# if isinstance(row['lastName'], str):
			# 	newitem['statements'].append({'type': 'String',
			# 								  'prop_nr': config['mapping']['prop_pref_family_name'][
			# 									  'wikibase'], 'value': row['lastName'].strip()})
			newitemqid = xwbi.itemwrite(newitem)
			newcreators[row['fullName_clusters']] = {'creatorqid':newitemqid, 'fullName_variants':[row['fullName']]}
			xwb.setclaimvalue(creatorstatement, newitemqid, "item")
			rest = rest[rest.creatorstatement != row['creatorstatement']]  # remove processed row from dataframe copy
			rest.to_csv(infile, index=False)  # save remaining rows for eventual restart of the script
			time.sleep(1)
		else:
			creatorqid = newcreators[row['fullName_clusters'].strip()]['creatorqid']
			if row['fullName'] not in newcreators[row['fullName_clusters'].strip()]['fullName_variants']:
				newcreators[row['fullName_clusters']]['fullName_variants'].append(row['fullName'])

			print(
				f"The full name {row['fullName_clusters']} belongs to a cluster the first member of which has been created just before as {creatorqid}. Will use that.")
		with open(newitemjsonfile, 'w', encoding='utf-8') as jsonfile:
			json.dump(newcreators, jsonfile, indent=2)

	if creatorqid:
		# Write creator statement
		xwb.setclaimvalue(creatorstatement, creatorqid, "item")
		if creatorwdqid:
			wikidatacreators[creatorwdqid] = creatorqid
		rest = rest[rest.creatorstatement != row['creatorstatement']] # remove processed row from dataframe copy
		rest.to_csv(infile, index=False) # save remaining rows for eventual restart of the script
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
				name_variants.append(row['lastName']+', '+row['givenName'])
			for name_variant in name_variants:
				if name_variant != existing_preflabel and name_variant not in existing_aliases:
					print(language+': This is a new name variant for ' + creatorqid + ': ' + name_variant)
					creatoritem.aliases.set(language, name_variant)
					itemchange = True
		if itemchange:
			creatoritem.write()
			print('Writing of new name variant(s) to '+creatorqid+' successful.')
		else:
			print(f"No new name variant found for {creatorqid}.")

		time.sleep(1)
