
prop_instanceof = "" # Wikidata P31
prop_subclassof = "" # Wikidata P279
prop_formatterurl = "" # Wikidata P1630
prop_formtterurirdf = "" # Wikidata
prop_inverseprop = "" # Wikidata 1696

# config related to the wikibase to connect to

wikibase_url = 'https://lexbib.elex.is'
entity_ns = "https://monumenta.wikibase.cloud/entity/"
api_url = 'https://lexbib.elex.is/w/api.php'
sparql_endpoint = 'https://lexbib.elex.is/query/sparql'
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
