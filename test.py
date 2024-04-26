from bots import inguma_functions
# from semanticscholar import SemanticScholar
# sch = SemanticScholar()
# from habanero import Crossref
# cr = Crossref()

# doc_qid = "Q35775"
# listbibl = inguma_functions.get_listbibl(doc_qid)
#
# for bibentry in listbibl:
#     alex_results = inguma_functions.get_openalex(doc_qid=doc_qid, bibentry=bibentry)
#     print(alex_results)
#

result = inguma_functions.get_googlebooks(bibtitle="Euskara Alemana Hiztegia")
print(result)