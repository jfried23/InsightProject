from flask import Flask,render_template,request,redirect
#import MidPoint
#import simplejson
#import googlePOI
#import time

app = Flask(__name__)

gMapsKey = "AIzaSyBJ0-ZPQengxtnHbCu1KotNA_yqyI_OD4Q"
callStr = "https://maps.googleapis.com/maps/api/js?callback=initMap&key="

@app.route('/',methods=['GET','POST'])
def index():

	if request.method == 'GET':
		return render_template('main.html')

	

if __name__ == "__main__":
	app.run(debug=True)