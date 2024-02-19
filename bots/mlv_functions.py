import csv, re, json
from bots import xwbi, botconfig

def load_text(docqid=None, start_prg=1, end_prg=0, span_start=0, span_end=0):
    if span_end == 0:
        span_end = None
    colors = "#800000 #FF0000 #800080 #FF00FF #008000 #00FF00 #808000 #FFFF00 #000080 #0000FF #008080 #00FFFF".split(" ")

    with open(f'profiles/MLV/data/text_cache/{docqid}_span.json', 'r') as jsonfile:
        data = json.load(jsonfile)
        spandata = {'spans':{}, 'tokens':{}}
        spancount = 0
        for row in data:
            spanqid = row['span']['value'].replace('https://monumenta.wikibase.cloud/entity/','')
            tokens = row['span_tokenak']['value'].split(' ')
            spandata['spans'][spanqid] = {'color': colors[spancount],'tokens':tokens, 'data':row}
            for token in tokens:
                if token not in spandata['tokens']:
                    spandata['tokens'][token] = [row['span']['value']]
                else:
                    spandata['tokens'][token].append(row['span']['value'])
            spancount += 1
            if spancount == len(colors):
                spancount = 0


    with open(f'profiles/MLV/data/text_cache/{docqid}_token.json', 'r') as jsonfile:
        data = json.load(jsonfile)
        lastpar = 0
        docdata = []
        prgdata = None
        no_sp_before = True
        for row in data:
            prgnum = int(row['wikisource_paragraph']['value'][-1])
            if prgnum + 1 <= start_prg:
                continue  # start_prg: user has chosen to skip some paragraphs
            if end_prg != 0 and prgnum >= end_prg:
                continue  # if end_prg is set and reached
            row['token_int'] = float(row['token_zbk']['value'])
            if row['token_int'] < span_start:
                continue
            if span_end:
                if row['token_int']['value'] > span_end:
                    break

            row['qid'] = row['token']['value'].replace('https://monumenta.wikibase.cloud/entity/','')
            if 'mlv_lexema' in row:
                row['mlv_lexema'] = row['mlv_lexema']['value'].replace('https://monumenta.wikibase.cloud/entity/','')
            else:
                row['mlv_lexema'] = ""
            if row['qid'] in spandata['tokens']: # TODO: if token is in more than 1 span (takes now span-id of first span in list)
                spanqid = spandata['tokens'][row['qid']][0].replace('https://monumenta.wikibase.cloud/entity/','')
                row['color'] = spandata['spans'][spanqid]['color']
                row['span'] = spandata['tokens'][row['qid']][0]
                row['spanqid'] = spanqid
            else:
                row['color'] = "#000000" # black
            if no_sp_before:
                row['sp_before'] = ""
                no_sp_before = False
            else:
                row['sp_before'] = " "

            if prgnum > lastpar: # first token in paragraph: write preceding paragraph data
                if prgdata:
                    docdata.append(prgdata)
                prgdata = {'prgnum':str(prgnum),'tokens':[]}
                lastpar = prgnum
                row['sp_before'] = ""
            else: # subsequent token in same paragraph
                if row['token_forma']['value'] in "(":
                    no_sp_before = True # for next row
                if row['token_forma']['value'] in ",.?!:);":
                    row['sp_before'] = ""

            prgdata['tokens'].append(row)

        docdata.append(prgdata) # last paragraph
    print(str(docdata)[0:5000])
    print(str(spandata))
    messages = [f"{docqid} testua ondo kargatu da."]
    if span_start > 0:
        messages.append(f"Span start: {span_start}. tokena")
    if span_end:
        messages.append(f"Span end: {span_end}. tokena")
    return {'messages':messages, 'msgcolor':'background:limegreen', 'docdata':docdata, 'spandata':spandata}

def create_span(form={}):
    print(str(form))
    spandict = {}
    for key in form:
        if key.startswith('span_include_token_'):
            spandict[key.replace('span_include_token_','')] = form[key]
    print(str(spandict))
    docdata = load_text(docqid=form['span_sortu'], span_start=int(list(spandict.keys())[0]), span_end=int(list(spandict.keys())[-1]))['docdata']
    statements = [{'prop_nr': 'P5', 'type': 'item', 'value': 'Q20'}] # instance of span
    for prg in docdata:
        label = ""
        for token in prg['tokens']:
            ordinal = spandict[token['token_zbk']]
            if ordinal == "0":
                print(f"Skip Token {token['qid']} marked with ordinal 0.")
                continue
            label += token['token_forma'] + ' '
            statements.append({'type': 'item', 'prop_nr':'P30', 'value':token['qid'], 'qualifiers':[{'type':'string','prop_nr':'P32', 'value':ordinal}]})
        itemdata = {'qid':False, 'statements':statements, 'labels':[{'lang': 'eu', 'value': label.rstrip()}], 'descriptions':[{'lang':'eu', 'value': form['span_sortu']+' testuko '+ prg['prgnum'] +'. paragrafoko token andana'}]}
        print(str(itemdata))
        spanqid = xwbi.itemwrite(itemdata)
        messages = [f'Andana sortuta. Anotazioak gehitzeko hona jo: <b><a href="https://monumenta.wikibase.cloud/entity/{spanqid}">{spanqid}</a></b>.']
        messages.append('[Fitxa hau itxi daiteke]')
        return {'messages':messages, 'msgcolor':'background:limegreen'}

