## Installation

This section explains what is necessary to start using the zotero-wikibase tool: 

* A Zotero account with read-and-write access to the Zotero group you want to export data from
  * You need a zotero user with read and write access to the Zotero group you want to use, a Zotero API key, and a Wikibase user with bot permissions and password.
  * A Zotere API key can be obtained [here](https://www.zotero.org/settings/keys/new). Be sure to grant read and write access through the key you create to the group library you want to export items from. The key consists of a single chain of characters.
* A Wikibase instance
* The Open Refine software, together with the module for connection to your Wikibase

Installation steps:
* This tool is a python3 app. You need python3 installed.
* Create a [virtual environment](https://realpython.com/python-virtual-environments-a-primer/), and run all subsequent steps, and the tool itself, always inside that.
* Clone this repository to a place of your choice, ideally the same project folder your virtual environment was created in.
* The tool requires the following packages; [install them in your virtual environment](https://realpython.com/python-virtual-environments-a-primer/#install-packages-into-it):
  * wikibaseintegrator
  * mwclient
  * pyzotero