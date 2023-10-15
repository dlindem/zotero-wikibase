from bots import botconfig, littlehelpers
from flask import Flask, render_template, request
from bots import config_private
# from flask_wtf import FlaskForm
app = Flask(__name__)
properties = botconfig.load_mapping('properties')
zoteromapping = botconfig.load_mapping('zotero')
configdata = botconfig.load_mapping('config')
wikibase_url = config_private.wikibase_url
if configdata['mapping']['wikibase_url'] != wikibase_url:
    print(f"Wikibase URL in config_private.py has changed to {wikibase_url}... Will update dependent configurations.")
    configdata['mapping']['wikibase_url'] = wikibase_url
    configdata = littlehelpers.build_depconfig(configdata)

@app.route('/')
def index_page():
    return render_template("index.html", wikibase_url=wikibase_url,
                           wikibase_name=configdata['mapping']['wikibase_name'],
                           zotero_name=configdata['mapping']['zotero_group_name'],
                           zoteromapping=zoteromapping['mapping'])

@app.route('/basic_config', methods= ['GET', 'POST'])
def basic_config():
    global configdata
    properties = botconfig.load_mapping('properties')
    if request.method == 'GET':
        return render_template("basic_config.html", data=configdata['mapping'])

    elif request.method == 'POST':
        if request.form:
            for key in request.form:
                if key.startswith('wikibase') or key.startswith('zotero'):
                    configdata['mapping'][key] = request.form.get(key)


                elif key.startswith('prop') or key.startswith('class'):
                    if key.endswith('_redo'): # user has pressed 'import from wikidata to known wikibase entity' button
                        newentity_name = key.replace('_redo', '')
                        if newentity_name.startswith("class") and newentity_name != "class_ontology_class":
                            classqid = configdata['mapping']['class_ontology_class']['wikibase']
                        else:
                            classqid = None
                        littlehelpers.import_wikidata_entity(
                            configdata['mapping'][newentity_name]['wikidata'], wbid=configdata['mapping'][newentity_name]['wikibase'], classqid=classqid)
                    elif key.endswith('_create'):  # user has pressed 'create new'
                        newentity_name = key.replace('_create','')
                        if newentity_name.startswith("class") and newentity_name != "class_ontology_class":
                            classqid = configdata['mapping']['class_ontology_class']['wikibase']
                        else:
                            classqid = None
                        if 'wikidata' in configdata['mapping'][newentity_name]:
                            newentity_id = littlehelpers.import_wikidata_entity(configdata['mapping'][newentity_name]['wikidata'], wbid=False, classqid=classqid)

                        else:
                            if newentity_name.startswith("class"):
                                newitemdata = {'qid':False, 'labels':[{'lang':'en', 'value':configdata['mapping'][newentity_name]['name']}],
                                                'statements':[]}
                                if classqid:
                                    newitemdata['statements'].append({'type':'WikibaseItem','prop_nr':configdata['mapping']['prop_instanceof']['wikibase'],'value':classqid})
                                    newentity_id = xwbi.itemwrite(newitemdata)
                            elif newentity_name.startswith("prop"):
                                newprop = xwbi.wbi.property.new(datatype=configdata['mapping'][newentity_name]['type'])
                                newprop.labels.set('en', configdata['mapping'][newentity_name]['name'])
                                newprop.write()
                                newentity_id = newprop.id
                                properties['mapping'][newentity_id] = {
                                    "enlabel": configdata['mapping'][newentity_name]['name'],
                                    "type": configdata['mapping'][newentity_name]['type'],
                                    "wdprop": None
                                }
                                botconfig.dump_mapping(properties)
                        configdata['mapping'][newentity_name]['wikibase'] = newentity_id
                    else: # user has manually chosen a value
                        configdata['mapping'][key]['wikibase'] = request.form.get(key)
        botconfig.dump_mapping(configdata)
        return render_template("basic_config.html", data=configdata['mapping'])

@app.route('/zoterofields/<itemtype>')
def map_zoterofield(itemtype):
    global properties
    global configdata
    for field in ['ISBN', 'extra', 'language']: # these are defined in basic config
        zoteromapping['mapping'][itemtype]['fields'].pop(field) if field in zoteromapping['mapping'][itemtype]['fields'] else True
    return render_template("zoterofields.html", itemtype=itemtype,
                           zoteromapping=zoteromapping['mapping'][itemtype],
                           wikibase_entity_ns=configdata['mapping']['wikibase_entity_ns'],
                           properties=properties['mapping'])


if __name__ == '__main__':
    app.run(debug=True)