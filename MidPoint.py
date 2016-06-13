import urllib2
import simplejson
import polyline
import time

def getDirections( p1, p2, key, time='now', mode='transit'):
	"""
	Returns json formmated travel directions from google.
		p1     --- tuple representing gps corrdinates (lat, long) representing starting point
		p2     --- tuple representing gps corrdinates (lat, long) representing ending point
		key    --- google API key
		time   --- time of day. Default = 'now'
		mode   --- key word describing the means of travel ['driving','walking','bicycling','transit']
	"""
	
	start    = '%s,%s' %( p1[0], p1[1])
	stop     = '%s,%s' %( p2[0], p2[1])
	htp      = "https://maps.googleapis.com/maps/api/directions/json?origin=%s&destination=%s&mode=%s&departure_time=%s&key=%s" %(start, stop, mode, time, key)
	jsonData = simplejson.loads( urllib2.urlopen(htp).read() )
	if jsonData['status'] != 'OK': print jsonData; raise ValueError
	else: return jsonData

def searchMidPoint(start, stop, key, mode='transit', time=time):
		jsonDir = getDirections( start, stop, key, time=time, mode = mode )

		if jsonDir == None: raise ValueError('No path found!')

		elif jsonDir['status'] == 'ZERO_RESULTS':
			jsonDir = getDirections( start, stop, key, time=time, mode = 'WALKING' )


		if jsonDir['status'] == 'OK':
			gps  =  findMidPoint(jsonDir) 
			return gps

		else: return None

def findMidPoint( jsonDir ):
	try:
		steps = jsonDir['routes'][0]['legs'][0]['steps']

		#First pass through all steps to find step containing midpoint
		lenOfStep = []
		trip_time = 0.0
		for step in steps:
			trip_time += step['duration']['value']
			lenOfStep.append( trip_time )
		
		trip_time *= 0.5  #The desired travel time for each Party

		#Find the step containing the midpoint of the journey
		keyStep = None
		for i, l in enumerate(lenOfStep):
			if l > trip_time:
				keyStep = i
				break
		
		#Now decode the midStep polyline into constinuent points and find middle one
		midStep =  steps[keyStep]
		points =  polyline.decode( midStep['polyline']['points'] )
		

		if keyStep > 0: netTime = 1.*trip_time - lenOfStep[keyStep-1]
		else:           netTime = 1.*trip_time

		avg_time_per_point = midStep['duration']['value']/len(points)*1.
		
		midIndex = int(round(netTime/(avg_time_per_point)))
		while midIndex > len(points) - 1: midIndex -=1
		
		midPointGPS =  points[midIndex]  #GPS corrdinates of middle point

		#TO DO LATER!!!!!!!!!!
		#if we are taking transit we cant just exit anywhere. Update midPointGPS to nearest stop
		if midStep['travel_mode'] == 'TRANSIT':
			lineInfo = midStep['transit_details']['line']['name'].replace(' ','+')
			#print lineInfo, midPointGPS

		dist = jsonDir['routes'][0]['legs'][0]['distance']['value']*0.5

		return midPointGPS, dist
	except: raise ValueError  

if __name__ == '__main__':
	keys = simplejson.load( open('./static/keys.json') )
	gMapsKey = keys['GMapsApiKey']
	

	start = 'Midtwon East New York'
	stop  = 'Brighton beach ny'

	start = 'east villiage'
	stop  = 'met museum'

	getFresh = True

	if getFresh:
		j = getDirections(start, stop, gMapsKey, time=int(time.time()+5) )
		print j
		#open('dir.data','w').write( simplejson.dumps(j) )
	else:
		j = simplejson.loads( open('dir.data','r').read() )

	print findMidPoint(j), time.time(), time.strftime("%H") > 12
