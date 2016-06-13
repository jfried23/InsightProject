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
		return render_template('index.html', msg='', poi=0, sort_order=0, center={'lat':40.749364, 'lng':-73.987687} )

	else:

		loc1, loc2   =  request.form['loc1'], request.form['loc2']
		query        =  request.form['query']
		transit_mode =  request.form['transit_mode']

		currentHour = int(time.strftime("%H"))

		#try to fail gracefully
		try: loc1_geo = googlePOI.geocodeFromName(loc1)
		except: return render_template('index.html', poi=0, sort_order=0, center={'lat':40.749364, 'lng':-73.987687}, 
			msg='The starting location <font color="red"> %s </font> was not found. Please try with new position description.' %(loc1)) 

		try: loc2_geo = googlePOI.geocodeFromName(loc2)
		except: return render_template('index.html', poi=0, sort_order=0, center={'lat':40.749364, 'lng':-73.987687}, 
			msg='The starting location  <font color="red"> %s </font> was not found. Please try with new position description' %(loc2)) 


		try:
			midPoint, dist = MidPoint.searchMidPoint(loc1_geo, loc2_geo, gMapsKey, time='now', mode = transit_mode)
		except:
			return render_template('index.html', poi=0, sort_order=0, center={'lat':40.749364, 'lng':-73.987687}, 
			msg='No <font color=red> %s </font> directions were found between %s and %s.' %(transit_mode,loc1, loc2)) 

		#d1 = MidPoint.getDirections(loc1_geo, loc2_geo, gMapsKey, time='now', mode = transit_mode)
	
		if dist < 50000: dist= 500


		for i in range(5):
			pois = googlePOI.searchNearBy(gMapsKey, query, midPoint, radius=dist + i*.05*dist, minprice=0, maxprice=4)

			if (len(pois['results']) > 0) & (pois['status'] =='OK'): break

		#if no points of intrest found route back to stating page
		if pois['status'] == 'ZERO_RESULTS': 
			return render_template('index.html', poi=0, sort_order=0, center={'lat':40.749364, 'lng':-73.987687}, 
			msg='No establishments matching the query <font color=red> \"%s\" </font> were not found.' %(query)) 


		sort_order = 0
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


		if len(pois['results']) > 0:
			return render_template('index.html', msg='', poi = simplejson.dumps(pois), sort_order = list(sort_order), center={'lat':midPoint[0],'lng':midPoint[1]} )
		else:
			return render_template('index.html', msg='',poi=0, sort_order=0, center={'lat':midPoint[0], 'lng':midPoint[1]} )
if __name__ == "__main__":
	app.run(debug=True)
