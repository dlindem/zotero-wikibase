from bots import xwbi

def p13_to_eudef(config={}, schemeqid=None):
    query = """select ?scheme ?eusterm_item ?p13def 
   where {
  ?eusterm_item xdp:P6 xwb:"""+schemeqid+""". 
  ?eusterm_item xdp:P13 ?p13def. 
  filter not exists {?eusterm_item schema:description ?eusterm_def. filter(lang(?eusterm_def)="eu")}  
 } group by ?scheme ?eusterm_item ?p13def
        """
    print(query)
    query_result = xwbi.wbi_helpers.execute_sparql_query(query=query,
                                                         prefix=config['mapping']['wikibase_sparql_prefixes'])

    for binding in query_result['results']['bindings']:
        wbqid = binding['eusterm_item']['value'].replace(config['mapping']['wikibase_entity_ns'],'')
        eusdef = binding['p13def']['value']
        xwbi.itemwrite({'qid':wbqid,'statements':[],'descriptions':[{'lang':'eu','value':eusdef}]})

    return {'messages':[f"Finished updating {str(len(query_result['results']['bindings']))} items of scheme <a href=\"{config['mapping']['wikibase_entity_ns']}{schemeqid}\", target=\"_blank\">{schemeqid}</a>."],  'msgcolor':'background:limegreen'}

def p8_to_eulabel(config={}, schemeqid=None):
    query = """select ?scheme ?eusterm_item ?eusterm_label ?p8label (group_concat(distinct str(?eusterm_altLabel);SEPARATOR="|") as ?eusterm_altLabels)
   where {
  ?eusterm_item xdp:P6 xwb:"""+schemeqid+""". 
  ?eusterm_item xdp:P8 ?p8label. 
  optional {?eusterm_item rdfs:label ?eusterm_label. filter(lang(?eusterm_label)="eu")}  
  optional {?eusterm_item skos:altLabel ?eusterm_altLabel. filter(lang(?eusterm_altLabel)="eu")}
 } group by ?scheme ?eusterm_item ?eusterm_label ?p8label ?eusterm_altLabels
        """
    print(query)
    query_result = xwbi.wbi_helpers.execute_sparql_query(query=query,
                                                         prefix=config['mapping']['wikibase_sparql_prefixes'])

    for binding in query_result['results']['bindings']:
        wbqid = binding['eusterm_item']['value'].replace(config['mapping']['wikibase_entity_ns'],'')
        newlabel = binding['p8label']['value'].strip()
        if 'eusterm_label' in binding:
            eustermlabel = binding['eusterm_label']['value']
        else:
            eustermlabel=None
        if 'eusterm_altLabels' in binding:
            aliases = binding['eusterm_altLabels']['value'].split('|')
        else:
            aliases = []
        if eustermlabel and newlabel.lower() != eustermlabel.lower():
            aliases.append(eustermlabel)
            newaliases = []
            for alias in aliases:
                newaliases.append({'lang':'eu','value':alias})
            xwbi.itemwrite({'qid':wbqid,'statements':[],'labels':[{'lang':'eu','value':newlabel}], 'aliases':newaliases})
        elif not eustermlabel:
            xwbi.itemwrite({'qid': wbqid, 'statements': [], 'labels': [{'lang': 'eu', 'value': newlabel}]})

    return {'messages':[f"Finished updating {str(len(query_result['results']['bindings']))} items of scheme <a href=\"{config['mapping']['wikibase_entity_ns']}{schemeqid}\", target=\"_blank\">{schemeqid}</a>."],  'msgcolor':'background:limegreen'}

def merge_wd_duplicates(config={}, schemeqid=None):
    query = """select distinct  ?wikibase ?wikibase2 ?wikidata
where { ?item xdp:P6 xwb:"""+schemeqid+"""; xdp:P1 ?wikidata . filter (regex (str(?item), "Q"))
      #  ?item2 xdp:P6 xwb:"""+schemeqid+"""; xdp:P1 ?wikidata . filter (?item2 != ?item)
        ?item2 xdp:P1 ?wikidata . filter (?item2 != ?item)
       #?scheme rdfs:label ?schemeLabel. filter(lang(?schemeLabel)="eu")
       bind (strafter(str(?item), '"""+config['mapping']['wikibase_entity_ns']+"""') as ?wikibase)
       bind (strafter(str(?item2), '"""+config['mapping']['wikibase_entity_ns']+"""') as ?wikibase2)
        } order by  xsd:integer(strafter(?wikibase,"Q"))
        """
    #print(query)
    query_result = xwbi.wbi_helpers.execute_sparql_query(query=query,
                                                         prefix=config['mapping']['wikibase_sparql_prefixes'])
    couples = []
    for binding in query_result['results']['bindings']:
        #print(str(binding))
        couple = sorted([binding['wikibase']['value'],binding['wikibase2']['value']])
        if couple not in couples:
            couples.append(couple)
    for couple in couples:
        print(f"Will merge this couple of duplicates: {str(couple)}")
        xwbi.wbi_helpers.merge_items(from_id=couple[1], to_id=couple[0], login=xwbi.login_instance)
    #print(str(couples))
    return {'messages': [
        f"Finished merging {str(len(couples))} couples with the same P1 statement in scheme <a href=\"{config['mapping']['wikibase_entity_ns']}{schemeqid}\", target=\"_blank\">{schemeqid}</a>."],
            'msgcolor': 'background:limegreen'}
