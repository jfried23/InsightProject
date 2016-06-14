import urllib2
import simplejson

def searchNearBy(key, keyWord, gpsCorr, radius=500, minprice=0, maxprice=4):
	"""
	Preforms a google places search, returing a json representation of the results.
	"""
	keyWord = keyWord.replace(' ','+')
	htp = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?opennow=true&location=%f,%f&radius=%f&keyword=%s&minprice=%i&maxprice=%i&key=%s' %(gpsCorr[0],gpsCorr[1],radius,keyWord,minprice,maxprice,key)
	results = simplejson.loads( urllib2.urlopen(htp).read() )
	return results

def geocodeFromName(address):
	h = "http://maps.google.com/maps/api/geocode/json?address=%s&sensor=false" % (address.replace(' ','+'))
	data = simplejson.loads( urllib2.urlopen(h).read() )
	if data['status'] == 'OK':
		corr = data['results'][0]['geometry']['location']
		return (corr['lat'], corr['lng'])
	else: raise ValueError

if __name__ == '__main__':

	radius = 500
	pos = (40.72892, -74.00859)
	keyword = 'pizza'

	keys = simplejson.loads( open('./static/keys.json').read() )
	gMapsKey=keys['GMapsApiKey']
	print geocodeFromName('545 1st ave, new york ny')
	print geocodeFromName('upper west side, ny')

	json = searchNearBy(gMapsKey, keyword, pos, radius=1000)
	print json
	#open('./data.json','w').write( simplejson.dumps(json) )