# Configuration of the tool

The zotero-wikibase tool will guide you through the configuration process, which consists of the following steps:

* The tool will ask you to enter basic parameters
  * Zotero group to export data from (Zotero group ID, Zotero API key)
  * Wikibase to export data to (Wikibase name and URL, bot-user name and password)
    * Sensible information (usernames and passwords, API key) will be stored in a file called `config_private.json`, which is by default included in `.gitignore`, so that there is no risk that you share this information in case you keep your zotero-wikibase folder synced using git. This means, that if you use your zotero-wikibase tool instance on various machines, you have to manually copy this file to the other machine, or re-do this configuration step inside the tool.
* Definition of basic ontology entities
  * Some basic properties, and items describing ontology classes need to be defined. During the process, the tool will ask you whether you want to create new entities, or use entities already existing on your Wikibase.
    * Examples for basic entities: "Wikidata Entity", a property of datatype "ExternalId" which points to the equivalent entity on Wikidata, or "instance of" (equivalent to rdf:type and wd:P31).
    * Examples for ontology classes: "Language", "Creator Role", or "BibItem type". Instances of these classes will be linked to their class using the "instance of" property.
* The mapping of Zotero creator types and Zotero data fields (one set of fields per BibItem type) is done when exporting data from Zotero, i.e., in the next step.
  * When you export data from Zotero (see next step), the tool checks if all BibItem types and all fields containing data in the set of records you are exporting are already mapped to Wikibase properties.
    * You can specify existing properties to use, or create new properties along the process. You are able to map fields differently according to the BibItem type. For example, you may want to have titles of books mapped to a different property than titles of television broadcasts.

