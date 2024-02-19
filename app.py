from flask import Flask,request,jsonify,redirect ,session ,url_for 
from flask_jwt_extended import JWTManager,jwt_required,create_access_token ,get_jwt_identity,get_current_user
from pymongo import MongoClient

from gridfs import GridFS
from flask_cors import CORS
import os
import json
import requests
from dotenv import  load_dotenv
load_dotenv()

from pathlib import Path
from datetime import datetime,timedelta

load_dotenv()
#from authlib.integrations.flask_client import OAuth
import datetime 
app  = Flask(__name__)
CORS(app, origins='http://localhost:5173', supports_credentials=True)

app.secret_key = os.urandom(12)


app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
jwt = JWTManager(app)
client = MongoClient('mongodb://localhost:27017/')
db = client['AI_database']

@app.route('/chef/signup' ,methods =['POST'])
def sign_up():

    if request.method  == 'POST':
        data = request.get_json()

        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        password = data.get('password')
        password_repeat= data.get('password_repeat')
        


        exist_user  =db.AllUser.find_one({'email':email},{'first_name':1})
        print(first_name)

        if exist_user:
            return jsonify({"message":"User Already registered"}),409
        if password != password_repeat:
            return jsonify({'Message':'Password not match'})
        db.AllUser.insert_one({'first_name':first_name ,'last_name':last_name,'email':email,'password':password})
        
        return jsonify({'message':'SignUp Successful'}),201
  
@app.route('/chef/login' ,methods =['POST'])
def login():
    if request.method =='POST':
        data=request.get_json()

        email = data.get('email')
        password  = data.get('password')
        session['email'] = email
        
        login_user = db.AllUser.find_one({'email':email ,'password':password})
        if login_user:
            access_token = create_access_token(identity= email)
           
            login_user = db.AllUser.find_one({'email':email},{'first_name':1 ,'last_name':1})

            kname = login_user['first_name']+" "+login_user['last_name']
            session['is_login'] = True
            return jsonify(message = 'Login Successful',access_token = access_token ,email = email ,name = kname)
        else:
            return  jsonify({'Message':'Invalid email and password'}),401


@app.route('/google_login',methods = ['POST'])
def google_login():
    auth_code = request.get_json()['code']

    data = {
        'code':auth_code,
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret':os.getenv('GOOGLE_SECRET_KEY'),
        'redirect_uri':'/chef/createDish',
        'grant_type':'authorization_code'
    
    }
    response = requests.post('https://oauth2.googleapis.com/token',data = data).json()
    headers ={
        'Authorization':f'Bearer {response["access_token"]}'
    }

    user_info = requests.get('https://www.googleapis.com/oauth2/v3/userinfo' ,headers = headers).json()

    token = create_access_token(identity= user_info['email'])

    return jsonify({'access_token':token,'user_info':user_info })

@app.route('/chef/createDish',methods = ['POST'])
@jwt_required()
def create_dish():
    
    user_info = get_jwt_identity()
    
    login_user = db.AllUser.find_one({'email':user_info},{'first_name':1 ,'last_name':1})

    kname = login_user['first_name']+" "+login_user['last_name']

    #dish_name =  request.form.get('name')
    #veg_non_veg = request.form.get('veg_non_veg')
   # description = request.form.get('description')

    #pop_state = request.form.get('popularity_state')

    #cuisine = request.form.get('cuisine')
    #kitchen_equi = request.form.get('kitchen_equipments')
    #course_type= request.form.get('course_type')

    temp = request.get_json()
    instructions = request.get_json()
    dish_name  = temp['name']
    veg_non_veg = temp['veg_non_veg']
    description = temp['description']
    pop_state = temp['popularity_state']
    cuisine = temp['cuisine']
    #image = temp['image']
    cooking_time = temp['cooking_time']
    kitchen_equip = temp['kitchen_equipments']
    course = temp['courses']

    ingre = temp['ingredients']
    instru = temp['instructions']

    formatted_time = datetime.datetime.now().strftime("%H:%M:%S")
    formatted_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    db.Dish.insert_one({"created_by":kname ,"indegrients": ingre,"instructions":instru ,"description":description,"dish_name":dish_name,"veg_non_veg":veg_non_veg,"popularity_state":pop_state,"Cuisine":cuisine,"cooking_time":cooking_time,"kitchen_equipments":kitchen_equip,"courses":course,"Created_date":formatted_date,"Created_time":formatted_time,"email":user_info})
    
    return jsonify({'Message':'Dished Saved Successfully'}),201

    
@app.route('/myAccount',methods = ['GET'])
@jwt_required()
def myAccount():

    user_info = get_jwt_identity()   
    login_user = db.AllUser.find_one({'email':user_info},{'first_name':1 ,'last_name':1})
    name = login_user['first_name']+" " +login_user['last_name']
    '''
    if filterCuisine =="Indian" or filterCuisine == "Chinese":
        dis = db.Dish.find({"created_by":name ,"Cuisine":filterCuisine,"email":user_info})
        
        output =[]
        for dish in dis:
            dish_data = {
                "id":str(dish['_id']),
                "name" :dish['dish_name'],
                "cuisine":dish['Cuisine'],
                "veg_non":dish['veg_non_veg'],
                "course_type":dish['courses'],
                "Created_date":dish['Created_date'],
                "Created_time":dish['Created_time'],
                "description":dish['description']   
            }
            output.append(dish_data)

        print("heello 8")
        return jsonify(output)
    
    else:
    
    '''
    All_dis = db.Dish.find({'email':user_info})
    output3  =[]

    for dish in All_dis:
        dish_data = {
                "id":str(dish['_id']),
                "name" :dish['dish_name'],
                "cuisine":dish['Cuisine'],
                "veg_non":dish['veg_non_veg'],
                "course_type":dish['courses'],
                "created_date":dish['Created_date'],
                "created_time":dish['Created_time'],
                "description":dish['description']   
        }
        output3.append(dish_data)

    return jsonify(output3)
    


@app.route('/api/dish/filter/<string:id>/id/',methods =['GET'])
@jwt_required()
def  filter_by_id(id):

    dishes = db.Dish.find({'_id':id})

    return jsonify(dishes)

@app.route('/show')
@jwt_required()
def show():
    user_info  = get_jwt_identity()
    login_user = db.AllUser.find_one({'email':user_info},{'first_name':1 ,'last_name':1})
    name = login_user['first_name']  +" " + login_user['last_name']
    return jsonify({'name':name ,'email':user_info}) 
    
@app.route('/api/contact',methods =['POST'])
def contact():

    data = request.get_json()
    name = data['name']
    email = data['email']
    message =data['message']

    db.Contact.insert_one({'name':name,'email':email ,'message':message})

    return jsonify({"Message":"Message submitted succesfully"})




if __name__ =="__main__":
    app.run(debug= True)
    