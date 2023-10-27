from bots import botconfig, littlehelpers
from flask import Flask, render_template, request
from bots import config_private
import os, re
from datetime import datetime
# from flask_wtf import FlaskForm
app = Flask(__name__)

properties = botconfig.load_mapping('properties')
zoteromapping = botconfig.load_mapping('zotero')
configdata = botconfig.load_mapping('config')
zotero_bibtypes = botconfig.load_mapping('zotero_bibtypes')
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
                        configitem = key.replace('_redo', '')
                        if configitem.startswith("class") and configitem != "class_ontology_class":
                            classqid = configdata['mapping']['class_ontology_class']['wikibase']
                        else:
                            classqid = None
                        littlehelpers.import_wikidata_entity(
                            configdata['mapping'][configitem]['wikidata'], wbid=configdata['mapping'][configitem]['wikibase'], classqid=classqid)
                    elif key.endswith('_create'):  # user has pressed 'create new'
                        configitem = key.replace('_create','')
                        if configitem.startswith("class") and configitem != "class_ontology_class":
                            classqid = configdata['mapping']['class_ontology_class']['wikibase']
                        else:
                            classqid = None
                        if 'wikidata' in configdata['mapping'][configitem]:
                            newentity_id = littlehelpers.import_wikidata_entity(configdata['mapping'][configitem]['wikidata'], wbid=False, classqid=classqid)

                        else:
                            if configitem.startswith("class"):
                                newitemdata = {'qid':False, 'labels':[{'lang':'en', 'value':configdata['mapping'][configitem]['name']}],
                                                'statements':[]}
                                if classqid:
                                    newitemdata['statements'].append({'type':'WikibaseItem','prop_nr':configdata['mapping']['prop_instanceof']['wikibase'],'value':classqid})
                                    newentity_id = littlehelpers.xwbi.itemwrite(newitemdata)
                            elif configitem.startswith("prop"):
                                newprop = littlehelpers.xwbi.wbi.property.new(datatype=configdata['mapping'][configitem]['type'])
                                newprop.labels.set('en', configdata['mapping'][configitem]['name'])
                                newprop.write()
                                newentity_id = newprop.id
                                properties['mapping'][newentity_id] = {
                                    "enlabel": configdata['mapping'][configitem]['name'],
                                    "type": configdata['mapping'][configitem]['type'],
                                    "wdprop": None
                                }
                                botconfig.dump_mapping(properties)
                        configdata['mapping'][configitem]['wikibase'] = newentity_id
                    else: # user has manually chosen a value
                        configdata['mapping'][key]['wikibase'] = request.form.get(key)
        botconfig.dump_mapping(configdata)
        return render_template("basic_config.html", data=configdata['mapping'])

