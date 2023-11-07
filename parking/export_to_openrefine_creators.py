from bots import botconfig, xwbi
import pandas

config = botconfig.load_mapping('config')
creators_xp = "mp:P13|mp:P14"
creators_xps = creators_xp.replace("mp:","mps:")

query = """
PREFIX mwb: <https://monumenta.wikibase.cloud/entity/>
PREFIX mdp: <https://monumenta.wikibase.cloud/prop/direct/>
PREFIX mp: <https://monumenta.wikibase.cloud/prop/>
PREFIX mps: <https://monumenta.wikibase.cloud/prop/statement/>
PREFIX mpq: <https://monumenta.wikibase.cloud/prop/qualifier/>
PREFIX mpr: <https://monumenta.wikibase.cloud/prop/reference/>
PREFIX mno: <https://monumenta.wikibase.cloud/prop/novalue/>

select ?bibItem ?creatorstatement ?listpos ?givenName ?lastName ?fullName 
(?fullName as ?fullName_clusters) 
(?fullName as ?fullName_recon_Wikidata)
(?fullName as ?fullName_recon_Wikibase)
where {
  ?bibItem """+creators_xp+""" ?creatorstatement .
  filter not exists{?bibItem mdp:P14|mdp:P13 ?creatoritem.}
  ?creatorstatement """+creators_xps+""" ?creatoritem.
  ?creatorstatement mpq:"""+config['mapping']['prop_series_ordinal']['wikibase']+""" ?listpos ;
                    mpq:"""+config['mapping']['prop_source_literal']['wikibase']+""" ?fullName .
optional {?creatorstatement mpq:"""+config['mapping']['prop_given_name_source_literal']['wikibase']+""" ?givenName.}
optional {?creatorstatement mpq:"""+config['mapping']['prop_family_name_source_literal']['wikibase']+""" ?lastName .}
   } order by ?lastName ?givenName"""

query_result = xwbi.wbi_helpers.execute_sparql_query(query=query, prefix=config['mapping']['sparql_prefixes'])
data = pandas.DataFrame(columns=query_result['head']['vars'])
# print(data)
for binding in query_result['results']['bindings']:
    pdrow = {}
    for key in binding:
        pdrow[key] = binding[key]['value']
    # print(str(pdrow))
    # data.append(pdrow, ignore_index=True)
    # data.concat(data, pdrow, ignore_index=True)
    data.loc[len(data)] = pdrow

data.to_csv('data/unreconciled_creators/mlv_unrecon.csv', index=False)