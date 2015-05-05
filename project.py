from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

from flask import session as login_session
import random, string

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
  state = ''.join(random.choice(string.ascii_uppercase +string.digits) for x in xrange(32))
  login_session['state'] = state
  s = "The current session state is " + login_session['state']
  return render_template('login.html')

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
