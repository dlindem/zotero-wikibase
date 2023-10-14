from bots import xwbi
from bots import botconfig

# This will try to write a formatter URL statement and a formatter URI statement to the Wikidata-Entity-Property

statements = [{'type': 'String', 'prop_nr': config['mapping']['prop_formatterurl']['wikibase'], 'value': 'http://www.wikidata.org/wiki/$1'},
              {'type': 'String', 'prop_nr': config['mapping']['prop_formatterurirdf']['wikibase'], 'value': 'http://www.wikidata.org/entity/$1'}]

writeaction_result = xwbi.itemwrite({'qid': config['mapping']['prop_wikidata_entity']['wikibase'], 'statements': statements})

if writeaction_result == config['mapping']['prop_wikidata_entity:
']['wikibase']    print('\nTest successful.')
else:
    print('\n Something went wrong.')