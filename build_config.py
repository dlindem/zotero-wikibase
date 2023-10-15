from bots import botconfig
import re

config = botconfig.load_mapping('config')

if config['mapping']['wikibase_url']:
    wikibase_url = config['mapping']['wikibase_url']
    config['mapping']['wikibase_site'] = re.sub(r'https?://', '', wikibase_url)
    config['mapping']['wikibase_entity_ns'] = wikibase_url + "/entity/"
    config['mapping']['wikibase_api_url'] = wikibase_url + "/w/api.php"
    config['mapping']['wikibase_sparql_endpoint'] = wikibase_url + "/query/sparql"
    config['mapping']['sparql_prefixes'] = ('\n').join([
        "PREFIX xwb: <" + wikibase_url + "/entity/>",
        "PREFIX xdp: <" + wikibase_url + "/prop/direct/>",
        "PREFIX xp: <" + wikibase_url + "/prop/>",
        "PREFIX xps: <" + wikibase_url + "/prop/statement/>",
        "PREFIX xpq: <" + wikibase_url + "/prop/qualifier/>",
        "PREFIX xpr: <" + wikibase_url + "/prop/reference/>",
        "PREFIX xno: <" + wikibase_url + "/prop/novalue/>"
    ])+'\n'

botconfig.dump_mapping(config)
