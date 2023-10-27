import json
import os
botpath = os.path.realpath('bots')
#
# with open('bots/mappings/config.json', 'r', encoding="utf-8") as configfile:
#     config = json.load(configfile)

# config related to the wikibase to connect to
# wikibase_name = config['mapping']['wikibase_name']
# wikibase_url = config['mapping']['wikibase_url']
# wikibase_entity_ns = wikibase_url + "/entity/"
# api_url = wikibase_url + "/w/api.php"
# sparql_endpoint = wikibase_url + "/query/sparql"
# sparql_prefixes = join('\n').[
#     "PREFIX xwb: <" + wikibase_url + "/entity/>",
#     "PREFIX xdp: <" + wikibase_url + "/prop/direct/>",
#     "PREFIX xp: <" + wikibase_url + "/prop/>",
#     "PREFIX xps: <" + wikibase_url + "/prop/statement/>",
#     "PREFIX xpq: <" + wikibase_url + "/prop/qualifier/>",
#     "PREFIX xpr: <" + wikibase_url + "/prop/reference/>",
#     "PREFIX xno: <" + wikibase_url + "/prop/novalue/>"
# ]

# store_qid_in_extra = True  # if set True, Wikibase BibItem Qid will be stored in the Zotero item's EXTRA field (otherwise, set to False)
# store_qid_in_attachment = True  # if set True, a URI attachment will be created for the Zotero item, leading to the Wikibase entity
#
# label_languages = config['mapping']['wikibase_label_languages']
# # essential properties, to be defined by the user in the GUI (choices are saved in config.json)
# prop_wikidata_entity = config['mapping']['prop_wikidata_entity']['wikibase']  # externalId-prop for "Wikidata entity"
# prop_zotero_item = config['mapping'][
#     'prop_zotero_item']  # externalId-prop for linking items to your Zotero group collection. formatter URL will be "https://www.zotero.org/groups/[group_num]/[group_name]/items/$1/item-details"
# prop_zotero_PDF = config['mapping'][
#     'prop_zotero_PDF']  # externalId-prop for linking items to its full text PDF stored as Zotero attachment. formatter URL will be "https://www.zotero.org/groups/[group_num]/[group_name]/items/$1/item-details"
# prop_instanceof = config['mapping']['prop_instance_of']['wikibase']  # datatype WikibaseItem, Wikidata P31
# prop_itemtype = config['mapping'][
#     'prop_itemtype']  # datatype WikibaseItem, bibliographical item type (used for pointing to the Zotero item type, e.g. 'journal article')
# prop_formatterurl = config['mapping']['prop_formatterurl']['wikibase']  # datatype String, Wikidata P1630
# prop_formatterurirdf = config['mapping']['prop_formatterurirdf']['wikibase']  # datatype String, Wikidata P1921
# prop_inverseprop = config['mapping']['prop_inverseprop']['wikibase']  # datatype Property, Wikidata P1696
# prop_series_ordinal = config['mapping'][
#     'prop_series_ordinal']  # datatype String, Wikidata P1545, used e.g. in crator statements
# prop_source_literal = config['mapping'][
#     'prop_source_literal']  # datatype String, used as qualifier, e.g. in creator statements
# prop_given_name_source_literal = config['mapping'][
#     'prop_given_name_source_literal']  # datatype String, used as qualifier in creator statements
# prop_family_name_source_literal = config['mapping'][
#     'prop_family_name_source_literal']  # datatype String, used as qualifier in creator statements
# prop_isbn_10 = config['mapping'][
#     'prop_isbn_10']  # datatype ExternalId, Wikidata P967. Used for 10-digit-ISBN identifiers. Most conveniently with formatter URL "https://worldcat.org/isbn/$1"
# prop_isbn_13 = config['mapping'][
#     'prop_isbn_13']  # datatype ExternalId, Wikidata P212. Used for 13-digit-ISBN identifiers. Most conveniently with formatter URL "https://worldcat.org/isbn/$1"
# prop_wikidata_sitelinks = config['mapping']['prop_wikidata_sitelinks']['wikibase']  # datatype URL, for Wikipedia sitelinks from Wikidata
# # essential ontology classes, to be defined here manually:
# class_bibitem = config['mapping']['class_bibitem']['wikibase']  # bibliographical records
# class_bibitem_type = config['mapping']['class_bibitem_type']['wikibase']  # bibliographical item type (journal article, book, etc.)
# class_creator_role = config['mapping']['class_creator_role']['wikibase']  # creator role properties (e.g. author, translator)
# class_journal = config['mapping']['class_journal']['wikibase']  # periodicals
# class_language = config['mapping']['class_language']['wikibase']  # natural languages
# class_ontology_class = config['mapping']['class_ontology_class']['wikibase']  # class that groups all ontology classes
# class_organization = config['mapping']['class_organization']['wikibase']  # organizations (can be creators, publishers,...)
# class_person = config['mapping']['class_person']['wikibase']  # natural persons (humans)
# # regex patterns for identifiers found in Zotero EXTRA field (e.g. Worldcat stores OCLC identifiers there; other use cases are PMID, etc.)
# # In this dictionary, keys are the patterns, values are the Wikibase ExternalId properties to map the identifier to.
# identifier_patterns = {
#     r"^OCLC: ([0-9]+)": "P55"  # the OCLC property should have as formatter URL: "https://worldcat.org/oclc/$1"
# }
#
# # wb_bot_user and wb_bot_pwd are stored in config.private.py
#
# # config related to Zotero:
#
# zotero_group_id = config['mapping']['zotero_group_id']  # integer not string
# zotero_export_tag = config['mapping'][
#     'zotero_export_tag']  # exact form of the Zotero tag you use for marking records to be exported
# zotero_on_wikibase_tag = config['mapping'][
#     'zotero_on_wikibase_tag']  # form of the Zotero tag written to successfully exported items
#

# zotero_api_key is stored in config.private.py


# DO NOT EDIT THE FOLLOWING SECTIONS
# import mappings
def load_mapping(mappingname):
    # print(f"Will load mapping: {mappingname}.json")
    with open(f"{botpath}/mappings/{mappingname}.json", 'r', encoding='utf-8') as jsonfile:
        return json.load(jsonfile)


def dump_mapping(mappingjson):
    print(f"Will dump mapping: {mappingjson['filename']}")
    with open(f"{botpath}/mappings/{mappingjson['filename']}", 'w', encoding='utf-8') as jsonfile:
        json.dump(mappingjson, jsonfile, indent=2)


# bot functions for the datatypes greyed out are not implemented
datatypes_mapping = {
    'ExternalId': 'external-id',
    'WikibaseForm': 'wikibase-form',
    #   'GeoShape' : 'geo-shape',
    'GlobeCoordinate': 'globe-coordinate',
    'WikibaseItem': 'wikibase-item',
    'WikibaseLexeme': 'wikibase-lexeme',
    #   'Math' : 'math',
    'Monolingualtext': 'monolingualtext',
    #   'MusicalNotation' : 'musical-notation',
    'WikibaseProperty': 'wikibase-property',
    #   'Quantity' : 'quantity',
    'WikibaseSense': 'wikibase-sense',
    'String': 'string',
    #   'TabularData' : 'tabular-data',
    'Time': 'time',
    'Url': 'url'
}
