from flask import Flask,render_template,request,redirect

import MidPoint
import googlePOI

import simplejson
import time
import numpy as np
import pandas as pd

import sqlalchemy




app = Flask(__name__)

#Load the API keys
keys = simplejson.load( open('./static/keys') )
gMapsKey = keys['GMapsApiKey']

#pois = {'status':'Bad'} 

@app.route("/logChoice", methods=['GET','POST'])
def getDirections():
	
	data = request.json
	a = time.localtime()


	#print time.strftime('%Y-%m-%d %H:%M:%S', a)
	#print data['user'], data['rating'], data['price_level'], data['fairness'], a
	if data['user'] != '':
		conn = sqlalchemy.create_engine('postgresql:///yelp')
		s = 'insert into users values (\'%s\', %f, %f, %f, \'%s\')' %(data['user'], data['rating'], data['price_level'], data['fairness']/100., time.strftime('%Y-%m-%d %H:%M:%S', a) )
		a=conn.execute(s)

	return render_template('index.html', msg='', poi=0, sort_order=0, center={'lat':40.749364, 'lng':-73.987687} )


@app.route('/', methods=['GET','POST'])
def index():

	if request.method == 'GET':
		return render_template('index.html', msg='', poi=0, sort_order=0, center={'lat':40.749364, 'lng':-73.987687} )

	else:

		loc1, loc2   =  request.form['loc1'], request.form['loc2']
		query        =  request.form['query']
		transit_mode =  request.form['transit_mode']
		userName     =  request.form['user_name']

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
		print midPoint

		for i in range(5):
			pois = googlePOI.searchNearBy(gMapsKey, query, midPoint, radius=dist + i*.05*dist, minprice=0, maxprice=4)

			if (len(pois['results']) > 3) & (pois['status'] =='OK'): break

		#if no points of intrest found route back to stating page
		if pois['status'] != 'OK': 
			return render_template('index.html', poi=0, sort_order=0, center={'lat':40.749364, 'lng':-73.987687}, 
			msg='No establishments matching the query <font color=red> \"%s\" </font> were not found.' %(query)) 
		#if we made it here pois status == OK
		
		#Populate the scoring matrix
		sort_order = 0
		fairness = []
		scores = np.zeros((len(pois['results']), 3))
		for idx, p in enumerate(pois['results']):
		
			wp =  (p['geometry']['location']['lat'], p['geometry']['location']['lng'])

			
			direct = MidPoint.getDirectionsWithWayPoint( loc1_geo, wp, loc2_geo, gMapsKey,  mode1=transit_mode, mode2=transit_mode)

			#Calculate the travel time for each person
			t1,t2=0.0,0.0
			for dd in direct[0]['routes'][0]['legs']: t1 += dd['duration']['value']
			for dd in direct[1]['routes'][0]['legs']: t2 += dd['duration']['value']

			pois['results'][idx]['duration']    = [t1,t2]
			pois['results'][idx]['fairness']    = int(100*round(min([t1,t2])/max([t1,t2]),2))
			pois['results'][idx]['path']        = { 'points1': direct[0]['routes'][0]['overview_polyline']['points'], 
									     'points2': direct[1]['routes'][0]['overview_polyline']['points'] } 
			fairness.append( min([t1,t2])/max([t1,t2]) )

			try: scores[idx][0] = float(p['price_level'])
			except: pass

			try: scores[idx][1] = float(p['rating'])
			except: pass

			try: scores[idx][2] = min([t1,t2])/max([t1,t2])
			except: pass



		#Now prepare user costimized ranking
		conn = sqlalchemy.create_engine('postgresql:///insight')
		s="select index from ny_tile where ST_Contains(st_geomfromtext, ST_GeomFromText( 'POINT(%f %f)', 4326) );" %(loc1_geo[1], loc1_geo[0])
		a=conn.execute(s).fetchall()
			

		try:
			s = 'select avg(score), avg(price), 1.0 from user_choice where reigon_id = %i' %(a[0][0])
			avg_score=conn.execute(s).fetchall()
		except: 
			s = 'select avg(score), avg(price), 1.0 from user_choice'
			avg_score=conn.execute(s).fetchall()

		avg_score = np.array([float(v) for v in avg_score[0]])

		#print avg_score

		dot =  np.dot(scores, avg_score) / ( np.linalg.norm(scores, axis=1) * np.linalg.norm(avg_score))
			
		#sort_order = np.argsort(dot)[::-1]
		sort_order = np.argsort(fairness)[::-1]

		for i, p in enumerate(pois['results']):
			pois['results'][i]['sim_score'] = round(dot[i],2)
			pois['results'][i]['idx_num'] = i
			pois['results'][i]['user'] = userName

		h=open('place.json','w')
		h.write( simplejson.dumps(pois) )
		h.close()
		
		return render_template('index.html', msg='', poi = simplejson.dumps(pois), sort_order = list(sort_order), center={'lat':midPoint[0],'lng':midPoint[1]} )
		
if __name__ == "__main__":
	app.run(debug=True)
