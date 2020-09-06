#Just an example how the dictionary may look like
devices = {
	'one' : {'floor' : 'fl1','position' : 'garage1/1'},
	'two' : {'floor' : 'fl2','position' : 'garage2/2'}	
	}
def whx(ownval,owndicts):
	for x in owndicts:
		if ownval in owndicts[x].values():
			return x
	return 'none'

print(whx('garage2',devices))
 #mydict.keys()[mydict.values().index(16)] 