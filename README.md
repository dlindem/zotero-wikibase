# zotero-wikibase
 **A python app for migrating bibliographical data**

This tool exports records in a Zotero group library to a custom Wikibase, prepares datasets to be sent to OpenRefine, and feeds OpenRefine reconciliaton results back to the Wikibase. Wikidata is envolved in the entity reconciliation.

The following are represented by default using 'item statements' (object properties), so that further steps for LOD-ification are not needed:
* Bibliographical item type
* Publication language

Creator names, or any 'string' (literal string value) property you specify are prepared for entity reconciliation using OpenRefine. Reconciliation results from Wikidata and/or from your own Wikibase (that makes sense if the entities you want to find already exist on your Wikibase) are accepted for re-feeding your Wikibase.

Identifiers (the Zotero Item ID, ISBN, ISSN, OCLC, and what you specify that my occur in the EXTRA field) are normalized and linked using 'external-id' properties.

## Installation and Configuration

### To start with

You need a zotero user with read and write access to the Zotero group you want to use, a Zotero API key, and a Wikibase user with bot permissions and password.
* A Zotere API key can be obtained here: https://www.zotero.org/settings/keys/new. Be sure to grant read and write access through the key you create to the group library you want to export items from. The key consists of a single chain of characters.

### Installation
* Create a virtual environment, and run the scripts always inside that.
* Required are the following packages; install them in your virtual environment:
  * wikibaseintegrator
  * mwclient
  * pyzotero

### Configuration
1. Edit the file `bots/config_template.py`, providing the required values
   1. All values for the variables in the "Zotero" section.
   2. All values for the variables in the "Wikibase" section. Most edits here can be done with a regex substitution (the example Wikibase URL by your Wikibase URL.) For the required properties, "Wikibase Entity" (type EternalId) and "Formatter URL" (type String), provide their numbers on your Wikibase; otherwise, create them manually, and insert here their numbers. If you use an empty Wikibase, they will be "P1" and "P2".
2. Save that file as `bots/config.py`.
3. Edit the file `bots/config_private.py`, providing values for all variables
   1. Username and password for a Wikibase bot user (i.e., with confirmed email and bot permissions)
   2. Your Zotero API key (see above), and the ID number of the Zotero group you will be sending data from (as it appears in your Zotero group's item URLs after "zotero.org/groups/"; this has to be an integer not a string)
4. Run the script `installation-test.py`. The test that will be performed is whether the Wikibase bot is able to set a value for "formatter URL" and "formatter URI" at your "Wikibase Entity" property, namely the values "https://www.wikidata.org/wiki/$1", and "http://www.wikidata.org/entity/$1", respectively. If you already had set that, delete the statement, so that the test script will re-set it. If the test works well, go ahead.
5. Now you can already start to export Zotero records! The mapping of the Zotero fields to Wikibase properties (which still may have to be created) is done when running the export tool.

### zotero-export.py
* In `config.py`, you have specified a tag you will use for marking Zotero items to be exported, such as `wikibase-export`. Mark some items with that tag (and sync with Zotero web, in case you work on a local Zotero instance.)
* Run `zotero-export.py`
  * The script first checks what Zotero item types you want to export, and will create a Wikibase Item representing each item type, in case it does not exist. For this, it imports the corresponding item from Wikidata, as defined in `bots/mappings/zotero_bibtypes.json`.
  * The script asks you then whether you want to check the mapping of the fields of these item types. As long as you are not sure all fields you want to export are mapped to a property, you should do this.
    * You can specify existing properties to use, or create new properties along the process. You are able to map fields differently according to the item type. For example, you may want to have titles of books mapped to a different property than titles of television broadcasts.
  * The script asks you then whether you want to do the same with the creator types present in the ingested dataset.
  * When that is done, the script transforms the Zotero API output, and uploads it to your Wikibase.
    * The Zotero API will deliver you chunks of 100 items. That is, if you tag more than 100 with your export tag, only one hundred of these will be processed in one run. Those that are not processed in one run will stay with the export tag.
    * Zotero items are patched in a way you specify (you can have the Wikibase URI written to the EXTRA field, and/or attached as URI link attachment). In any case, successfully exported items will be tagged with the tag you specify, such as `on-wikibase`.

### Details about Zotero fields and how they are processed
* Creators: Creator given and family names, together with a string consisting of the full name, and the list position number, are stored as 'string' qualifiers to an 'unknown value' statement. After reconciliation, the 'unknown value' of that statement will be replaced with the item representing the natural person (or organization).
* Languages: The tool expects by default a three-digit ISO-639-3 or a two-digit ISO-639-1 language code. Language names (e.g. worldcat pushes names like 'English' to the language field) can also be mapped to language items; the user is prompted for providing the correspondent ISO-639-3 code in cases where the literal is not already mapped.
* ISBN are converted into pure digits (deleting the hyphens), and linked to a ISBN-13 or ISBN-10 property, according to their length. This is how Wikidata does this.
* ISSN are normalized: four digits - hyphen - four digits.
* OCLC (and other identifiers that Zotero import 'translators' send to the EXTRA field) are found using regex patterns, and linked to the specified 'external-id' property. The user can specify 'formatter URL' and 'formatter URI for RDF resource' patterns on the wikibase, so that the identifiers become clickable and accessible as full URI.
* Any other field is mapped to a 'string' property. As said above, you are able to link fields differently per item type (this is also true for creators, e.g., that you may want to use different properties for authors of articles and authors of audio recordings.) If you want to reconcile e.g. publishers, or places, you provide an 'item' property which is used for replacing the 'string' property statement after reconciliation.
