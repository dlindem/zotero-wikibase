import editdistance, sys, os, pandas
# sys.path.insert(1, os.path.realpath(os.path.pardir))
# os.chdir(os.path.realpath(os.path.pardir))
from bots import botconfig #, zotwb_functions
from flask import Flask, render_template, request
import os, re, json
from datetime import datetime

pandas.set_option('display.max_rows', 1000)
pandas.set_option('display.max_columns', 1000)
pandas.set_option('display.width', 1000)


def suggest(dic, word, maxdist=4):
   outdic = {}
   for i in range(maxdist+1):
      outdic[i]=[]
   for dicentry in dic:
      dist = editdistance.eval(word, dicentry['form'])
      if dist <= maxdist:
         outdic[dist].append(dicentry)
   return outdic

with open('profiles/serbian/data/SRP18520_wikibase.csv', 'r') as csvfile:
    corpus = pandas.read_csv(csvfile)
    corpus.offset_index = corpus.offset_index.astype(int)
    corpus = corpus.sort_values('offset_index')
    corpus = corpus.reset_index(drop=True)
    # print(corpus)


# from flask_wtf import FlaskForm
app = Flask(__name__)
profile = "serbian" # zotwb config profile

@app.route('/dictionary_linking', methods= ['GET', 'POST'])
def dictionary_linking():
    messages = []
    msgcolor = None
    annotation_index = 5
    context_index = []
    i = annotation_index-5
    while i <= annotation_index+5:
        if i >= 0:
            context_index.append(i)
    context = corpus.loc[context_index]
    print(context)






    if request.method == 'GET':
        return render_template("dictionary_linking.html",
                               messages=messages, msgcolor=msgcolor)

    elif request.method == 'POST':
        if request.form:
            for key in request.form:
                print(key, request.form.get(key))
                # if key == 'create_new_profile':
                #     newprofile = request.form.get(key)
                #     action = zotwb_functions.create_profile(name=newprofile)
                #     messages = action['messages']
                #     msgcolor = action['msgcolor']
                # elif key.startswith('activate_'):
                #     profile = key.replace('activate_','')
                #     message = f"This profile will be activated: {profile}."
                #     print(message)
                #     with open('profiles.json', 'w', encoding='utf-8') as file:
                #         json.dump({'last_profile':profile,'profiles_list':[profiles['last_profile']]+other_profiles}, file, indent=2)
                #     messages.append(message + ' Quit and restart ZotWb and go to <a href="/">ZotWb start page</a>.')
                #     msgcolor="background:limegreen"

            return render_template("dictionary_linking.html",
                               messages=messages, msgcolor=msgcolor)





# dic = [{'form':"kaixxo",'lemma':'kaixo','fid':'L1-F1'},
#        {'form':"laixxooo",'lemma':'kaixo','fid':'L1-F2'},
#        {'form':"kaixooooo",'lemma':'kaixo','fid':'L1-F3'},
#        {'form':"kaixo",'lemma':'kaixo','fid':'L1-F4'}]
# word = "kaixo"
# suggestions = suggest(dic=dic, word=word)
# print(str(suggestions))

if __name__ == '__main__':
    app.run(debug=True)