import sys, os, time, csv, re

from bots import xwbi

# PREFIX nif: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#>
# PREFIX ontolex: <http://www.w3.org/ns/lemon/ontolex#>
# PREFIX lex: <http://purl.org/lex#>
# PREFIX olia: <http://purl.org/olia/olia.owl#>
# PREFIX lexinfo: <http://www.lexinfo.net/ontology/2.0/lexinfo#>
# PREFIX eltec: <http://llod.jerteh.rs/ELTEC/srp/NIF2/>
# select   *
# where  {
#   ?token a nif:Word; nif:referenceContext eltec:SRP18520.txt; nif:lemma ?lemma .
#   optional {?token nif:beginIndex ?beginIndex.}
#   optional {?token nif:endIndex ?endIndex.}
#   optional {?token nif:previousWord ?previousWord.}
#   optional {?token nif:nextWord ?nextWord.}
#
# }
#
# http://fuseki.jerteh.rs/#/dataset/SrpELTeC-V2-1000/query?query=PREFIX%20nif%3A%20%3Chttp%3A%2F%2Fpersistence.uni-leipzig.org%2Fnlp2rdf%2Fontologies%2Fnif-core%23%3E%0APREFIX%20ontolex%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2Fns%2Flemon%2Fontolex%23%3E%0APREFIX%20lex%3A%20%3Chttp%3A%2F%2Fpurl.org%2Flex%23%3E%0APREFIX%20olia%3A%20%3Chttp%3A%2F%2Fpurl.org%2Folia%2Folia.owl%23%3E%0APREFIX%20lexinfo%3A%20%3Chttp%3A%2F%2Fwww.lexinfo.net%2Fontology%2F2.0%2Flexinfo%23%3E%0APREFIX%20eltec%3A%20%3Chttp%3A%2F%2Fllod.jerteh.rs%2FELTEC%2Fsrp%2FNIF2%2F%3E%0Aselect%20%20%20%2A%0Awhere%20%20%7B%0A%20%20%3Ftoken%20a%20nif%3AWord%3B%20nif%3AreferenceContext%20eltec%3ASRP18520.txt%3B%20nif%3Alemma%20%3Flemma%20.%0A%20%20optional%20%7B%3Ftoken%20nif%3AbeginIndex%20%3FbeginIndex.%7D%0A%20%20optional%20%7B%3Ftoken%20nif%3AendIndex%20%3FendIndex.%7D%0A%20%20optional%20%7B%3Ftoken%20nif%3ApreviousWord%20%3FpreviousWord.%7D%0A%20%20optional%20%7B%3Ftoken%20nif%3AnextWord%20%3FnextWord.%7D%0A%20%0A%7D
#


# oliacats = {}
# oliacats_raw = [{"oliacat":"https://serbian.wikibase.cloud/entity/Q21","oliacatLabel":"Numeral","rdf":"http://purl.org/olia/olia.owl#Numeral"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q22","oliacatLabel":"Verb","rdf":"http://purl.org/olia/olia.owl#Verb"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q23","oliacatLabel":"Punctuation","rdf":"http://purl.org/olia/olia.owl#Punctuation"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q24","oliacatLabel":"Coordinating Conjunction","rdf":"http://purl.org/olia/olia.owl#CoordinatingConjunction"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q25","oliacatLabel":"Residual","rdf":"http://purl.org/olia/olia.owl#Residual"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q26","oliacatLabel":"Determiner","rdf":"http://purl.org/olia/olia.owl#Determiner"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q27","oliacatLabel":"Proper Noun","rdf":"http://purl.org/olia/olia.owl#ProperNoun"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q28","oliacatLabel":"Adverb","rdf":"http://purl.org/olia/olia.owl#Adverb"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q29","oliacatLabel":"Common Noun","rdf":"http://purl.org/olia/olia.owl#CommonNoun"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q30","oliacatLabel":"Adposition","rdf":"http://purl.org/olia/olia.owl#Adposition"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q31","oliacatLabel":"Adjective","rdf":"http://purl.org/olia/olia.owl#Adjective"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q32","oliacatLabel":"Interjection","rdf":"http://purl.org/olia/olia.owl#Interjection"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q33","oliacatLabel":"Pronoun","rdf":"http://purl.org/olia/olia.owl#Pronoun"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q34","oliacatLabel":"Subordinating Conjunction","rdf":"http://purl.org/olia/olia.owl#SubordinatingConjunction"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q35","oliacatLabel":"Auxiliary Verb","rdf":"http://purl.org/olia/olia.owl#AuxiliaryVerb"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q36","oliacatLabel":"Particle","rdf":"http://purl.org/olia/olia.owl#Particle"}]
# for entry in oliacats_raw:
#     oliacats[entry['rdf']] = entry['oliacat'].replace('https://serbian.wikibase.cloud/entity/','')

with open('profiles/serbian/data/token_mapping.csv', 'r', encoding="utf-8") as logfile:
    logrows = logfile.read().split('\n')
    done_items = {}
    for row in logrows:
        splitrow = row.split('\t')
        try:
            done_items[splitrow[0]] = splitrow[1]
        except:
            pass

# load item mappings from file
with open('profiles/serbian/data/SRP18520_2.csv') as csvfile:
    rows = csv.DictReader(csvfile, delimiter=",") # word,anchor,oliacat
    count = 0

    for row in rows:
        count += 1

        tokenid = row['token'].replace('http://llod.jerteh.rs/ELTEC/srp/NIF2/', '')
        if tokenid in done_items:
            wbqid = done_items[tokenid]
            print(f"{tokenid} is there as {wbqid}")
        else:
            input(f"error: {tokenid} is NOT there!!")
            continue
        print(f"\n[{count}] Will write this to Wikibase:")

        statements = [{'prop_nr': 'P17', 'type': 'string', 'value': row['lemma']}] # lemma string

        if len(row['beginIndex'])>0:
            statements.append({'prop_nr': 'P15', 'type': 'string', 'value': row['beginIndex']})
        if len(row['endIndex'])>0:
            statements.append({'prop_nr': 'P16', 'type': 'string', 'value': row['endIndex']})
        if len(row['previousWord']) > 0:
            previousId = done_items[row['previousWord'].replace('http://llod.jerteh.rs/ELTEC/srp/NIF2/', '')]
            statements.append({'prop_nr': 'P19', 'type': 'item', 'value': previousId})
        if len(row['nextWord']) > 0:
            nextId = done_items[row['nextWord'].replace('http://llod.jerteh.rs/ELTEC/srp/NIF2/', '')]
            statements.append({'prop_nr': 'P18', 'type': 'item', 'value': nextId})

        print(f"{statements}\n")
        wbid = xwbi.itemwrite({'qid': wbqid, 'statements':statements})

        print(f"Successfully written data; {tokenid} = {wbid}.")
        time.sleep(0.5)