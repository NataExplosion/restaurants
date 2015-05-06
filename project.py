from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
  state = ''.join(random.choice(string.ascii_uppercase +string.digits) for x in xrange(32))
  login_session['state'] = state
  s = "The current session state is " + login_session['state']
  return render_template('login.html', state=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
  if request.args.get('state') != login_session['state']:
    response = make_response(json.dumps('Invalid state parameter'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  code = request.data
  try:
    oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
    oauth_flow.redirect_uri = 'postmessage'
    credentials = oauth_flow.step2_exchange(code)
  except FlowExchangeError:
    response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  access_token = credentials.access_token
  url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
  h = httplib2.Http()
  result = json.loads(h.request(url, 'GET')[1])
  if result.get('error') is not None:
    response = make_response(json.dumps(result.get('error')), 500)
    response.headers['Content-Type'] = 'application/json'
    return response
  gplus_id = credentials.id_token['sub']
  if result['user_id'] != gplus_id:
    response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401) 
    response.headers['Content-Type'] = 'application/json'
    return response
  stored_access_token = login_session.get('access_token')
  stored_gplus_id = login_session.get('gplus_id')
  if stored_access_token is not None and gplus_id == stored_gplus_id:
    response = make_response(json.dumps('Current user is already connected.'), 200)
    response.headers['Content-Type'] = 'application/json'
  
  login_session['access_token'] = access_token
  login_session['gplus_id'] = gplus_id

  userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
  params = {'access_token': access_token, 'alt': 'json'}
  answer = requests.get(userinfo_url, params=params)
  data = json.loads(answer.text)

  login_session['username'] = data["name"]
  login_session['picture'] = data["picture"]
  login_session['email'] = data["email"]


  output = ''
  output += '<img src=" '
  output += login_session['picture']
  output += ' " style = "width:300px; height:300px; border-radius:150px; -webkit-border-radius:150px; -moz-border-radius:150px;">'
  flash("you are now logged in as %s"%login_session['username'])
  return output

@app.route('/gdisconnect')
def gdisconnect():
  credentials = login_session.get('credentials')
  if credentials is None:
    response = make_response(json.dumps("Current user not connected."), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  access_token = credentials.access_token
  url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' %access_token
  h = httplib2.Http()
  result = h.request(url, 'GET')[0]

  if result['status'] == '200':
    del login_session['credentials']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    response = make_response(json.dumps('Successfully disconnected.'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response
  else:
    response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/restaurants/JSON')
def restaurantJSON():
  rests = session.query(Restaurant).all()
  return jsonify(MenuRestaurants=[r.serialize for r in rests]) 

@app.route('/restaurants/<int:restaurant_id>/JSON')
def restaurantItemJSON(restaurant_id):
  restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
  return jsonify(restaurant.serialize) 

@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
  restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
  items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
  return jsonify(MenuItems=[i.serialize for i in items])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def restaurantMenuItemJSON(restaurant_id, menu_id):
  item = session.query(MenuItem).filter_by(id = menu_id).one()
  return jsonify(item.serialize)

@app.route('/')
@app.route('/restaurants/')
def restaurants():
  rests = session.query(Restaurant).all()
  return render_template('rests.html', rests = rests)

@app.route('/restaurants/new', methods = ['GET', 'POST'])
def newRestaurant():
  if 'username' not in login_session:
    return redirect('/login')
  if request.method == 'POST':
    restaurant = Restaurant(name = request.form['name'])
    session.add(restaurant)
    session.commit()
    flash("new restaurant created!")
    return redirect(url_for('restaurants'))
  else:
    return render_template('newrestaurant.html')

@app.route('/restaurants/<int:restaurant_id>/edit', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
  if 'username' not in login_session:
    return redirect('/login')
  editedRestaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
    if request.form['name']:
      editedRestaurant.name = request.form['name']
    session.add(editedRestaurant)
    session.commit()
    flash("restaurant was edited!")
    return redirect(url_for('restaurants'))
  else:
    return render_template('editrestaurant.html', restaurant = editedRestaurant)

@app.route('/restaurants/<int:restaurant_id>/delete', methods = ['GET', 'POST'])
def deleteRestaurant(restaurant_id):
  if 'username' not in login_session:
    return redirect('/login')
  deletedRestaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
    session.delete(deletedRestaurant)
    session.commit()
    flash("restaurant was deleted!")
    return redirect(url_for('restaurants'))
  else:
    return render_template('deleterestaurant.html', restaurant = deletedRestaurant)


@app.route('/restaurants/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
  restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
  items = session.query(MenuItem).filter_by(restaurant_id = restaurant.id)
  return render_template('menu.html', restaurant=restaurant, items=items)

#Task 1: Create route for newMenuItem function here
@app.route('/restaurants/<int:restaurant_id>/new', methods = ['GET', 'POST'])
def newMenuItem(restaurant_id):
  if 'username' not in login_session:
    return redirect('/login')
  if request.method == 'POST':
    newItem = MenuItem(name = request.form['name'],description = request.form['description'], price = request.form['price'], restaurant_id=restaurant_id)
    session.add(newItem)
    session.commit()
    flash("new menu item created!")
    return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
  else:
    return render_template('newmenuitem.html',restaurant_id = restaurant_id)

#Task 2: Create route for editMenuItem function here
@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
  if 'username' not in login_session:
    return redirect('/login')
  editedItem = session.query(MenuItem).filter_by(id = menu_id).one()
  if request.method == 'POST':
    if request.form['name']:
      editedItem.name = request.form['name']
    if request.form['description']:
      editedItem.description = request.form['description']
    if request.form['price']:
      editedItem.price = request.form['price']
    session.add(editedItem)
    session.commit()
    flash("menu item was edited!")
    return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
  else:
    return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = editedItem)

#Task 3: Create a route for deleteMenuItem function here
@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete', methods = ['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
  if 'username' not in login_session:
    return redirect('/login')
  deletedItem = session.query(MenuItem).filter_by(id = menu_id).one()
  if request.method == 'POST':
    session.delete(deletedItem)
    session.commit()
    flash("menu item was deleted!")
    return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
  else:
    return render_template('deletemenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = deletedItem)
    
if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
