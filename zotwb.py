from bots import botconfig, zotwb_functions
from flask import Flask, render_template, request
from bots import config_private
import os, re, json, pandas
from datetime import datetime
# from flask_wtf import FlaskForm
app = Flask(__name__)

# wikibase_url = config_private.wikibase_url
# if configdata['mapping']['wikibase_url'] != wikibase_url:
#     print(f"Wikibase URL in config_private.py has changed to {wikibase_url}... Will update dependent configurations.")
#     configdata['mapping']['wikibase_url'] = wikibase_url
#     configdata = zotwb_functions.build_depconfig(configdata)

@app.route('/')
def index_page():
    configdata = botconfig.load_mapping('config')
    zoteromapping = botconfig.load_mapping('zotero')
    config_check = zotwb_functions.check_config(configdata=configdata['mapping'])
    return render_template("index.html", wikibase_url=configdata['mapping']['wikibase_url'],
                           wikibase_name=configdata['mapping']['wikibase_name'],
                           zotero_name=configdata['mapping']['zotero_group_name'],
                           zoteromapping=zoteromapping['mapping'],
                           config_check=config_check,
                           all_types = "all_types")

@app.route('/zotero_export', methods= ['GET', 'POST'])
def zotero_export():
    configdata = botconfig.load_mapping('config')
    zoteromapping = botconfig.load_mapping('zotero')
    with open('data/zoteroexport.json', 'r', encoding='utf-8') as jsonfile:
        zoterodata = json.load(jsonfile)
        zotero_check_messages = zotwb_functions.check_export(zoterodata=zoterodata, zoteromapping=zoteromapping)
    if request.method == 'GET':

        return render_template("zotero_export.html", wikibase_url=wikibase_url,
                               wikibase_entity_ns=configdata['mapping']['wikibase_entity_ns'],
                               wikibase_name=configdata['mapping']['wikibase_name'],
                               zotero_name=configdata['mapping']['zotero_group_name'],
                               zoterodata=zoterodata,
                               zotero_check_messages=zotero_check_messages,
                               zotero_len=str(len(zoterodata)),
                               zotero_when=datetime.utcfromtimestamp(os.path.getmtime('data/zoteroexport.json')).strftime(
            '%Y-%m-%d at %H:%M:%S UTC'),
                               export_tag=configdata['mapping']['zotero_export_tag'],
                               onwiki_tag=configdata['mapping']['zotero_on_wikibase_tag'],
                               messages=[]
                               )
    elif request.method == 'POST':
        if request.form:
            for command in request.form:
                if command == "get_export":
                    zoterodata = zotwb_functions.zoterobot.getexport(save_to_file=True)
                    messages = [f"Successfully ingested zotero data (set of {str(len(zoterodata))} records tagged '{configdata['mapping']['zotero_export_tag']}')."]
                    msgcolor = "background:limegreen"
                    zotero_check_messages = zotwb_functions.check_export(zoterodata=zoterodata,
                                                                         zoteromapping=zoteromapping)
                elif command == "do_upload":
                    upload = zotwb_functions.wikibase_upload(data=zoterodata)
                    messages = upload['messages']
                    msgcolor = upload['msgcolor']
        return render_template("zotero_export.html", wikibase_url=wikibase_url,
                               wikibase_entity_ns=configdata['mapping']['wikibase_entity_ns'],
                               wikibase_name=configdata['mapping']['wikibase_name'],
                               zotero_name=configdata['mapping']['zotero_group_name'],
                               zoterodata=zoterodata,
                               zotero_check_messages=zotero_check_messages,
                               zotero_len=str(len(zoterodata)),
                               zotero_when=datetime.utcfromtimestamp(os.path.getmtime('data/zoteroexport.json')).strftime(
            '%Y-%m-%d at %H:%M:%S UTC'),
                               export_tag=configdata['mapping']['zotero_export_tag'],
                               onwiki_tag=configdata['mapping']['zotero_on_wikibase_tag'],
                               messages=messages, msgcolor=msgcolor
                               )




