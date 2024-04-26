import sys, os, csv, time, mwclient, json

from bots import xwbi

with open(f"serbian_scripts/data/config_private.json", 'r', encoding="utf-8") as jsonfile:
	config_private = json.load(jsonfile)
site = mwclient.Site('serbian.wikibase.cloud')
def get_token():
	global site
	login = site.login(username="DavidLbot", password=config_private["wb_bot_pwd"])
	csrfquery = site.api('query', meta='tokens')
	token=csrfquery['query']['tokens']['csrftoken']
	print("Got fresh CSRF token for Serbian Wikibase.")
	return token
token = get_token()

def newform(lid, form, gram=None, form_id=None, nodupcheck = None):
	global token

	# existingforms = {}
	# request = site.get('wbgetentities', ids=lid)
	# if "success" in request:
	# 	try:
	# 		for existform in request['entities'][lid]['forms']:
	# 			existingforms[existform['representations']['eu']['value']] = existform['id']
	# 		if nodupcheck and form in existingforms:
	# 			print('This form already exists: '+existingforms[form])
	# 			return existingforms[form]
	# 	except Exception as ex:
	# 		print('Get existing forms operation failed for: '+lid) #,str(ex))

	data = {"representations":{"sr":{"value":form,"language":"sr"}}}
	data["grammaticalFeatures"] = []
	done = 0
	while done < 1:
		try:
			formcreation = site.post('wbladdform', token=token, format="json", lexemeId=lid, bot=1, data=json.dumps(data))
			#itemcreation = site.post('wbeditentity', token=token, format="json", id=lid, bot=1, data=json.dumps(data))
		except Exception as ex:
			if 'Invalid CSRF token.' in str(ex):
				print('Wait a sec. Must get a new CSRF token...')
				token = get_token()
			else:
				print(str(ex))
				time.sleep(4)
				done += 0.2
			continue
		#print(str(itemcreation))
		if formcreation['success'] == 1:
			#print(str(formcreation))
			formid = formcreation['form']['id']
			print('Form creation for '+lid+': success: '+formid)
			if form_id:
				stringclaim(formid,"P21",form_id)
			return formid
		else:
			print('Form creation failed, will try again...')
			time.sleep(2)
			done += 0.2
	print('newform failed 5 times.'+lid+','+form+','+str(gram)+','+form_id)
	logging.error('newform failed 5 times.'+lid+','+form+','+str(gram)+','+form_id)
	return False

def newlexeme(pos=None, lemma=None, lexemeid=None):
	global token
	data = {"type":lexeme, "lemmas":[{"language":"sr", "value":lemma}]}
	done = 0
	while done < 1:
		try:
			lexemecreation = site.post('wbeditentitiy', token=token, format="json", new=lexeme, bot=1,
									 data=json.dumps(data))

		except Exception as ex:
			if 'Invalid CSRF token.' in str(ex):
				print('Wait a sec. Must get a new CSRF token...')
				token = get_token()
			else:
				print(str(ex))
				time.sleep(4)
				done += 0.2
			continue
		# print(str(itemcreation))
		if lexemecreation['success'] == 1:
			# print(str(formcreation))
			lid = formcreation['lexeme']['id']
			print('Lexeme creation for ' + lexemeid+ ': success: ' + lid)
			stringclaim(lid, "P21", lexemeid)

			return lid
		else:
			print('Form creation failed, will try again...')
			time.sleep(2)
			done += 0.2
	print('newform failed 5 times.' + lid + ',' + form + ',' + str(gram) + ',' + form_id)
	logging.error('newform failed 5 times.' + lid + ',' + form + ',' + str(gram) + ',' + form_id)
	return False

def stringclaim(s, p, o):
	global token

	done = False
	value = '"'+o.replace('"', '\\"')+'"'
	while (not done):
		try:
			request = site.post('wbcreateclaim', token=token, entity=s, property=p, snaktype="value", value=value, bot=1)
			if request['success'] == 1:
				done = True
				claimId = request['claim']['id']
				print('Claim creation done: '+s+' ('+p+') '+o+'.')
				#time.sleep(1)
		except Exception as ex:
			if 'Invalid CSRF token.' in str(ex):
				print('Wait a sec. Must get a new CSRF token...')
				token = get_token()
			else:
				print('Claim creation failed, will try again...\n'+str(ex))
				time.sleep(4)
	return claimId

