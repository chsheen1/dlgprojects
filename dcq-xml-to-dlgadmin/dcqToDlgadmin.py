#!/usr/bin/env python
from lxml import etree

# --- Dictionaries for reference ---
qdcFieldsDict = {
    "dcterms:provenance":"dcterms_provenance",
    "dc:title":"dcterms_title",
    "dc:creator":"dcterms_creator",
    "dc:contributor":"dcterms_contributor",
    "dc:subject":"dcterms_subject",
    "dc:description":"dcterms_description",
    "dc:identifier":"dcterms_identifier",
    "dc:publisher":"dcterms_publisher",
    "dcterms:isShownAt":"dcterms_is_shown_at",
    "dc:date":"dc_date",
    "dcterms:temporal":"dcterms_temporal",
    "dcterms:spatial":"dcterms_spatial",
    "dc:format":"dc_format",
    "dcterms:isPartOf":"dcterms_is_part_of",
    "dc:rights":"dc_right",
    "dcterms:rightsHolder":"dcterms_rights_holder",
    "dcterms:bibliographicCitation":"dcterms_bibliographic_citation",
    "dlg:localRights":"dlg_local_right",
    "dc:relation":"dc_relation",
    "dc:type":"dcterms_type",
    "dcterms:medium":"dcterms_medium",
    "dcterms:extent":"dcterms_extent",
    "dc:language":"dcterms_language",
    "dlg:subjectPersonal":"dlg_subject_personal"
    }
nsDict = {
    'oai_dc':'http://www.openarchives.org/OAI/2.0/oai_dc/',
    'oai_qdc':'http://worldcat.org/xmlschemas/qdc-1.0/',
    'dcterms':'http://purl.org/dc/terms/',
    'dc':'http://purl.org/dc/elements/1.1/',
    'dlg':'http://dlg.org/local/elements/1.1/',
    'repox':'http://repox.ist.utl.pt'
    }


# --- Ask for file ---
xmlFile = input('What xml file would you like to add rights statement to? (do not enter file extension)    ') + '.xml'


# --- Ask for values not in harvested xml ---
publicStatus = input('These records will be public. (enter true or false)   ')
dplaStatus = input('These records will be included in DPLA. (enter true or false)   ')
localStatus = input('These digital objects are hosted at the DLG. (enter true or false)   ')
portal = input('What portal(s) will these items be in? (Enter multiple values with a space between them: georgia crdl)   ')
collCode = input('What collection do these records belong to? (enter repo_coll)   ')

addColls = input('Do these records need to be added to additional collections? (y or n)   ')
if addColls == 'y':
    colls = input('Enter the additional collections with a space between them. (Ex. repo_coll repo_coll)    ')

baseUrl = input('What is the base URL for the item id?    ')


# --- Ask for dc version and adjust for repox formatting ---
dcVersion = input('Were these harvested as DC or QDC records? (Enter dc or qdc)    ')
if dcVersion == 'dc':
    dcValue = 'oai_dc:dc'
if dcVersion == 'qdc':
    dcValue = 'oai_qdc:qualifieddc'

slugPath = 'metadata/' + dcValue + '/dcterms:isShownAt'
nodePath = 'item/metadata/' + dcValue


# --- Parse file and remove blank space so pretty print will work ---
parser = etree.XMLParser(remove_blank_text=True)
tree = etree.parse(xmlFile, parser)
root = tree.getroot()


# --- Set up XML to have 'items/item' hierarchy ---
root.tag = 'items'
root.set('type', 'array')

for items in root.findall('record'):
    items.tag = 'item'


# --- Functions ---
def nestedFormat(item, oldtag):
    '''Converts to dlgadmin nested xml format, looks for the old tag,
    creates a new node and sets the type, nests new nodes with text values,
    then removes the old node'''
    fieldname = items.findall(str(oldtag), nsDict)
    if fieldname is not None:
        x = 0
        parent = item.getparent()
        grParent = parent.getparent()
        newEl = etree.Element(str(qdcFieldsDict[oldtag]))
        newEl.set('type', 'array')
        grParent.insert(0, newEl)
        for new in fieldname:
            new = etree.SubElement(newEl, str(qdcFieldsDict[oldtag]))
            new.text = fieldname[x].text
            newEl.append(new)
            item.remove(fieldname[x])
            x += 1


# --- Add inputted values ---
for items in root.findall('item'):

    # --- Add collection structure ---
    collection = etree.Element('collection')
    items.append(collection)
    recordId = etree.SubElement(collection, 'record_id')
    recordId.text = (str(collCode))
    collection.append(recordId)

    # --- Add additional collections if necessary ---
    if addColls == 'y':
        # --- Top level ---
        otherColls1 = etree.Element('other_colls')
        otherColls1.set('type', 'array')
        items.append(otherColls1)
        # --- Second level ---
        otherColls2 = etree.SubElement(otherColls1, 'other_coll')
        otherColls1.append(otherColls2)
        # --- Third level ---
        splitColls = colls.split()
        for entries in splitColls:
            newColl = etree.SubElement(otherColls2, 'record_id')
            newColl.text = (str(entries))

    # --- Add portal structure ---
    # --- Top level ---
    portal1 = etree.Element('portals')
    portal1.set('type', 'array')
    items.append(portal1)
    # --- Second level ---
    portal2 = etree.SubElement(portal1, 'portal')
    portal1.append(portal2)
    if ' ' in portal:
        portals = portal.split()
        for words in portals:
            portalCode = etree.SubElement(portal2, 'code')
            portalCode.text = (str(words))
    else:
        portalCode = etree.SubElement(portal2, 'code')
        portalCode.text = (str(portal))
        portal2.append(portalCode)

    #--- Add Public, DPLA, and local values ---
    public = etree.Element('public')
    public.set('type', 'boolean')
    public.text = (str(publicStatus))
    items.append(public)

    dpla = etree.Element('dpla')
    dpla.set('type', 'boolean')
    dpla.text = (str(dplaStatus))
    items.append(dpla)

    local = etree.Element('local')
    local.set('type', 'boolean')
    local.text = (str(localStatus))
    items.append(local)

    # --- Get item IDs (slugs) and add them to structure ---
    slug = etree.Element('slug')
    origUrl = items.find(slugPath, nsDict)
    ID = origUrl.text.replace(baseUrl, "")
    slug.text = ID
    items.append(slug)


# --- Do the processing on original xml ---
for items in root.findall(nodePath, nsDict):
    # --- Convert all the fields
    for keys in qdcFieldsDict:
        nestedFormat(items, keys)


# --- Strip out the nodes leftover from shuffling things around in the hierarchy ---
for leftovers in root.findall('item/metadata'):
    strip = leftovers.getparent()
    strip.remove(leftovers)


# --- Clean up extraneous attriubtes on nodes ---
etree.strip_attributes(root,"set", "batchsize", "id", "timestamp", "total")
etree.cleanup_namespaces(root)


# --- Create new xml file ---
filename = xmlFile
(prefix, sep, suffix) = filename.rpartition('.')

new_filename = prefix + '_batch.xml'
tree.write(new_filename, pretty_print=True, encoding="UTF-8", xml_declaration=True)

print('\n', 'Your new file,', new_filename, ', has been created.')
