#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from xmlrpc.client import FastParser
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
import datetime
from models import Artist, Venue, Shows, db

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
#db = SQLAlchemy(app)
db.init_app(app)

migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models. ----- Seperation of concerns: moved to models.py -------
#----------------------------------------------------------------------------#
'''
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable = False, default = False)
    seeking_description = db.Column(db.String(1000))


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, nullable = False, default = False)
    seeking_description = db.Column(db.String(1000))


class Shows(db.Model):
    __tablename__ = 'Shows'

    id = db.Column(db.Integer, primary_key = True)
    start_time = db.Column(db.DateTime, nullable = False)
    venue = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable = False)
    artist = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable = False)'''


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  venues = Venue.query.all()

  data = []

  current_time = datetime.datetime.utcnow()

  # - Iterate over venues and sort by cities
  for venue in venues:
    if not data:
      data.append({
        'city': venue.city,
        'state': venue.state,
        'venues': [{
          'id': venue.id,
          'name': venue.name,
          'num_upcoming_shows': Shows.query.filter(Shows.venue == venue.id).filter(Shows.start_time < current_time).count()
        }]
      })
    else:
      inserted = False
      for place in data:
        if(place['city'] == venue.city and place['state'] == venue.state):
          place['venues'].append({
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': Shows.query.filter(Shows.venue == venue.id).filter(Shows.start_time < current_time).count()
          })
          inserted = True
      if not inserted:
        data.append({
          'city': venue.city,
          'state': venue.state,
          'venues': [{
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': Shows.query.filter(Shows.venue == venue.id).filter(Shows.start_time < current_time).count()
          }]
        })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():

  venues = Venue.query.filter(Venue.name.ilike(f'%{request.form.get("search_term", "")}%') )
  
  data = []
  
  current_time = datetime.datetime.utcnow()

  for venue in venues:
    data.append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': Shows.query.filter(Shows.venue == venue.id).filter(Shows.start_time < current_time).count()
    })
  
  response = {
    'count': venues.count(),
    'data': data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = Venue.query.get(venue_id)

  current_time = datetime.datetime.utcnow()
  upcoming_shows = Shows.query.filter(Shows.venue == venue_id).filter(Shows.start_time > current_time)
  past_shows = Shows.query.filter(Shows.venue == venue_id).filter(Shows.start_time < current_time)

  upcoming_shows_list = []
  past_shows_list = []

  for upcoming_show in upcoming_shows:
    artist = Artist.query.get(upcoming_show.artist)
    upcoming_shows_list.append({
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': upcoming_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for past_show in past_shows:
    artist = Artist.query.get(past_show.artist)
    past_shows_list.append({
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': past_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  data = {
    'id': venue.id,
    'name': venue.name,
    'genres': venue.genres.split(', '),
    'city': venue.city,
    'state': venue.state,
    'phone': venue.phone,
    'website': venue.website_link,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link,
    'past_shows': past_shows_list,
    'upcoming_shows': upcoming_shows_list,
    'past_shows_count': past_shows.count(),
    'upcoming_shows_count': upcoming_shows.count(),
  }

  data1={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    "past_shows": [{
      "artist_id": 4,
      "artist_name": "Guns N Petals",
      "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
      "start_time": "2019-05-21T21:30:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  data2={
    "id": 2,
    "name": "The Dueling Pianos Bar",
    "genres": ["Classical", "R&B", "Hip-Hop"],
    "address": "335 Delancey Street",
    "city": "New York",
    "state": "NY",
    "phone": "914-003-1132",
    "website": "https://www.theduelingpianos.com",
    "facebook_link": "https://www.facebook.com/theduelingpianos",
    "seeking_talent": False,
    "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
    "past_shows": [],
    "upcoming_shows": [],
    "past_shows_count": 0,
    "upcoming_shows_count": 0,
  }
  data3={
    "id": 3,
    "name": "Park Square Live Music & Coffee",
    "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
    "address": "34 Whiskey Moore Ave",
    "city": "San Francisco",
    "state": "CA",
    "phone": "415-000-1234",
    "website": "https://www.parksquarelivemusicandcoffee.com",
    "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
    "seeking_talent": False,
    "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    "past_shows": [{
      "artist_id": 5,
      "artist_name": "Matt Quevedo",
      "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
      "start_time": "2019-06-15T23:00:00.000Z"
    }],
    "upcoming_shows": [{
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-01T20:00:00.000Z"
    }, {
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-08T20:00:00.000Z"
    }, {
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-15T20:00:00.000Z"
    }],
    "past_shows_count": 1,
    "upcoming_shows_count": 1,
  }
  #data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  error = False

  try:
    venue = Venue(
      name = request.form.get('name'),
      city = request.form.get('city'),
      state = request.form.get('state'),
      address = request.form.get('address'),
      phone = request.form.get('phone', 'Not provided'),
      genres = ', '.join(request.form.getlist('genres')),
      image_link = request.form.get('image_link', 'Default immage link'), #TODO
      facebook_link = request.form.get('facebook_link'),
      website_link = request.form.get('website_link', 'No website available.'),
      seeking_talent = True if request.form.get('seeking_talent', False) == 'y' else False,
      seeking_description = request.form.get('seeking_description', '')
    )
    db.session.add(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')



@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  error = False

  try:
    venue = Venue.query.get(venue_id)
    venue_name = venue.name
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info)
  finally:
    db.session.close()
  
  if error:
    flash('An error occurred. Venue ' + venue_name + ' could not be deleted.')

  else:
    flash('Venue ' + venue_name + ' was successfully deleted!') 

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  artists = Artist.query.all()
  data = []

  for artist in artists:
    data.append({'id': artist.id, 'name': artist.name})

  return render_template('pages/artists.html', artists=data)



@app.route('/artists/search', methods=['POST'])
def search_artists():
  
  artists = Artist.query.filter(Artist.name.ilike(f'%{request.form.get("search_term", "")}%') )
  
  data = []
  
  current_time = datetime.datetime.utcnow()

  for artist in artists:
    data.append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': Shows.query.filter(Shows.artist == artist.id).filter(Shows.start_time > current_time).count()
    })
  
  response = {
    'count': artists.count(),
    'data': data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))



@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist = Artist.query.get(artist_id)

  current_time = datetime.datetime.utcnow()
  upcoming_shows = Shows.query.filter(Shows.artist == artist_id).filter(Shows.start_time > current_time)
  past_shows = Shows.query.filter(Shows.artist == artist_id).filter(Shows.start_time < current_time)

  upcoming_shows_list = []
  past_shows_list = []

  for upcoming_show in upcoming_shows:
    venue = Venue.query.get(upcoming_show.venue)
    upcoming_shows_list.append({
      'venue_id': venue.id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'start_time': upcoming_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for past_show in past_shows:
    venue = Venue.query.get(past_show.venue)
    past_shows_list.append({
      'venue_id': venue.id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'start_time': past_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  data = {
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genres.split(', '),
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'website': artist.website_link,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    'image_link': artist.image_link,
    'past_shows': past_shows_list,
    'upcoming_shows': upcoming_shows_list,
    'past_shows_count': past_shows.count(),
    'upcoming_shows_count': upcoming_shows.count(),
  }

  return render_template('pages/show_artist.html', artist=data)



#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  form = ArtistForm()

  artist = Artist.query.get(artist_id)

  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id> 
  return render_template('forms/edit_artist.html', form=form, artist=data)



@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  error = False
  
  try:
    artist = Artist.query.get(artist_id)

    seeking_venue = True if request.form.get('seeking_venue', False) == 'y' else False

    if(artist.name != request.form.get('name')): artist.name = request.form.get('name')
    if(artist.city != request.form.get('city')): artist.city = request.form.get('city')
    if(artist.state != request.form.get('state')): artist.state = request.form.get('state')
    if(artist.phone != request.form.get('phone')): artist.phone = request.form.get('phone')
    if(artist.image_link != request.form.get('image_linke')): artist.image_link = request.form.get('image_link')
    if(artist.facebook_link != request.form.get('facebook_link')): artist.facebook_link = request.form.get('facebook_link')
    if(artist.genres != request.form.get('genres')): artist.genres = request.form.get('genres')
    if(artist.website_link != request.form.get('website_link')): artist.website_link = request.form.get('website_link')
    if(artist.seeking_description != request.form.get('seeking_description')): artist.seeking_description = request.form.get('seeking_description') 
    if(artist.seeking_venue != seeking_venue): artist.seeking_venue = seeking_venue

    db.session.commit()
  
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info)
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Venue ' + request.form.get('name') + ' could not be edited.')
  else:
    flash('Venue ' + request.form.get('name') + ' was successfully edited!')

  return redirect(url_for('show_artist', artist_id=artist_id))



@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  data = {
    'id': venue.id,
    'name': venue.name,
    'genres': venue.genres.split(', '),
    'address': venue.address,
    'city': venue.city,
    'state': venue.state,
    'phone': venue.phone,
    'website': venue.website_link,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id> 
  return render_template('forms/edit_venue.html', form=form, venue=data)



@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  error = False
  
  try:
    venue = Venue.query.get(venue_id)

    seeking_talent = True if request.form.get('seeking_talent', False) == 'y' else False

    if(venue.name != request.form.get('name')): venue.name = request.form.get('name')
    if(venue.city != request.form.get('city')): venue.city = request.form.get('city')
    if(venue.state != request.form.get('state')): venue.state = request.form.get('state')
    if(venue.address != request.form.get('address')): venue.address = request.form.get('address')
    if(venue.phone != request.form.get('phone')): venue.phone = request.form.get('phone')
    if(venue.image_link != request.form.get('image_linke')): venue.image_link = request.form.get('image_link')
    if(venue.facebook_link != request.form.get('facebook_link')): venue.facebook_link = request.form.get('facebook_link')
    if(venue.genres != request.form.get('genres')): venue.genres = request.form.get('genres')
    if(venue.website_link != request.form.get('website_link')): venue.website_link = request.form.get('website_link')
    if(venue.seeking_description != request.form.get('seeking_description')): venue.seeking_description = request.form.get('seeking_description') 
    if(venue.seeking_talent != seeking_talent): venue.seeking_talent = seeking_talent

    db.session.commit()
  
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info)
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Venue ' + request.form.get('name') + ' could not be edited.')

  else:
    flash('Venue ' + request.form.get('name') + ' was successfully edited!') 
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))




#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)



@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  error = False

  try:
    artist = Artist(
      name = request.form.get('name'),
      city = request.form.get('city'),
      state = request.form.get('state'),
      phone = request.form.get('phone', 'Not provided'),
      genres = ', '.join(request.form.getlist('genres')),
      image_link = request.form.get('image_link', 'Default immage link'), #TODO
      facebook_link = request.form.get('facebook_link'),
      website_link = request.form.get('website_link', 'No website available.'),
      seeking_venue = True if request.form.get('seeking_venue', False) == 'y' else False,
      seeking_description = request.form.get('seeking_description', '')
    )
    db.session.add(artist)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')




#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  data = []

  shows = Shows.query.all()

  for show in shows:
    venue = Venue.query.get(show.venue)
    artist = Artist.query.get(show.artist)
    data.append({
      'venue_id': venue.id,
      'venue_name': venue.name,
      'artist_id': artist.id,
      'artist_image_link': artist.image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)



@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  
  if(Venue.query.get(request.form.get('venue_id')) is not None
  and
  Artist.query.get(request.form.get('artist_id')) is not None):
  
    error = False

    try:
      show = Shows(
        artist = request.form.get('artist_id'),
        venue = request.form.get('venue_id'),
        start_time =  request.form.get('start_time')
      )
      db.session.add(show)
      db.session.commit()
    except:
      db.session.rollback()
      error = True
      print(sys.exc_info())
    finally:
      db.session.close()

    if error:
      flash('An error occurred. Show could not be listed.')
    else:
      flash('Show was successfully listed!')
  
  else:
    flash('Artist or venue does not exist!')

  return render_template('pages/home.html')



@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404



@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
