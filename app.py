from flask import Flask,render_template,request,redirect
import MidPoint
import simplejson
import time
import numpy as np
import sqlalchemy

import googlePOI


app = Flask(__name__)

keys = simplejson.load( open('./static/keys') )

gMapsKey = keys['GMapsApiKey']
callStr = "https://maps.googleapis.com/maps/api/js?callback=initMap&key="

@app.route('/', methods=['GET','POST'])
def index():

	if request.method == 'GET':
		return render_template('index.html', poi=0, sort_order=0, center={'lat':40.749364, 'lng':-73.987687} )

	else:
		loc1, loc2   =  request.form['loc1'], request.form['loc2']
		query       =  request.form['query']
		transit_mode =  request.form['transit_mode']
		#price        =  request.form['price']
		#review       =  request.form['review']

		currentHour = int(time.strftime("%H"))

		loc1_geo = googlePOI.geocodeFromName(loc1)
		loc2_geo = googlePOI.geocodeFromName(loc2)

		midPoint, dist = MidPoint.searchMidPoint(loc1, loc2, gMapsKey, time='now', mode = transit_mode)
		d1 = MidPoint.getDirections(str(loc1_geo).replace(',', ' '), str(midPoint).replace(',', ' '), gMapsKey, time='now', mode = transit_mode)
		print d1
		print str(loc1_geo).replace(',', ' '), str(midPoint).replace(',', ' ')

		if dist < 50000: dist= 500

		for i in range(5):
			pois = googlePOI.searchNearBy(gMapsKey, query, midPoint, radius=dist + i*.05*dist, minprice=0, maxprice=4)
			if (len(pois['results']) > 0) & (pois['status'] =='OK'): break
			i+=1


		if pois['status'] =='OK':
			scores = np.zeros((len(pois['results']), 2))

			for idx, p in enumerate(pois['results']):
			
				try: scores[idx][0] = float(p['price_level'])
				except: pass

				try: scores[idx][1] = float(p['rating'])
				except: pass


			conn = sqlalchemy.create_engine('postgresql:///insight')
			s="select index from ny_tile where ST_Contains(st_geomfromtext, ST_GeomFromText( 'POINT(%f %f)', 4326) );" %(loc1_geo[1], loc1_geo[0])
			a=conn.execute(s).fetchall()
			

			try:
				s = 'select avg(score), avg(price) from user_choice where reigon_id = %i' %(a[0][0])
				avg_score=conn.execute(s).fetchall()
			except: 
				s = 'select avg(score), avg(price) from user_choice'
				avg_score=conn.execute(s).fetchall()

			avg_score = np.array([float(v) for v in avg_score[0]])

			dot =  np.dot(scores, avg_score) / ( np.linalg.norm(scores, axis=1) * np.linalg.norm(avg_score))
			
			sort_order = np.argsort(dot)[::-1]

			for i, p in enumerate(pois['results']):
				pois['results'][i]['sim_score'] = round(dot[i],2)



		return render_template('index.html', poi = simplejson.dumps(pois), order = list(sort_order), center={'lat':midPoint[0],'lng':midPoint[1]} )

if __name__ == "__main__":
	app.run(debug=True)
