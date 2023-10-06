import csv
import json
import re
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os, glob
import sys, shutil
from pathlib import Path
from bots import xwb, xwbi, config
import pandas


# This expects a csv with the following colums:
# bibItem [bibitem xwb Qid] / creatorstatement / listpos / fullName / Qid [reconciled person item xwb-qid] / givenName / lastName

list_of_files = glob.glob('data/reconciled_creators/*.csv') # * means all if need specific format then *.csv
infile = max(list_of_files, key=os.path.getctime)
origfile = infile.replace('.csv','_original.csv')
if not Path(origfile).is_file():
	shutil.copyfile(infile, origfile)
print('This file will be processed: '+infile)
df = pandas.read_csv(infile)
rest = df.copy()
newcreators = {}
wikidatacreators = {}

for rowindex, row in df.iterrows():
	#statement_id_re = re.compile(r'statement\/(Q\d+)\-(.*)')

	creatorqid = None
	print('\nItem ['+str(rowindex)+']:')
	bibItem = row['bibItem'].replace(config.wikibase_entity_ns, "")
	print('BibItem is '+bibItem+'.')
	creatorstatement = re.search(r'statement/(Q.*)', row['creatorstatement']).group(1)
	print('CreatorStatement is '+creatorstatement+'.')
	if 'Wikibase_Qid' in row and isinstance(row['Wikibase_Qid'], str) and re.search(r'^Q[0-9]+$',str(row['Wikibase_Qid'])):
		creatorqid = row['Wikibase_Qid']
	elif 'Wikidata_Qid' in row and isinstance(row['Wikidata_Qid'], str) and re.search(r'^Q[0-9]+$',str(row['Wikidata_Qid'])):
		creatorwdqid = row['Wikidata_Qid']
		if creatorwdqid not in wikidatacreators:
			# check whether this wikicreator is already on wikibase
			query = 'SELECT * WHERE { ?wikibase_entity xdp:'+config.prop_wikidata_entity+' "'+creatorwdqid+'" }'
			bindings = xwbi.wbi_helpers.execute_sparql_query(query=query, prefix=config.sparql_prefixes)['results']['bindings']
			if len(bindings) > 1:
				print('Mapping error: More than one entity is linked to '+creatorwdqid+':\n'+str(bindings))
				print('These entities should probably be merged to one.')
				input('Press ENTER to continue and use the first in this list to process.')
			if len(bindings) > 0:
				creatorqid = bindings[0]['wikibase_entity']['value'].replace(config.wikibase_entity_ns, '')
				print('This person exists already as '+creatorqid+', will use that.')
			if len(bindings) == 0:
				print(f"Will create new person item for {row['fullName']}, Wikidata {creatorwdqid}")
				creatorqid = xwbi.importitem(creatorwdqid, wbqid=False, process_claims=False, classqid=config.class_person)
		else:
			creatorqid = wikidatacreators[creatorwdqid]
			print(f"A person for {row['fullName']}, Wikidata {creatorwdqid} has been created in this run of the script: {creatorqid}")

	else:
		print('This row contains no Wikidata and no Wikibase Qid.')

	if creatorqid:
		# Write creator statement
		xwb.setclaimvalue(creatorstatement, creatorqid, "item")
		wikidatacreators[creatorwdqid] = creatorqid
		rest = rest[rest.creatorstatement != row['creatorstatement']] # remove processed row from dataframe copy
		rest.to_csv(infile, index=False) # save remaining rows for eventual restart of the script
		# Compare labels, names, and write variants to Wikibase creator item
		creatoritem = xwbi.wbi.item.get(entity_id=creatorqid)
		itemchange = False
		for language in config.label_languages:
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
			print('No new name variant found for '+creatorqid+'.')


	time.sleep(1)

# if row['fullName'].strip() not in newcreators:
	# 	print('Will create new person item for '+row['fullName'])
	# 	creatorqid = xwb.newitemwithlabel("Q5","en",row['fullName'].strip())
	# 	xwb.stringclaim(creatorqid,config.prop_given_name_source_literal,row['givenName'].strip())
	# 	xwb.stringclaim(creatorqid,config.prop_family_name_source_literal,row['lastName'].strip())
	# 	xwb.setlabel(creatorqid,"en",row['lastName'].strip()+", "+row['firstName'].strip(), type="alias")
	# 	newcreators[row['fullName'].strip()] = creatorqid
	# else:
	# 	creatorqid = newcreators[row['fullName'].strip()]
	# 	print('A person item for this fullName has been created before in this iteration of the script and will be re-used: '+row['fullName']+': '+creatorqid)