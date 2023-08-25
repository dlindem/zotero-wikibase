import lwbi

newprop = lwbi.wbi.
property.new(datatype='wikibase-item')
newprop.labels.set('en', 'test property')
newprop.write()
