from flask import Flask, render_template, request
import pickle
import numpy 
import pytesseract
import pandas as pd
import cv2
import joblib
import math
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe'

#This function makes a pie chart
def make_pie_chart(dic):
	c,tf,p,s,sod=0,0,0,0,0

	for item in dic.keys():
		if(not  math.isnan(dic[item][0])):
			c=c+int(dic[item][0])
		if(not  math.isnan(dic[item][1])):
			tf=tf+int(dic[item][1])
		if(not  math.isnan(dic[item][2])):
			p=p+int(dic[item][2])
		if(not  math.isnan(dic[item][3])):
			s=s+int(dic[item][3])
		sod=sod+int(dic[item][4])
	labels = ['Calories','Fat','Protein','Sugar','Sodium']
	sizes=[c,tf,p,s,sod]
	explode = (0.03, 0.03,0.03,0.03,0.03)  # only "explode" the 2nd slice (i.e. 'Hogs')
	colors = ['#ff6699','#ffff00','#99ff99','#ffaa99','#66b3ff',]
	fig1, ax1 = plt.subplots()
	ax1.pie(sizes,colors = colors,explode=explode, labels=labels, autopct='%1.1f%%',shadow=True, startangle=90,pctdistance=0.85,)
	centre_circle = plt.Circle((0,0),0.70,fc='white')
	fig = plt.gcf()
	fig.gca().add_artist(centre_circle)
	ax1.axis('equal')  
	plt.tight_layout()
	plt.savefig('static/pie_chart.png')

#This function uses a previously trained clustering algorithm's weights to generate recommendations	
def get_recommendations(dic):
	avg_cal= 0
	avg_fat= 0
	avg_pro= 0
	avg_carb= 0
	for item in dic.keys():
		avg_cal=avg_cal+(dic[item][0]).astype(float)
		avg_fat=avg_fat+(dic[item][1]).astype(float)
		avg_pro=avg_pro+(dic[item][2]).astype(float)
		avg_carb=avg_carb+(dic[item][5]).astype(float)
	avg_cal=avg_cal.tolist()
	avg_fat=avg_fat.tolist()
	avg_pro=avg_pro.tolist()
	avg_carb=avg_carb.tolist()

	res=[avg_cal,avg_fat,avg_pro,avg_carb]
	res=numpy.expand_dims(res,0)
	kmeans = joblib.load("kmeans1.sav")
	print(res.shape)
	print(type(res[0]))
	c=kmeans.predict(res)
	df=pd.read_csv('cluster_df.csv')
	l=[]
	
	for name,category in  zip(df['Food and Serving'], df['Cluster']):
		if category==c:
			l.append(name)
	return l


@app.route("/")
def home():
	return render_template('home.html')

#This function accepts the shopping list, identifies items from it, sorts the items in order, gets recommendations and pie chart
@app.route("/", methods=['POST'])
def get_info():
	filestr = request.files['img'].read()
	#convert string data to numpy array
	npimg = numpy.fromstring(filestr, numpy.uint8)
	# convert numpy array to image
	image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
	l=pytesseract.image_to_string(image)
	items=l.split("\n")
	df=pd.read_csv('cluster_df.csv')
	d={}

	for item in items:
		for elem in range(len(df['Calories'])):
			if df['Food and Serving'][elem]==item:
				d[item]=[df['Calories'][elem],df['Total Fat'][elem],df['Protein'][elem],df['Sugars'][elem],df['Sodium'][elem],df['Total Carbo-hydrate'][elem]]
	l=d.keys()
	cals = sorted(l, key=lambda x: d[x][0], reverse=True)
	fats=  sorted(l, key=lambda x: d[x][1], reverse=True)
	make_pie_chart(d)
	rec_items=get_recommendations(d)
	with open('data.pickle','wb') as file:
		pickle.dump(d,file) 
	
	return render_template('details.html',d=d,cals=cals,fats=fats,lim=3,recom=rec_items)

#This function deleted the item from the list and updates the pie chart accordingly
@app.route("/delete/<item>")
def remove_item(item):
	with open('data.pickle','rb') as file:
		d=pickle.load(file)

	print(d.keys())
	del d[str(item)]
	cals = sorted(d.keys(), key=lambda x: d[x][0], reverse=True)
	fats=  sorted(d.keys(), key=lambda x: d[x][1], reverse=True)
	make_pie_chart(d)
	with open('data.pickle','wb') as file:
		pickle.dump(d,file)
	return render_template('details.html',d=d,cals=cals,fats=fats,lim=3)

if __name__=='__main__':
	app.run()
