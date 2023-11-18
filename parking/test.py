from bots import xwb
import json

claimid = "Q315$FEC1D39A-9B58-4B00-B715-B39FC7AA1E85"
print(xwb.setqualifier(qid="Q315", prop="P15", claimid=claimid, qualiprop="P178", qualio="Q65", dtype="externalid", replace=True))


# claimid = "Q315$FEC1D39A-9B58-4B00-B715-B39FC7AA1E85"
# item = xwbi.wbi.item.get(entity_id="Q315")
# data = item.get_json()
# print(data)

# with open('parking/test.json', 'r') as file:
#     #json.dump(data, file, indent=2)
#     data = json.load(file)
#
#     print(data['claims']['P15'])
#     data['claims']['P15'][0]['qualifiers']['P178'][0]['datavalue']['value'] = "Q1"
#     print(data['claims']['P15'])
#
# newitem = xwbi.wbi.item().from_json(data)
#
# print(newitem.id)

# claims = item.claims.claims
# new_claims = {}
# for prop_id, claim_list in claims.items():
#     for claim in claim_list:
#         print(claim)
#         if claim.id == claimid:
#
#             claimdict = claim.get_json()
#             print(claimdict)
#             claimdict['qualifiers'] = {
#               "P178": [
#                 {
#                   "snaktype": "value",
#                   "property": "P178",
#                   "datatype": "external-id",
#                   "datavalue": {
#                     "value": "Q1",
#                     "type": "string"
#                   }
#                 }
#               ]
#             }