def get_token_details(token_qid=None):
    token = xwbi.wbi.item.get(entity_id=token_qid)
    token_forma = token.claims.get('P147')[0].mainsnak.datavalue['value']
    return {'token_positions':list(range(len(token_forma))), 'token_forma':token_forma}

def split_token(token_qid=None, split_position=None):
    left_token = xwbi.wbi.item.get(entity_id=token_qid)
    token_forma = left_token.claims.get('P147')[0].mainsnak.datavalue['value']
    left_token_desc = left_token.descriptions.get('eu').value
    left_token_forma = token_forma[0:split_position]
    right_token_forma = token_forma[split_position:]
    right_next_token = left_token.claims.get('P150')[0].mainsnak.datavalue['value']['id']
    left_token_zbk = left_token.claims.get('P148')[0].mainsnak.datavalue['value']
    right_token_zbk = str(int(left_token_zbk + 0.1))
    right_token_desc = re.sub(left_token_zbk,right_token_zbk,left_token_desc)

    right_token_itemdata = {'qid': False, 'labels':[{'lang':'eu', 'value':right_token_forma}],
                            'descriptions': [{'lang':'eu', 'value': right_token_desc}],
                            'statements': [{'type': 'item', 'prop_nr': 'P5', 'value': 'Q15'},
                                           {'type': 'string', 'prop_nr': 'P147', 'value': right_token_forma},
                                           {'type': 'string', 'prop_nr': 'P148', 'value': right_token_zbk},
                                           {'type': 'item', 'prop_nr': 'P150', 'value': right_next_token},
                                           {'type': 'item', 'prop_nr': 'P28', 'value': left_token.claims.get('P28')[0].mainsnak.datavalue['value']['id']},
                                           {'type': 'externalid', 'prop_nr': 'P177', 'value': left_token.claims.get('P177')[0].mainsnak.datavalue['value']}]
                            }
    right_token_qid = xwbi.itemwrite(right_token_itemdata)
    left_token_itemdata = {'qid': token_qid, 'labels':[{'lang':'eu', 'value':left_token_forma}],
                           'statements': [{'type': 'string', 'prop_nr': 'P147', 'value': left_token_forma, 'action': 'replace'},
                                          {'type': 'item', 'prop_nr': 'P150', 'value': right_token_qid, 'action': 'replace'}]
                           }
    left_token_qid = xwbi.itemwrite(left_token_itemdata)
    return {'messages': ['Tokena banatu egin da.',
                         f'Ezkerreko tokena: <b>"{left_token_forma}"</b>, <a href="https://monumenta.wikibase.cloud/{left_token_qid}" target="_blank">{left_token_qid}</a>"',
                         f'Eskumako tokena: <b>"{right_token_forma}"</b>, <a href="https://monumenta.wikibase.cloud/{right_token_qid}" target="_blank">{right_token_qid}</a>"']}


