from flask import Flask,render_template,request,redirect
#import MidPoint
#import simplejson
#import googlePOI
#import time

app = Flask(__name__)

gMapsKey = "AIzaSyBJ0-ZPQengxtnHbCu1KotNA_yqyI_OD4Q"
callStr = "https://maps.googleapis.com/maps/api/js?callback=initMap&key="

@app.route('/', methods=['GET','POST'])
def index():

	if request.method == 'GET':
		return render_template('index.html')

	else:
		loc1, loc2   =  request.form['loc1'], request.form['loc2']
		querry       =  request.form['querry']
		transit_mode =  request.form['transit_mode']

		print loc1, loc2, querry, transit_mode

		return render_template('index.html')

if __name__ == "__main__":
	app.run(debug=True)
