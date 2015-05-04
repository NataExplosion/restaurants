from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
from database_setup import Base, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()



class webServerHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		try:
			if self.path.endswith("/hello"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				output = ""
				output += "<html><body>"
				output += "<h1>Hello!</h1>"
				output += '''<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?</h2><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
				output += "</body></html>"
				self.wfile.write(output)
				print output
				return

			if self.path.endswith("/restaurants"):
				restaurants = session.query(Restaurant).all()
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				output = ""
				output += "<html><body>"
				output += '<a href="restaurants/new">Create a new restaurant</a></br></br>'		
				for r in restaurants:
					output += r.name
					output += '</br>' 
					output += '<a href ="restaurants/' + str(r.id) + '/edit">Edit</a></br>'
					output += '<a href ="restaurants/' + str(r.id) + '/delete">Delete</a></br></br>'
				output += "</body></html>"
				self.wfile.write(output)
				print output
				return

			if self.path.endswith("/restaurants/new"):
				#import pdb; pdb.set_trace()
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				output = ""
				output += "<html><body>"
				output += "<h1>Create a new restaurant</h1>"
				output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants/new'><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
				output += "</body></html>"
				self.wfile.write(output)
				print output
				return

			if self.path.endswith("/edit"):
				id_rest = self.path.split("/")[2]
				edit_restaurant = session.query(Restaurant).filter_by(id=id_rest).one()
				#import pdb; pdb.set_trace()
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				output = ""
				output += "<html><body>"
				output += "<h1>Edit " + edit_restaurant.name +"</h1>"
				output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants/''' + id_rest + '''/edit'><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
				output += "</body></html>"
				self.wfile.write(output)
				print output
				return

			if self.path.endswith("/delete"):
				id_rest = self.path.split("/")[2]
				delete_restaurant = session.query(Restaurant).filter_by(id=id_rest).one()
				#import pdb; pdb.set_trace()
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				output = ""
				output += "<html><body>"
				output += "<h1>Are you sure you want to delete " + delete_restaurant.name +"?</h1>"
				output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants/''' + id_rest + '''/delete'><input type="submit" value="Delete"> </form>'''
				output += "</body></html>"
				self.wfile.write(output)
				print output
				return
				
			if self.path.endswith("/hola"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				output = ""
				output += "<html><body>"
				output += "<h1>&#161 Hola !</h1>"
				output += '''<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?</h2><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
				output += "</body></html>"
				self.wfile.write(output)
				print output
				return

		except IOError:
			self.send_error(404, 'File Not Found: %s' % self.path)


	def do_POST(self):
		try:
			if self.path.endswith("/delete"):
				#import pdb; pdb.set_trace()
				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields=cgi.parse_multipart(self.rfile, pdict)
				id_rest = self.path.split("/")[2]
				delete_restaurant = session.query(Restaurant).filter_by(id=id_rest).one()
				session.delete(delete_restaurant)
				session.commit()
				
				self.send_response(301)
				self.send_header('Content-type', 'text/html')
				self.send_header('Location', '/restaurants')
				self.end_headers()

			if self.path.endswith("/edit"):
				#import pdb; pdb.set_trace()
				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields=cgi.parse_multipart(self.rfile, pdict)
				messagecontent = fields.get('message')
				id_rest = self.path.split("/")[2]
				edit_restaurant = session.query(Restaurant).filter_by(id=id_rest).one()
				edit_restaurant.name = messagecontent[0]
				session.add(edit_restaurant)
				session.commit()
				
				self.send_response(301)
				self.send_header('Content-type', 'text/html')
				self.send_header('Location', '/restaurants')
				self.end_headers()
			if self.path.endswith("/hello"):
				self.send_response(301)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields=cgi.parse_multipart(self.rfile, pdict)
					messagecontent = fields.get('message')
				output = ""
				output +=  "<html><body>"
				output += " <h2> Okay, how about this: </h2>"
				output += "<h1> %s </h1>" % messagecontent[0]
				output += '''<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?</h2><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
				output += "</body></html>"
				self.wfile.write(output)
				print output

			if self.path.endswith("/restaurants/new"):
				#import pdb; pdb.set_trace()
				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields=cgi.parse_multipart(self.rfile, pdict)
				messagecontent = fields.get('message')
				restaurant = Restaurant(name = messagecontent[0])
				session.add(restaurant)
				session.commit()
				
				self.send_response(301)
				self.send_header('Content-type', 'text/html')
				self.send_header('Location', '/restaurants')
				self.end_headers()
					
		except:
			pass


def main():
	try:
		port = 8080
		server = HTTPServer(('', port), webServerHandler)
		print "Web Server running on port %s"  % port
		server.serve_forever()
	except KeyboardInterrupt:
		print " ^C entered, stopping web server...."
		server.socket.close()

if __name__ == '__main__':
	main()
