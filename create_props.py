from bots import xwbi, config
import csv, traceback

datatype = {
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

with open('data/props.csv', 'r', encoding="utf-8") as file:
	propsdict = csv.DictReader(file)
	newprops = {}
	for row in propsdict:
		plannedqid = row['prop'].strip()
		print('\nWill process data for '+plannedqid+'...')
		enlabel = row['propLabel'].strip()
		dtype = datatype[row['datatype']]
		wdpid = row['wd'].strip()
		formatterUrl = row['formatterUrl'].strip()
		newprop = xwbi.wbi.property.new(datatype=dtype)
		newprop.labels.set('en',enlabel)
		print('enlabel set: '+enlabel)
		if wdpid.startswith("P"):
			newprop.claims.add(xwbi.ExternalID(value=wdpid,prop_nr=config.wikidata_entity_prop))
			print('P1 set: '+wdpid)
		if formatterUrl.startswith('http'):
			newprop.claims.add(xwbi.String(value=formatterUrl,prop_nr=config.formatter_url_prop))
			print('P2 set: '+formatterUrl)
		presskey = input('Press Enter for writing data for '+plannedqid)
		d = False
		while d == False:
			try:
				print('Writing to xwb wikibase...')
				r = newprop.write(is_bot=1, clear=False)
				d = True
				print('Successfully written data to item: '+newprop.id)
			except Exception:
				ex = traceback.format_exc()
				print(ex)
				presskey = input('Press key for retry.')