@app.route('/basic_config', methods= ['GET', 'POST'])
def basic_config():
    configdata = botconfig.load_mapping('config')
    properties = botconfig.load_mapping('properties')
    if request.method == 'GET':
        return render_template("basic_config.html", data=configdata['mapping'], message = None, msgcolor = None)

    elif request.method == 'POST':
        if request.form:
            for key in request.form:
                if key.startswith('wikibase') or key.startswith('zotero'):
                    configdata['mapping'][key] = request.form.get(key)
                    if key == 'wikibase_url': # update configs that depend on the wikibase URL
                        configdata = zotwb_functions.build_depconfig(configdata)
                    command = 'Update '+key.replace('_',' ')
                elif key.startswith('prop') or key.startswith('class'):
                    command = key.replace('_', ' ')
                    if key.endswith('_redo'): # user has pressed 'import from wikidata to known wikibase entity' button
                        configitem = key.replace('_redo', '')
                        if configitem.startswith("class") and configitem != "class_ontology_class":
                            classqid = configdata['mapping']['class_ontology_class']['wikibase']
                        else:
                            classqid = None
                        zotwb_functions.import_wikidata_entity(
                            configdata['mapping'][configitem]['wikidata'], wbid=configdata['mapping'][configitem]['wikibase'], classqid=classqid)
                    elif key.endswith('_create'):  # user has pressed 'create new'
                        configitem = key.replace('_create','')
                        if configitem.startswith("class") and configitem != "class_ontology_class":
                            classqid = configdata['mapping']['class_ontology_class']['wikibase']
                        else:
                            classqid = None
                        if 'wikidata' in configdata['mapping'][configitem]:
                            newentity_id = zotwb_functions.import_wikidata_entity(configdata['mapping'][configitem]['wikidata'], wbid=False, classqid=classqid)

                        else:
                            if configitem.startswith("class"):
                                newitemdata = {'qid':False, 'labels':[{'lang':'en', 'value':configdata['mapping'][configitem]['name']}],
                                                'statements':[]}
                                if classqid:
                                    newitemdata['statements'].append({'type':'WikibaseItem','prop_nr':configdata['mapping']['prop_instanceof']['wikibase'],'value':classqid})
                                    newentity_id = zotwb_functions.xwbi.itemwrite(newitemdata)
                            elif configitem.startswith("prop"):
                                newprop = zotwb_functions.xwbi.wbi.property.new(datatype=configdata['mapping'][configitem]['type'])
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
                        command = command = 'Update '+key.replace('_',' ')
                message = f"Successfully performed operation: {command}."
                msgcolor = "background:limegreen"
        botconfig.dump_mapping(configdata)
        return render_template("basic_config.html", data=configdata['mapping'], message=message, msgcolor=msgcolor)

