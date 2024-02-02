import sys, os, time, csv, re

from bots import xwbi

oliacats = {}
oliacats_raw = [{"oliacat":"https://serbian.wikibase.cloud/entity/Q21","oliacatLabel":"Numeral","rdf":"http://purl.org/olia/olia.owl#Numeral"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q22","oliacatLabel":"Verb","rdf":"http://purl.org/olia/olia.owl#Verb"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q23","oliacatLabel":"Punctuation","rdf":"http://purl.org/olia/olia.owl#Punctuation"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q24","oliacatLabel":"Coordinating Conjunction","rdf":"http://purl.org/olia/olia.owl#CoordinatingConjunction"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q25","oliacatLabel":"Residual","rdf":"http://purl.org/olia/olia.owl#Residual"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q26","oliacatLabel":"Determiner","rdf":"http://purl.org/olia/olia.owl#Determiner"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q27","oliacatLabel":"Proper Noun","rdf":"http://purl.org/olia/olia.owl#ProperNoun"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q28","oliacatLabel":"Adverb","rdf":"http://purl.org/olia/olia.owl#Adverb"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q29","oliacatLabel":"Common Noun","rdf":"http://purl.org/olia/olia.owl#CommonNoun"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q30","oliacatLabel":"Adposition","rdf":"http://purl.org/olia/olia.owl#Adposition"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q31","oliacatLabel":"Adjective","rdf":"http://purl.org/olia/olia.owl#Adjective"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q32","oliacatLabel":"Interjection","rdf":"http://purl.org/olia/olia.owl#Interjection"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q33","oliacatLabel":"Pronoun","rdf":"http://purl.org/olia/olia.owl#Pronoun"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q34","oliacatLabel":"Subordinating Conjunction","rdf":"http://purl.org/olia/olia.owl#SubordinatingConjunction"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q35","oliacatLabel":"Auxiliary Verb","rdf":"http://purl.org/olia/olia.owl#AuxiliaryVerb"},{"oliacat":"https://serbian.wikibase.cloud/entity/Q36","oliacatLabel":"Particle","rdf":"http://purl.org/olia/olia.owl#Particle"}]
for entry in oliacats_raw:
    oliacats[entry['rdf']] = entry['oliacat'].replace('https://serbian.wikibase.cloud/entity/','')

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
with open('profiles/serbian/data/SRP18520.csv') as csvfile:
    rows = csv.DictReader(csvfile, delimiter=",")
    count = 0

    for row in rows:
        count += 1

        tokenid = row['word'].replace('http://llod.jerteh.rs/ELTEC/srp/NIF2/', '')
        wbqid = False
        if tokenid in done_items:
            print(f"{tokenid} is already there as {done_items[tokenid]}")
            continue
        print(f"\n[{count}] Will write this to Wikibase:")
        # word,anchor,oliacat

        wb_oliacat = oliacats[row['oliacat']]
        statements = [{'prop_nr': 'P5', 'type': 'item', 'value': 'Q2', 'action': 'replace'}, # instance of Word
                      {'prop_nr': 'P8', 'type': 'string', 'value': row['anchor'], 'action': 'replace'}, # token literal
                      {'prop_nr': 'P10', 'type': 'item', 'value': "Q201", 'action': 'replace'}, # part of doc
                      {'prop_nr': 'P6', 'type': 'externalid', 'value': tokenid, 'action': 'replace'}, # ELTEC word ID
                      {'prop_nr': 'P9', 'type': 'item', 'value': wb_oliacat, 'action': 'replace'}]
        labels = [{'lang': 'sr', 'value': row['anchor']}]
        print(f"{statements}\n")
        wbid = xwbi.itemwrite({'qid': wbqid, 'statements':statements, 'labels':labels})
        with open('profiles/serbian/data/token_mapping.csv', 'a', encoding="utf-8") as logfile:
            logfile.write(f"{tokenid}\t{wbid}\n")
        print(f"Successfully processed {tokenid} as {wbid}.")
        time.sleep(0.5)