@app.route('/zoterofields/<itemtype>', methods= ['GET', 'POST'])
def map_zoterofield(itemtype):
    global properties
    global configdata
    global zotero_bibtypes
    global zoteromapping
    for field in ['ISBN', 'extra', 'language']: # these are defined in basic config
        zoteromapping['mapping'][itemtype]['fields'].pop(field) if field in zoteromapping['mapping'][itemtype]['fields'] else True
    if request.method == 'GET':
        return render_template("zoterofields.html", itemtype=itemtype,
                           zoteromapping=zoteromapping['mapping'],
                           wikibase_entity_ns=configdata['mapping']['wikibase_entity_ns'],
                           properties=properties['mapping'],
                           zotero_bibtypes=zotero_bibtypes['mapping'],
                               message=None)
    elif request.method == 'POST':
        if request.form:
            for key in request.form:
                message = f"Operation sucessful. Operation name was '{key}'."
                msgcolor = "background:limegreen"
                if key.startswith('bibtypeqid'): # zotero itemtype > bibtypeqid mapping
                    if key.endswith('_redo'):  # user has pressed 'import from wikidata to known wikibase entity' button
                        fieldname = key.replace('_redo', '')
                        littlehelpers.import_wikidata_entity(
                            zotero_bibtypes['mapping'][itemtype], wbid=zoteromapping['mapping'][itemtype]['bibtypeqid'], classqid=configdata['mapping']['class_bibitem_type']['wikibase'])
                    elif key.endswith('_create'):  # user has pressed 'create new'
                        fieldname = key.replace('_create', '')
                        newentity_id = littlehelpers.import_wikidata_entity(zotero_bibtypes['mapping'][itemtype], wbid=False, classqid=configdata['mapping']['class_bibitem_type']['wikibase'])
                        zoteromapping['mapping'][itemtype]['bibtypeqid'] = newentity_id
                    else: # user has manually chosen a bibtypeqid value
                        zoteromapping['mapping'][itemtype]['bibtypeqid'] = request.form.get(key)
                else: # field or creatortype mappings
                    fieldtype = re.search(r'([a-zA-Z]+)@',key).group(1)
                    command = re.sub(r'[a-zA-Z]+@','',key)
                    if command.endswith('_redo'):  # user has pressed 'import from wikidata to known wikibase entity' button
                        fieldname = command.replace('_redo', '')
                        littlehelpers.import_wikidata_entity(
                            properties[zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop']]['wdprop'],
                            wbid=zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop'])
                        properties['mapping'][zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop']] = {
                            "enlabel": zoteromapping['mapping']['all_types'][fieldtype][fieldname]['name'],
                            "type": zoteromapping['mapping']['all_types'][fieldtype][fieldname]['dtype'],
                            "wdprop": properties[zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop']]['wdprop']
                        }
                        botconfig.dump_mapping(properties)
                    elif command.endswith('_create'):  # user has pressed 'create new'
                        fieldname = command.replace('_create', '')
                        datatype = botconfig.datatypes_mapping[zoteromapping['mapping']['all_types'][fieldtype][fieldname]['dtype']]
                        newprop = littlehelpers.xwbi.wbi.property.new(datatype=datatype)
                        newprop.labels.set('en', zoteromapping['mapping']['all_types'][fieldtype][fieldname]['name'])
                        newprop.descriptions.set('en', 'Property created for Zotero field '+fieldname)
                        print(str(newprop))
                        newprop.write()
                        newentity_id = newprop.id
                        properties['mapping'][newentity_id] = {
                            "enlabel": zoteromapping['mapping']['all_types'][fieldtype][fieldname]['name'],
                            "type": zoteromapping['mapping']['all_types'][fieldtype][fieldname]['dtype'],
                            "wdprop": None
                        }
                        zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop'] = newentity_id
                        botconfig.dump_mapping(properties)
                    else: # user has manually entered a wikibase property ID or "False"
                        wbprop = littlehelpers.check_prop_id(request.form.get(key))
                        zoteromapping['mapping'][itemtype][fieldtype][command]['wbprop'] = wbprop
                        if wbprop == None:
                            message = 'Operation failed: Value bad format. Format must be e.g. "P123" or "False" or "X".'
                            msgcolor = "background:orangered"
            botconfig.dump_mapping(zoteromapping)
            return render_template("zoterofields.html", itemtype=itemtype,
                                   zoteromapping=zoteromapping['mapping'],
                                   wikibase_entity_ns=configdata['mapping']['wikibase_entity_ns'],
                                   properties=properties['mapping'],
                                   zotero_bibtypes=zotero_bibtypes['mapping'],
                                   message=message, msgcolor=msgcolor)

@app.route('/wikidata_alignment', methods= ['GET', 'POST'])
def wikidata_alignment():
    global properties
    global configdata
    global zoteromapping


    if request.method == 'GET':
        propcachedate = datetime.utcfromtimestamp(os.path.getmtime('bots/mappings/properties.json')).strftime(
            '%Y-%m-%d at %H:%M:%S UTC')
        return render_template("wikidata_alignment.html", wikibase_url=config_private.wikibase_url,
                               wikibase_name=configdata['mapping']['wikibase_name'],
                           wikibase_entity_ns=configdata['mapping']['wikibase_entity_ns'],
                           properties=properties['mapping'],
                               propcachedate=propcachedate,
                           message=None)
    elif request.method == 'POST':
        propcachedate = datetime.utcfromtimestamp(os.path.getmtime('bots/mappings/properties.json')).strftime(
            '%Y-%m-%d at %H:%M:%S UTC')
        if request.form:
            for key in request.form:
                message = f"Operation sucessful. Operation name was '{key}'."
                msgcolor = "background:limegreen"
                if key == "update_cache":

                    littlehelpers.rewrite_properties_mapping()
                    properties = botconfig.load_mapping('properties')
                    message = f"Properties data cache update sucessful."
            return render_template("wikidata_alignment.html", wikibase_url=config_private.wikibase_url,
                                   wikibase_name=configdata['mapping']['wikibase_name'],
                                   wikibase_entity_ns=configdata['mapping']['wikibase_entity_ns'],
                                   properties=properties['mapping'],
                                   propcachedate=propcachedate,
                                   message=message)


if __name__ == '__main__':
    app.run(debug=True)