@app.route('/zoterofields/<itemtype>', methods= ['GET', 'POST'])
def map_zoterofield(itemtype):
    properties = botconfig.load_mapping('properties')
    configdata = botconfig.load_mapping('config')
    zotero_bibtypes = botconfig.load_mapping('zotero_bibtypes')
    zoteromapping = botconfig.load_mapping('zotero')
    for field in ['ISBN', 'extra', 'language']: # these are defined in basic config
        zoteromapping['mapping'][itemtype]['fields'].pop(field) if field in zoteromapping['mapping'][itemtype]['fields'] else True
    if request.method == 'GET':
        return render_template("zoterofields.html", itemtype=itemtype,
                           zoteromapping=zoteromapping['mapping'],
                           wikibase_entity_ns=configdata['mapping']['wikibase_entity_ns'],
                           properties=properties['mapping'],
                           zotero_bibtypes=zotero_bibtypes['mapping'],
                               messages=[])
    elif request.method == 'POST':
        if request.form:
            for key in request.form:
                messages = []
                msgcolor = "background:limegreen"
                if key.startswith('bibtypeqid'): # zotero itemtype > bibtypeqid mapping
                    if key.endswith('_redo'):  # user has pressed 'import from wikidata to known wikibase entity' button
                        fieldname = key.replace('_redo', '')
                        zotwb_functions.import_wikidata_entity(
                            zotero_bibtypes['mapping'][itemtype], wbid=zoteromapping['mapping'][itemtype]['bibtypeqid'], classqid=configdata['mapping']['class_bibitem_type']['wikibase'])
                    elif key.endswith('_create'):  # user has pressed 'create new'
                        fieldname = key.replace('_create', '')
                        newentity_id = zotwb_functions.import_wikidata_entity(zotero_bibtypes['mapping'][itemtype], wbid=False, classqid=configdata['mapping']['class_bibitem_type']['wikibase'])
                        zoteromapping['mapping'][itemtype]['bibtypeqid'] = newentity_id
                    else: # user has manually chosen a bibtypeqid value
                        zoteromapping['mapping'][itemtype]['bibtypeqid'] = request.form.get(key)
                    messages = [f"Successfully update BibType entity for {itemtype}."]
                else: # field or creatortype mappings
                    fieldtype = re.search(r'([a-zA-Z]+)@',key).group(1)
                    command = re.sub(r'[a-zA-Z]+@','',key)
                    if command.endswith('_redo'):  # user has pressed 'import from wikidata to known wikibase entity' button
                        fieldname = command.replace('_redo', '')
                        zotwb_functions.import_wikidata_entity(
                            properties[zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop']]['wdprop'],
                            wbid=zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop'])
                        properties['mapping'][zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop']] = {
                            "enlabel": zoteromapping['mapping']['all_types'][fieldtype][fieldname]['name'],
                            "type": zoteromapping['mapping']['all_types'][fieldtype][fieldname]['dtype'],
                            "wdprop": properties[zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop']]['wdprop']
                        }
                        botconfig.dump_mapping(properties)
                        messages = [f"Successfully imported {properties[zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop']]['wdprop']} to {zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop']}."]
                    elif command.endswith('_create'):  # user has pressed 'create new'
                        fieldname = command.replace('_create', '')
                        datatype = botconfig.datatypes_mapping[zoteromapping['mapping']['all_types'][fieldtype][fieldname]['dtype']]
                        newprop = zotwb_functions.xwbi.wbi.property.new(datatype=datatype)
                        newprop.labels.set('en', zoteromapping['mapping']['all_types'][fieldtype][fieldname]['name'])
                        newprop.descriptions.set('en', 'Property created for Zotero field '+fieldname)
                        if fieldtype == "creatorType":
                            propclass = configdata['mapping']['class_creator_role']['wikibase']
                        elif fieldtype == "fields":
                            propclass = configdata['mapping']['class_bibitem_type']['wikibase']
                        # tbd: propclss statement
                        print(str(newprop))
                        newprop.write()
                        newentity_id = newprop.id
                        properties['mapping'][newentity_id] = {
                            "enlabel": zoteromapping['mapping']['all_types'][fieldtype][fieldname]['name'],
                            "type": zoteromapping['mapping']['all_types'][fieldtype][fieldname]['dtype'],
                            "wdprop": None
                        }
                        botconfig.dump_mapping(properties)
                        zoteromapping['mapping'][itemtype][fieldtype][fieldname]['wbprop'] = newentity_id
                        if itemtype == "all_types":
                            propagation = zotwb_functions.propagate_mapping(fieldtype=fieldtype, fieldname=fieldname, wbprop=newentity_id)
                            zoteromapping['mapping'] = propagation['mapping']
                            messages += propagation['messages']
                            messages.append(f"...Successfully created and propagated property {newentity_id} for {fieldname} to all item types.")
                        messages = [f"Successfully created {newentity_id} with datatype {zoteromapping['mapping']['all_types'][fieldtype][fieldname]['dtype']}."]
                    else: # user has manually entered a wikibase property ID or "False"

                        wbprop = zotwb_functions.check_prop_id(request.form.get(key))
                        zoteromapping['mapping'][itemtype][fieldtype][command]['wbprop'] = wbprop
                        if wbprop == None:
                            messages = ['Operation failed: Value bad format. Format must be e.g. "P123" or "False" or "X".']
                            msgcolor = "background:orangered"
                        elif itemtype == "all_types":
                            propagation = zotwb_functions.propagate_mapping(zoteromapping=zoteromapping['mapping'], fieldtype=fieldtype, fieldname=command, wbprop=wbprop)
                            zoteromapping['mapping'] = propagation['mapping']
                            messages += propagation['messages']
                            messages.append(f"...Successfully propagated property {wbprop} for {command} to all item types.")
                        else:
                            messages = [f"Successfully set property {wbprop} as mapped to {itemtype}-{command}."]

            botconfig.dump_mapping(zoteromapping)
            print(str(messages))
            return render_template("zoterofields.html", itemtype=itemtype,
                                   zoteromapping=zoteromapping['mapping'],
                                   wikibase_entity_ns=configdata['mapping']['wikibase_entity_ns'],
                                   properties=properties['mapping'],
                                   zotero_bibtypes=zotero_bibtypes['mapping'],
                                   messages=messages, msgcolor=msgcolor)

@app.route('/wikidata_alignment', methods= ['GET', 'POST'])
def wikidata_alignment():
    properties = botconfig.load_mapping('properties')
    configdata = botconfig.load_mapping('config')


    if request.method == 'GET':
        propcachedate = datetime.utcfromtimestamp(os.path.getmtime('bots/mappings/properties.json')).strftime(
            '%Y-%m-%d at %H:%M:%S UTC')
        return render_template("wikidata_alignment.html", wikibase_url=configdata['mapping']['wikibase_url'],
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

                    zotwb_functions.rewrite_properties_mapping()
                    properties = botconfig.load_mapping('properties')
                    message = f"Properties data cache update sucessful."
            return render_template("wikidata_alignment.html", wikibase_url=configdata['mapping']['wikibase_url'],
                                   wikibase_name=configdata['mapping']['wikibase_name'],
                                   wikibase_entity_ns=configdata['mapping']['wikibase_entity_ns'],
                                   properties=properties['mapping'],
                                   propcachedate=propcachedate,
                                   message=message)

@app.route('/openrefine', methods= ['GET', 'POST'])
def openrefine():
    configdata = botconfig.load_mapping('config')
    get_recon = zotwb_functions.get_recon_pd(folder="data/reconciled_creators")
    recon_df = get_recon['data']
    recon_df.set_index('creatorstatement')
    recon_wd = str(len(recon_df.dropna(subset=['Wikidata_Qid'])))
    recon_wb = str(len(recon_df.dropna(subset=['Wikibase_Qid'])))
    if request.method == 'GET':

        return render_template("openrefine.html", wikibase_name=configdata['mapping']['wikibase_name'],
                               messages=[], msgcolor="background:limegreen",
                               recon_all= str(len(recon_df)), recon_wd = recon_wd, recon_wb=recon_wb, filename = get_recon['filename'])
    elif request.method == 'POST':
        if request.form:
            for key in request.form:
                messages = [f"Operation sucessful. Operation name was '{key.replace('_',' ')}'."]
                msgcolor = "background:limegreen"
                if key == "export_unreconciled_creators":
                    messages = zotwb_functions.export_creators()
                    get_recon = zotwb_functions.get_recon_pd(folder="data/reconciled_creators")
                    recon_df = get_recon['data']
                    recon_df.set_index('creatorstatement')
                    recon_wd = str(len(recon_df.dropna(subset=['Wikidata_Qid'])))
                    recon_wb = str(len(recon_df.dropna(subset=['Wikibase_Qid'])))
                if key == "import_reconciled_wikidata":
                    messages = zotwb_functions.import_creators(data=recon_df, infile=get_recon['filename'], wikidata=True)
                if key == "import_reconciled_wikibase":
                    messages = zotwb_functions.import_creators(data=recon_df, infile=get_recon['filename'], wikibase=True)
                if key == "import_unreconciled":
                    messages = zotwb_functions.import_creators(data=recon_df, infile=get_recon['filename'], unrecon=True)

        return render_template("openrefine.html", wikibase_name=configdata['mapping']['wikibase_name'],
                               messages=messages, msgcolor=msgcolor,
                               recon_all = str(len(recon_df)), recon_wd = recon_wd, recon_wb = recon_wb, filename = get_recon['filename'])



if __name__ == '__main__':
    app.run(debug=True)