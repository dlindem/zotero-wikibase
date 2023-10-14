from bots import xwbi, botconfig
import csv, traceback

zoteromapping = botconfig.load_mapping('zotero')
propertymapping = botconfig.load_mapping('properties')

datatypesmapping = {
    'ExternalId' : 'external-id',
    'WikibaseForm' : 'wikibase-form',
    'GeoShape' : 'geo-shape',
    'GlobeCoordinate' : 'globe-coordinate',
    'WikibaseItem' : 'wikibase-item',
    'WikibaseLexeme' : 'wikibase-lexeme',
    'Math' : 'math',
    'Monolingualtext' : 'monolingualtext',
    'MusicalNotation' : 'musical-notation',
    'WikibaseProperty' : 'wikibase-property',
    'Quantity' : 'quantity',
    'WikibaseSense' : 'wikibase-sense',
    'String' : 'string',
    'TabularData' : 'tabular-data',
    'Time' : 'time',
    'Url' : 'url'
}

# load props.csv

with open('zotero-wikibase-props.csv', 'r', encoding="utf-8") as file:
	propsdict = csv.DictReader(file)

	for row in propsdict:
		newpropid = None
		print('\nWill process data for '+row['propLabel']+'...')
		if row['existing'].startswith('P'):
			newpropid = row['existing']
		enlabel = row['propLabel'].strip()
		dtype = row['datatype']
		wdpid = row['wikidata_prop'].strip() if row['wikidata_prop'].startswith('P') else None
		# formatterUrl = row['formatterUrl'].strip()
		zoterofield = row['zotero'] if len(row['zotero']) > 1 else None
		if zoterofield:
			print('This property shall map to a Zotero field: '+row['zotero'])

		if not newpropid:
			newprop = xwbi.wbi.property.new(datatype=datatypesmapping[dtype])
			newprop.labels.set('en',enlabel)
			print('enlabel set: '+enlabel)
			if wdpid:
				newprop.claims.add(xwbi.ExternalID(value=wdpid,prop_nr=config['mapping']['prop_wikidata_entity']['wikibase']))
				print('P1 set: '+wdpid)
			# if formatterUrl.startswith('http'):
			# 	newprop.claims.add(xwbi.String(value=formatterUrl,prop_nr=config.formatter_url_prop))
			# 	print('P2 set: '+formatterUrl)
			presskey = input('Press Enter for writing data for '+enlabel)
			d = False
			while d == False:
				try:
					print('Writing to xwb wikibase...')
					r = newprop.write(is_bot=1, clear=False)
					d = True
					newpropid = newprop.id
					print('Successfully written data to item: '+newprop.id)
				except Exception:
					ex = traceback.format_exc()
					print(ex)
					presskey = input('Press key for retry.')

		# write zotero mapping
		if zoterofield:
			for itemtype in zoteromapping['mapping']:
				for field in zoteromapping['mapping'][itemtype]['fields']:
					if field == zoterofield:
						zoteromapping['mapping'][itemtype]['fields'][field]['wbprop'] = newpropid
						zoteromapping['mapping'][itemtype]['fields'][field]['dtype'] = dtype
				for creatortype in zoteromapping['mapping'][itemtype]['creatorTypes']:
					if creatortype == zoterofield:
						zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['wbprop'] = newpropid
						zoteromapping['mapping'][itemtype]['creatorTypes'][creatortype]['dtype'] = dtype
			botconfig.dump_mapping(zoteromapping)

		# write properties mapping
		propertymapping['mapping'][newpropid] = {
			'enlabel': enlabel,
			'type': dtype,
			'wdprop': wdpid
		}
		botconfig.dump_mapping(propertymapping)