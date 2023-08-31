from bots import xwbi
from bots import config

# This will try to write a formatter URL statement and a formatter URI statement to the Wikidata-Entity-Property

statements = [{'type': 'String', 'prop_nr': config.prop_formatterurl, 'value': 'http://www.wikidata.org/wiki/$1'},
              {'type': 'String', 'prop_nr': config.prop_formatterurirdf, 'value': 'http://www.wikidata.org/entity/$1'}]

writeaction_result = xwbi.itemwrite({'qid': config.prop_wikidata_entity, 'statements': statements})

if writeaction_result == config.prop_wikidata_entity:
    print('\nTest successful.')
else:
    print('\n Something went wrong.')