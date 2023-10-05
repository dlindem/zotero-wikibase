import csv
import json
import re
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os
import sys
from bots import xwb, xwbi, config


# This expects a csv with the following colums:
# bibItem [bibitem xwb Qid] / creatorstatement / listpos / fullName / Qid [reconciled person item xwb-qid] / givenName / lastName

# ask for file to process
print('Please select Open Refine output CSV to be processed.')
Tk().withdraw()
infile = askopenfilename()
print('This file will be processed: '+infile)

if (os.path.isfile(infile) == False) or (infile.endswith('.csv') == False):
	print('Error opening file.')
	sys.exit()

with open(infile, encoding="utf-8") as f:
	data = csv.DictReader(f)

	#statement_id_re = re.compile(r'statement\/(Q\d+)\-(.*)')
	count = 1
	newcreators = {}
	wikidatacreators = {}
	for item in data:
        creatorqid = None
		print('\nItem ['+str(count)+']:')
		bibItem = item['bibItem'].replace(config.wikibase_url,"")
		print('BibItem is '+bibItem+'.')
		creatorstatement = re.search(r'statement/(Q.*)', item['creatorstatement']).group(1)
		print('CreatorStatement is '+creatorstatement+'.')
		if 'Wikibase_Qid' in item and item['Wikibase_Qid'].startswith("Q"): # write creator item to creatorstatement
			creatorqid = item['Qid']
			xwb.setclaimvalue(creatorstatement, creatorqid, "item")
			creatoritemlabel = xwb.getlabel(creatorqid,"en")
			creatoritemaliaslist = xwb.getaliases(creatorqid,"en")
			if (item['fullName'] != creatoritemlabel) and (item['fullName'] not in creatoritemaliaslist):
				print('This is a new name variant for '+creatorqid+': '+item['fullName'])
				xwb.setlabel(creatorqid,"en",item['fullName'],type="alias")
		elif 'Wikidata_Qid' in item and item['Wikidata_Qid'].startswith("Q"):
			creatorwdqid = item['Wikidata_Qid']
			if creatorwdqid not in wikidatacreators:
				print(f"Will create new person item for {item['fullName']}, Wikidata {creatorwdqid}")
				creatorqid = xwbi.importitem(creatorwdqid, wbqid=False, process_claims=False, classqid=config.class_person)
			else:
				creatorqid = wikidatacreators[creatorwdqid]
				print(f"A person for {item['fullName']}, Wikidata {creatorwdqid} has been created in this run of the script: {creatorqid}")
		# if item['fullName'].strip() not in newcreators:
		# 	print('Will create new person item for '+item['fullName'])
		# 	creatorqid = xwb.newitemwithlabel("Q5","en",item['fullName'].strip())
		# 	xwb.stringclaim(creatorqid,config.prop_given_name_source_literal,item['givenName'].strip())
		# 	xwb.stringclaim(creatorqid,config.prop_family_name_source_literal,item['lastName'].strip())
		# 	xwb.setlabel(creatorqid,"en",item['lastName'].strip()+", "+item['firstName'].strip(), type="alias")
		# 	newcreators[item['fullName'].strip()] = creatorqid
		# else:
		# 	creatorqid = newcreators[item['fullName'].strip()]
		# 	print('A person item for this fullName has been created before in this iteration of the script and will be re-used: '+item['fullName']+': '+creatorqid)
			xwb.setclaimvalue(creatorstatement, creatorqid, "item")
		count +=1
		time.sleep(1)
