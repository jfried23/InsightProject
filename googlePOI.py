import urllib2
import simplejson

def searchNearBy(key, keyWord, gpsCorr, radius=500, minprice=0, maxprice=4):
	keyWord = keyWord.replace(' ','+')
	htp = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=%f,%f&radius=%f&keyword=%s&minprice=%i&maxprice=%i&key=%s' %(gpsCorr[0],gpsCorr[1],radius,keyWord,minprice,maxprice,key)
	return simplejson.loads( urllib2.urlopen(htp).read() )

def geocodeFromName(address):
	h = "http://maps.google.com/maps/api/geocode/json?address=%s&sensor=false" % (address.replace(' ','+'))
	data = simplejson.loads( urllib2.urlopen(h).read() )
	if data['status'] == 'OK':
		corr = data['results'][0]['geometry']['location']
		return (corr['lat'], corr['lng'])

if __name__ == '__main__':

	radius = 500
	pos = (40.73033, -73.99263)
	keyword = 'pizza'

	print geocodeFromName('545 1st ave, new york ny')

	#json = searchNearBy(gMapsKey, keyword, pos, radius=1000)
	#print json
	#open('./data.json','w').write( simplejson.dumps(json) )