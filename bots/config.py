
prop_instanceof = "" # Wikidata P31
prop_subclassof = "" # Wikidata P279
prop_formatterurl = "" # Wikidata P1630
prop_formtterurirdf = "" # Wikidata
prop_inverseprop = "" # Wikidata P1696

# config related to Zotero:

zotero_group_id = 1892855 # integer not string
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
PREFIX wikibase: <http://wikiba.se/ontology#>

"""
wikidata_entity_prop = "P1" # to define manually here: externalId-prop for "Wikidata entity"
formatter_url_prop = "P2" # to define manually here: String-prop for "Formatter URL"
formatter_uri_prop = "P3" # to define manually here: String-prop for "Formatter URI for RDF resource"
# wb_bot_user and wb_bot_pwd are stored in config.private.py

# import mappings
def load_mapping(mappingname):
    with open(f"mappings/{mappingname}.json", 'r', encoding='utf-8') as jsonfile:
        return json.load(mappingfile)
def dump_mapping(mappingjson):
    with open(f"mappings/{mappingjson['filename']}", 'w', encoding='utf-8') as jsonfile:
        json.dump(mappingjson, jsonfile, indent=2)