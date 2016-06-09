from flask import Flask,render_template,request,redirect
import MidPoint
import simplejson
import time
import numpy as np

import googlePOI


app = Flask(__name__)

keys = simplejson.load( open('./static/keys') )

gMapsKey = keys['GMapsApiKey']
callStr = "https://maps.googleapis.com/maps/api/js?callback=initMap&key="

@app.route('/', methods=['GET','POST'])
def index():

	if request.method == 'GET':
		return render_template('index.html', poi=0, center={'lat':40.749364, 'lng':-73.987687} )

	else:
		loc1, loc2   =  request.form['loc1'], request.form['loc2']
		query       =  request.form['query']
		transit_mode =  request.form['transit_mode']
		price        =  request.form['price']
		review       =  request.form['review']

		currentHour = int(time.strftime("%H"))

		loc1_geo = googlePOI.geocodeFromName(loc1)
		loc2_geo = googlePOI.geocodeFromName(loc2)

		midPoint, dist = MidPoint.searchMidPoint(loc1, loc2, gMapsKey, time='now', mode = transit_mode)

		if dist < 10000: dist= 500

		for i in range(5):
			pois = googlePOI.searchNearBy(gMapsKey, query, midPoint, radius=dist+i*dist*.05, minprice=0, maxprice=4)
			if (len(pois['results']) > 0) & (pois['status'] =='OK'): break
			i+=1


		if pois['status'] =='OK':
			scores = np.zeros((len(pois['results']), 3))

			for idx, p in enumerate(pois['results']):
			
				try: scores[idx][0] = float(p['price_level'])
				except: pass

				try: scores[idx][1] = float(p['rating'])
				except: pass

				try: scores[idx][2] = float(p['opening_hours']['open_now'])
				except: pass

			print scores
			print price, review



		return render_template('index.html', poi = simplejson.dumps(pois), center={'lat':midPoint[0],'lng':midPoint[1]} )

if __name__ == "__main__":
	app.run(debug=True)
