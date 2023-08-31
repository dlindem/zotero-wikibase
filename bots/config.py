import json

# essential properties, to be defined here manually:
prop_wikidata_entity = "P1" # externalId-prop for "Wikidata entity"
prop_instanceof = "P5" # datatype WikibaseItem, Wikidata P31
prop_subclassof = "P4" # datatype WikibaseItem, Wikidata P279
prop_formatterurl = "P2" # datatype String, Wikidata P1630
prop_formatterurirdf = "P3" # datatype String, Wikidata P1921
prop_inverseprop = "P73" # datatype Property, Wikidata P1696
prop_series_ordinal = "P32" # datatype String, Wikidata P1545, used e.g. in crator statements
prop_source_literal = "P36" # datatype String, used as qualifier, e.g. in creator statements
prop_given_name_source_literal = "P38" # datatype String, used as qualifier in creator statements
prop_family_name_source_literal = "P39" # datatype String, used as qualifier in creator statements
# essential ontology classes, to be defined here manually:
class_bibitem = "Q4" # bibliographical records
class_bibitem_type = "Q6" # bibliographical item type (journal article, etc.)
class_creator_role = "" # creator roles (e.g. author, translator)
class_journal = "" # periodicals
class_language = "" # natural languages
class_ontology_class = "Q1" # class that groups all ontology classes
class_organization = "" # organizations (can be creators, publishers,...)
class_person = "Q5" # natural persons (humans)

# wb_bot_user and wb_bot_pwd are stored in config.private.py

# config related to Zotero:

zotero_group_id = 1892855 # integer not string
zotero_export_tag = "wikibase-export" # exact form of the Zotero tag you use for marking records to be exported
# zotero_api_key is stored in config.private.py

# config related to the wikibase to connect to

wikibase_url = 'https://monumenta.wikibase.cloud'
entity_ns = "https://monumenta.wikibase.cloud/entity/"
api_url = 'https://monumenta.wikibase.cloud/w/api.php'
sparql_endpoint = 'https://monumenta.wikibase.cloud/query/sparql'
sparql_prefixes = """
PREFIX xwb: <https://monumenta.wikibase.cloud/entity/>
PREFIX xdp: <https://monumenta.wikibase.cloud/prop/direct/>
PREFIX xp: <https://monumenta.wikibase.cloud/prop/>
PREFIX xps: <https://monumenta.wikibase.cloud/prop/statement/>
PREFIX xpq: <https://monumenta.wikibase.cloud/prop/qualifier/>
PREFIX xpr: <https://monumenta.wikibase.cloud/prop/reference/>
PREFIX xno: <https://monumenta.wikibase.cloud/prop/novalue/>

"""
label_languages = "eu es en de fr".split(" ") # two-letter wiki language codes of those you want to have labels and descriptions (e.g. when importing from Wikidata)
store_qid_in_extra = True # if set True, Wikibase BibItem Qid will be stored in the Zotero item's EXTRA field (otherwise, set to False)
store_qid_in_attachment = True # if set True, a URI attachment will be created for the Zotero item, leading to the Wikibase entity

# DO NOT EDIT THE FOLLOWING SECTIONS
# import mappings
def load_mapping(mappingname):
    print(f"Will load mapping: {mappingname}.json")
    with open(f"bots/mappings/{mappingname}.json", 'r', encoding='utf-8') as jsonfile:
        return json.load(jsonfile)
def dump_mapping(mappingjson):
    print(f"Will dump mapping: {mappingjson['filename']}")
    with open(f"bots/mappings/{mappingjson['filename']}", 'w', encoding='utf-8') as jsonfile:
        json.dump(mappingjson, jsonfile, indent=2)

# bot functions for the datatypes greyed out are not implemented
datatypes_mapping = {
    'ExternalId' : 'external-id',
    'WikibaseForm' : 'wikibase-form',
 #   'GeoShape' : 'geo-shape',
    'GlobeCoordinate' : 'globe-coordinate',
    'WikibaseItem' : 'wikibase-item',
    'WikibaseLexeme' : 'wikibase-lexeme',
 #   'Math' : 'math',
    'Monolingualtext' : 'monolingualtext',
 #   'MusicalNotation' : 'musical-notation',
    'WikibaseProperty' : 'wikibase-property',
 #   'Quantity' : 'quantity',
    'WikibaseSense' : 'wikibase-sense',
    'String' : 'string',
 #   'TabularData' : 'tabular-data',
    'Time' : 'time',
    'Url' : 'url'
}