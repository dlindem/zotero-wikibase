import requests, time, re, json
from bots import config
from bots import config_private
from pyzotero import zotero
pyzot = zotero.Zotero(config.zotero_group_id,'group',config_private.zotero_api_key) # Zotero LexBib group

citations_cache = {}
with open('bots/data/citations_cache.jsonl') as jsonlfile:
	jsonl = jsonlfile.read().split('\n')
	for line in jsonl:
		if line.startswith("{"):
			jsonline = json.loads(line)
			citations_cache[jsonline['zotitemid']] = jsonline['citation']

def getcitation(zotitemid):
	global citations_cache
	if zotitemid in citations_cache:
		print(f"Will take citation from cache: {zotitemid}")
		return citations_cache[zotitemid]
	print(f'Will now get citation for Zotero ID {zotitemid}')
	zotapid = 'https://api.zotero.org/groups/'+config.zotero_group_id+'/items/'+zotitemid
	attempts = 0
	while attempts < 5:
		attempts += 1
		params = {'format': 'json', 'include': 'bib', 'linkwrap': 1, 'locale': 'eu_ES', 'style':'modern-language-association'}
		r = requests.get(zotapid, params=params)
		if "200" in str(r):
			zotitem = r.json()
			# print(zotitemid + ': got zotitem data')
			# print(zotitem['bib'])
			bib = re.search('<div class="csl-entry">(.*)</div>', zotitem['bib']).group(1)
			# convert Lexbib link (from "archive location" - needs mla style)
			bib = re.sub(r'https?://lexbib.elex.is/entity/(Q[0-9]+)', r'([[Item:\1|\1]])', bib)
			# convert remaining links
			bib = re.sub(r'<a href="(https?://)([^/]+)([^"]+)">[^<]+</a>', r'[\1\2\3 \2]', bib)
			print(bib)
			citations_cache[zotitemid] = bib
			with open('data/citations_cache.jsonl', 'a', encoding='utf-8') as jsonlfile:
				jsonlfile.write(json.dumps({'zotitemid':zotitemid,'citation':bib})+'\n')
			return(bib)

		if "400" or "404" in str(r):
			print('*** Fatal error: Item ' + zotitemid + ' got ' + str(r) + ', does not exist on Zotero. Will skip.')
			time.sleep(5)
			break
		print('Zotero API GET request failed (' + zotitemid + '), will repeat. Response was ' + str(r))
		time.sleep(2)

# testitem = "HERCJU9P"
# print(getcitation(testitem))

def getzotitem(zotitemid):
	pass

def getexport():
	exportitems = pyzot.items(tag=config.zotero_export_tag)
	return exportitems

def getchildren(zotitemid):
	children = pyzot.children(zotitemid)
	return children

def patch_item(qid=None, zotitem=None, children = []):
	# communicate with Zotero, write Wikibase entity URI to "extra" and attach URI as link attachment

		zotitem['data']['extra'] = config.entity_ns + qid + "\n" + zotitem['data']['extra']
		pyzot.update_item(zotitem)
		# attempts = 0
		# while attempts < 5:
		# 	attempts += 1
		# 	r = requests.patch(zotapid,
		# 					   headers={"Zotero-API-key": config_private.zotero_api_key},
		# 					   json={"extra": config.entity_ns + qid + "\n" + zotitem['data']['extra'],
		# 							 "version": zotitem['version']})
		#
		# 	if "204" in str(r):
		# 		print('Successfully patched zotero item ' + zotitemid + ': ' + bibItemQid)
		# 		# with open(config_private.datafolder+'zoteroapi/lwbqid2zotero.csv', 'a', encoding="utf-8") as logfile:
		# 		# 	logfile.write(qid+','+zotitemid+'\n')
		# 		break
		# 	print(
		# 		'Zotero API PATCH request failed (' + zotitemid + ': ' + bibItemQid + '), will repeat. Response was ' + str(
		# 			r) + str(r.content))
		# 	time.sleep(2)
		#
		# if attempts > 4:
		# 	print('Abort after 5 failed attempts.')
		# 	sys.exit()

		# check for presence of link attachment
		linkattachment = False
		for child in children:
			if child['data']['url'].startswith(config.entity_ns):
				if child['data']['url'].endswith(qid):
					print('Correct link attachment already present.')
				else:
					print('Fatal error: Zotero item was linked before to some other Q-id')
			else:


		# attempts = 0
		# while attempts < 5:
		# 	attempts += 1
		# 	r = requests.get(zotapid + "/children")
		# 	if "200" in str(r):
		# 		zotitem = r.json()
		# 		print(zotitemid + ': got zotitem attachment data')
		# 		break
		# 	if "400" or "404" in str(r):
		# 		print(
		# 			'*** Fatal error: Item ' + zotitemid + ' got ' + str(r) + ', does not exist on Zotero. Will skip.')
		# 		time.sleep(5)
		# 		break
		# 	print('Zotero API GET request failed (' + zotitemid + '), will repeat. Response was ' + str(r))
		# 	time.sleep(2)
		#
		# if attempts < 5:
		# 	att_presence = None
		# 	for attachmnt in r.json():
		# 		if 'title' in attachmnt['data']:
		# 			if attachmnt['data']['title'] == "LexBib Linked Data":
		# 				att_presence = True
		# 				break
		#
		# if not att_presence:
			# attach link to wikibase
				attachment = [
					{
						"itemType": "attachment",
						"parentItem": zotitem['data']['key'],
						"linkMode": "linked_url",
						"title": config.wikibase_name,
						"accessDate": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
						"url": config.entity_ns + qid,
						"note": '<p>See this item as linked data at <a href="'+config.wikibase_url+'/wiki/Item:' + qid + '">'+config.entity_ns+ qid + '</a>',
						"tags": [],
						"collections": [],
						"relations": {},
						"contentType": "",
						"charset": ""
					}
				]

				r = requests.post('https://api.zotero.org/groups/'+str(config.zotero_group_id)+'/items',
								  headers={"Zotero-API-key": config_private.zotero_api_key,
										   "Content-Type": "application/json"}, json=attachment)

				if "200" in str(r):
					print(f"Link attachment successfully attached to Zotero item {zotitem['data']['key']}.")



