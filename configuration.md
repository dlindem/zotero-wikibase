# Installation and Configuration

## To start with

You need a zotero user with read and write access to the Zotero group you want to use, a Zotero API key, and a Wikibase user with bot permissions and password.
* A Zotere API key can be obtained here: https://www.zotero.org/settings/keys/new

## Installation
* Create a virtual environment, and run the scripts always inside that.
* Required are the following packages; install them in your virtual environment:
  * wikibaseintegrator
  * mwclient
  * pyzotero

## Configuration
1. Edit the file `bots/config_template.py`, providing the required values
   1. All values for the variables in the "Zotero" section.
   2. All values for the variables in the "Wikibase" section. Most edits here can be done with a regex substitution (the example Wikibase URL by your Wikibase URL.) For the required properties, "Wikibase Entity" (type EternalId) and "Formatter URL" (type String), provide their numbers on your Wikibase; otherwise, create them manually, and insert here their numbers. If you use an empty Wikibase, they will be "P1" and "P2".
2. Save that file as `bots/config.py`.
3. Edit the file `bots/config_private.py`, providing values for all variables
   1. Username and password for a Wikibase bot user (i.e., with confirmed email and bot permissions)
   2. Your Zotero API key (that is linked to your Zotero user), and the ID number of the Zotero group you will be sending data from (as it appears in your Zotero item URLs after "zotero.org/groups/"; this has to be an integer not a string)
4. Run the script `installation-test.py`. The test that will be performed is whether the Wikibase bot is able to set a value for "formatter URL" and "formatter URI" at your "Wikibase Entity" property, namely the values "https://www.wikidata.org/wiki/$1", and "http://www.wikidata.org/entity/$1", respectively. If you already had set that, delete the statement, so that the test script will re-set it. If the test works well, go ahead.
5. 