# http://fuseki.jerteh.rs/#/dataset/SMD2-ontolex/query?query=PREFIX%20ontolex%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2Fns%2Flemon%2Fontolex%23%3E%0APREFIX%20lex%3A%20%3Chttp%3A%2F%2Fpurl.org%2Flex%23%3E%0APREFIX%20olia%3A%20%3Chttp%3A%2F%2Fpurl.org%2Folia%2Folia.owl%23%3E%0APREFIX%20lexinfo%3A%20%3Chttp%3A%2F%2Fwww.lexinfo.net%2Fontology%2F2.0%2Flexinfo%23%3E%0Aselect%20%3Flexeme%20%3FlexinfoPos%20%3FoliaPos%20%3Flemma%20%28group_concat%28concat%28%3Fformrep%2C%22%40%22%2Cstr%28%3Fform%29%29%3BSEPARATOR=%22%7C%22%29%20as%20%3Fforms%29%0Awhere%20%20%7B%0A%20%20%3Flexeme%20lexinfo%3ApartOfSpeech%20%3FlexinfoPos%20%3B%20olia%3ApartOfSpeech%20%3FoliaPos%3B%20ontolex%3AcanonicalForm%20%5Bontolex%3AwrittenRep%20%3Flemma%5D%3B%20ontolex%3AlexicalForm%20%3Fform.%20%3Fform%20ontolex%3AwrittenRep%20%3Fformrep.%0A%20%0A%7D%20group%20by%20%3Flexeme%20%3FlexinfoPos%20%3FoliaPos%20%3Flemma%20%3Fforms

olia_to_lexinfo_pos = {}
with open('serbian_scripts/data/pos_mapping.json') as jsonfile:
	posjson = json.load(jsonfile)
	for item in posjson:
		olia_to_lexinfo_pos[item['oliacat_uri']] = item
	print(olia_to_lexinfo_pos)

# load existing lexemes lookup table
with open('serbian_scripts/data/lexeme_mapping.csv') as mappingcsv:
	mappingrows = mappingcsv.read().split('\n')
	lexeme_map = {}
	for row in mappingrows:
		# print(row)
		mapping = row.split('\t')
		if len(mapping) == 2:
			lexeme_map[mapping[0]] = mapping[1]
print(f'Loaded {str(len(lexeme_map))} existing lexeme mappings.')

with open('serbian_scripts/data/ontolex_dict_lemma_forms_2.csv') as csvfile:
	rows = csv.DictReader(csvfile, delimiter=",") # "lexeme","oliaPos","lemma","forms"
	count = 0
	for row in rows:
		count += 1
		lexemeid = row['lexeme'].replace('http://llod.jerteh.rs/id/SMD/','') # SMD: Q2

		lexemepos = olia_to_lexinfo_pos[row['oliaPos']]['lexinfopos'].replace('https://serbian.wikibase.cloud/entity/', '')
		forms = row['forms'].split('|')
		print(f'\n[{str(count)}] Now processing entry with original URI {lexemeid}, pos {lexemepos}.')

		if lexemeid in lexeme_map:
			print(f"Lexeme {lexemeid} is already there as {lexeme_map[lexemeid]}")
			# if int(lexeme_map[lexemeid][1:]) < 155:
			# 	continue
			# continue
			lexeme = xwbi.wbi.lexeme.get(entity_id=lexeme_map[lexemeid])
			# existing_F1 = lexeme.forms.forms[f"{lexeme.id}-F1"].claims.claims['P21'][0].mainsnak.datavalue['value']
			# print(f"existing F1: {existing_F1}")

		else:
			print(f"Will create new lexeme for {lexemeid}")
			time.sleep(1.1)
			lexeme = xwbi.wbi.lexeme.new(language="Q7", lexical_category=lexemepos)
			lexeme.lemmas.set(language='sr', value=row['lemma'])
			lexeme.claims.add(xwbi.ExternalID(prop_nr='P21', value=lexemeid))
			lexeme.claims.add(xwbi.Item(prop_nr='P22', value="Q20"))

		newforms = 1
		for formgrp in forms:
			newforms += 1
			formrep = formgrp.split('@')[0]
			formuri = formgrp.split('@')[1].replace('http://llod.jerteh.rs/id/SMD/','')
			# if formuri == existing_F1:
			# 	continue
			formid = newform(lexeme.id, formrep, form_id=formuri)
			print(f"success: {formid}")
			time.sleep(0.5)
			# newform = xwbi.Form()
			# newform.grammatical_features = []
			# newform.representations.set(language="sr", value=formrep) # we assume here cardinality 1 for ontolex:writtenRep
			# newform.claims.add(xwbi.ExternalID(prop_nr='P21', value=formuri))
			#
			# newform.form_id = f"{lexeme.id}-F{newforms}"
			# print(newform)
			# lexeme.forms.add(newform)
			# print(str(lexeme.forms))

		# done = False
		# while not done:
		# 	try:
		# 		# print(str(lexeme.get_json()))
		# 		lexeme.write(is_bot=True, clear=True)
		# 		done = True
		# 	except Exception as ex:
		# 		if "404 Client Error" in str(ex):
		# 			print('Got 404 response from wikibase, will wait and try again...')
		# 			time.sleep(10)
		# 		else:
		# 			print('Unexpected error:\n' + str(ex))
		# 			sys.exit()
		#
		# with open('profiles/serbian/serbian_scripts/data/lexeme_mapping.csv', 'a') as mappingcsv:
		# 	mappingcsv.write(lexemeid + '\t' + lexeme.id + '\n')
		# print('Finished processing ' + lexeme.id)