def sparql_doc(doc_qid=None):
    config = botconfig.load_mapping('config')
    tokenquery = """select ?token ?token_zbk ?token_forma  ?mlv_lexema (iri(concat('http://www.wikidata.org/entity/',?wikidata_sense_id)) as ?wikidata_sense)
        ?wd_pos_label
        (iri(concat('https://eu.wikisource.org/wiki/',?wikisource)) as ?wikisource_paragraph) 
         ?lemma ?sense ?forma (group_concat(?morph_label;SEPARATOR="-") as ?morph_labels) ?pos_label
        (iri(concat('http://www.wikidata.org/entity/',?wd_erref)) as ?wd_ent_erref) 
        (concat(?wd_erref_label," (",?class_label,")") as ?wd_erref_info)
           
        where {
          ?token xdp:P5 xwb:Q15 ;
                xdp:P28 xwb:"""+doc_qid+""";
                xdp:P148 ?token_zbk ;
                xdp:P147 ?token_forma ;
                xdp:P177 ?wikisource ;
          optional { ?token xp:P7 ?lemmanode . ?lemmanode xps:P7 ?mlv_lexema. ?mlv_lexema wikibase:lemma ?lemma .
                    optional {?mlv_lexema xdp:P1 ?wd_qid .}
                    optional {?lemmanode xpq:P155 ?sense_id. ?sense_id skos:definition ?sense; xp:P1 [xps:P1 ?wikidata_sense_id; xpq:P153 ?wd_pos]. ?wd_pos rdfs:label ?wd_pos_label. filter(lang(?wd_pos_label) = "eu")}
                    optional {?lemmanode xpq:P156 ?form_id. ?form_id ontolex:representation ?forma .
                    optional {?form_id xdp:P172 ?morph. ?morph rdfs:label ?morph_label. filter(lang(?morph_label) = "eu")}
                    optional {?form_id xdp:P173 ?pos. ?pos rdfs:label ?pos_label. filter(lang(?pos_label) = "eu")}          
                             }
                   }
          optional { ?token xdp:P178 ?wd_erref .
                   bind(iri(concat(str(wd:),?wd_erref)) as ?item)
                   SERVICE <https://query.wikidata.org/sparql> {
                   select ?item ?wd_erref_label (sample(?class_l) as ?class_label)
                   where {?item rdfs:label ?wd_erref_label. filter(lang(?wd_erref_label) = "eu")
                          ?item wdt:P31/rdfs:label|wdt:P279/rdfs:label ?class_l. filter(lang(?class_l) = "eu")}
                       group by ?item ?wd_erref_label ?class_label    
                        }          
                   }
        } group by ?token ?token_zbk ?token_forma ?mlv_lexema ?wikidata_sense_id ?wd_pos_label ?wikisource ?lemma ?sense ?forma ?morph_labels ?pos_label ?wd_erref ?wd_erref_label ?class_label
        order by xsd:float(?token_zbk)"""

    spanquery = """select 
        ?span 
        (group_concat(strafter(str(?token),str(xwb:))) as ?span_tokenak)
        ?span_label
        (group_concat(?num_forma) as ?span_formak) 
        (iri(concat('https://eu.wikisource.org/wiki/',sample(?wikisource))) as ?wikisource_paragraph)
        (iri(concat('http://www.wikidata.org/entity/',?wd_erref)) as ?wd_ent_erref) 
        (concat(?wd_erref_label," (",?class_label,")") as ?wd_erref_info)
        ?phil_anot ?quote_anot ?quote_wb_erref (iri(concat('http://www.wikidata.org/entity/',?quote_wd_erref)) as ?quote_wikidata_erref) 
        
        where {
        ?token xdp:P28 xwb:"""+doc_qid+""".
        ?span xdp:P5 xwb:Q20; 
               xp:P30 [xps:P30 ?token; xpq:P32 ?ord];
               rdfs:label ?span_label. filter(lang(?span_label) = "eu")
         ?token xdp:P147 ?token_forma . bind (concat(?ord,":",?token_forma) as ?num_forma)  
         ?token xdp:P177 ?wikisource .
          optional{?span xdp:P178 ?wd_erref .
                   bind(iri(concat(str(wd:),?wd_erref)) as ?item)
                   SERVICE <https://query.wikidata.org/sparql> {
                   select ?item ?wd_erref_label (sample(?class_l) as ?class_label)
                   where {?item rdfs:label ?wd_erref_label. filter(lang(?wd_erref_label) = "eu")
                          ?item wdt:P31/rdfs:label ?class_l. filter(lang(?class_l) = "eu")}
                       group by ?item ?wd_erref_label ?class_label    
                        }          
                   }
          optional{?span xp:P180 ?philst . ?philst xps:P180 ?phil_anot .
                  }
          optional{?span xp:P164 ?quotest . ?quotest xps:P164 ?quote_anot .
                   optional {?quotest xpq:P67 ?quote_wb_erref.}
                   optional {?quotest xpq:P178 ?quote_wd_erref.}
                  }
             
         } group by ?span ?span_tokenak ?span_label ?span_formak ?wd_erref ?wd_erref_label ?class_label ?phil_anot ?quote_anot ?quote_wb_erref ?quote_wd_erref"""

    print("Waiting for tokens from SPARQL...")
    bindings = \
    xwbi.wbi_helpers.execute_sparql_query(query=tokenquery, prefix=config['mapping']['wikibase_sparql_prefixes'])['results'][
        'bindings']
    print('Found ' + str(len(bindings)) + ' results to process.\n')
    with open(f'profiles/MLV/data/text_cache/{doc_qid}_token.json', 'w', encoding="utf-8") as jsonfile:
        json.dump(bindings, jsonfile, indent=2)

    print("Waiting for spans from SPARQL...")
    bindings = \
        xwbi.wbi_helpers.execute_sparql_query(query=spanquery, prefix=config['mapping']['wikibase_sparql_prefixes'])[
            'results'][
            'bindings']
    print('Found ' + str(len(bindings)) + ' results to process.\n')
    with open(f'profiles/MLV/data/text_cache/{doc_qid}_span.json', 'w', encoding="utf-8") as jsonfile:
        json.dump(bindings, jsonfile, indent=2)
    return {'messages':[f'Arrakasta {doc_qid} testua Wikibasetik SPARQL bidez hartu eta gordetzean.']}