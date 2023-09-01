import csv, json

with open('wdlangs.csv', encoding="utf-8") as file:
	table = csv.DictReader(file)

	langmapping = {'filename': 'iso-639-3.json', 'mapping':{}}
	for row in table:
		print(str(row))
		langmapping['mapping'][row['iso3']] = {
			'enlabel': row['langLabel'],
			'iso1': row['iso1'] if row['iso1'] != "" else None,
			'wikilang': row['wikilang'] if row['wikilang'] != "" else None,
			'wdqid': row['lang'].replace("http://www.wikidata.org/entity/",""),
			'wbqid': None
		}

with open(langmapping['filename'], 'w', encoding='utf-8') as file:
	json.dump(langmapping, file, indent=2)
