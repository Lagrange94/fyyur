#----------------------------------------------------------------------------#
# - Main file.
#----------------------------------------------------------------------------#


#----------------------------------------------------------------------------#
# - Imports.
#----------------------------------------------------------------------------#

import dateutil.parser
import logging
import babel
import json
import sys

from flask_sqlalchemy import SQLAlchemy
from xmlrpc.client import FastParser
from flask_migrate import Migrate
from flask_moment import Moment
from datetime import datetime
from flask_wtf import Form
from forms import *

from flask import (
  Flask, 
  render_template, 
  request, 
  Response, 
  flash, 
  redirect, 
  url_for
  )

from logging import (
  Formatter, 
  FileHandler
  )

from models import (
  Artist, 
  Venue, 
  Shows, 
  db
  )

#----------------------------------------------------------------------------#
# - App Config.
#----------------------------------------------------------------------------#

# - Set the name equivalent to the name of the file (app.py)
app = Flask(__name__)

# - ??
moment = Moment(app)

# - Load configuration data from config file
app.config.from_object('config')

# - Initialize database object
db.init_app(app)

# - Initialilze migration interface
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# - Filters.
#----------------------------------------------------------------------------#

# - Function to format the datetime
def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# - Controllers.
#----------------------------------------------------------------------------#

# - Decorates index to be the callback of client request of '/'
@app.route('/')
def index():
  return render_template('pages/home.html')


#----------------------------------------------------------------------------#
# - Venue Controllers.
#----------------------------------------------------------------------------#

# - Decorates venues to be the callback of client request of '/venues'
@app.route('/venues')
def venues():

  # - Query the venue table
  venues = Venue.query.all()

  # - Create a list object
  data = []

  # - Get the current time from datetime
  current_time = datetime.utcnow()

  # - Iterate over venues and sort by city and state attribute
  for venue in venues:

    # - If the data list object is empty add the first entry
    if not data:
      data.append({
        'city': venue.city,
        'state': venue.state,
        'venues': [{
          'id': venue.id,
          'name': venue.name,
          'num_upcoming_Shows': Shows.query.filter(Shows.venue_id 
                                == venue.id).filter(Shows.start_time 
                                < current_time).count()
        }]
      })

    # - Else check if the location attributes already exist in the list
    else:
      inserted = False
      for place in data:
        if(place['city'] == venue.city and place['state'] == venue.state):
          
          # - If location already exists, add venue to location
          place['venues'].append({
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_Shows': Shows.query.filter(Shows.venue_id 
                                  == venue.id).filter(Shows.start_time 
                                  < current_time).count()
          })
          inserted = True
      if not inserted:

        # - If location does not exist, create new location and add venue
        data.append({
          'city': venue.city,
          'state': venue.state,
          'venues': [{
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_Shows': Shows.query.filter(Shows.venue_id 
                                  == venue.id).filter(Shows.start_time 
                                  < current_time).count()
          }]
        })

  # - Render respective template with given data
  return render_template('pages/venues.html', areas=data)


# - Decorates search_venues to be the callback of client request of
# - '/venues/search'
@app.route('/venues/search', methods=['POST'])
def search_venues():

  # - Query venues and filter for values like the search term
  venues = Venue.query.filter(Venue.name.ilike(
                              f'%{request.form.get("search_term", "")}%') 
                              )
  
  # - Create a list object
  data = []

  # - Get the current time from datetime
  current_time = datetime.utcnow()

  # - Add queried venues to list object
  for venue in venues:
    data.append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_Shows': Shows.query.filter(Shows.venue == venue.id)
                                       .filter(Shows.start_time 
                                                < current_time).count()
    })
  
  # - Create a response 
  response = {
    'count': venues.count(),
    'data': data
  }

  # - Render respective template with given data
  return render_template('pages/search_venues.html', results=response, 
                         search_term=request.form.get('search_term', ''))


# - Decorates show_venue to be the callback of client request of
# - '/venues/<int:venue_id>'
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  # - Query the venue table
  venue = Venue.query.get(venue_id)
   
  # - Get the current time from datetime
  current_time = datetime.utcnow()

  # - Filter shows for upcoming and past shows for given venue
  upcoming_shows = (Shows.query.filter(Shows.venue_id == venue_id)
                               .filter(Shows.start_time > current_time))
  past_shows = (Shows.query.filter(Shows.venue_id == venue_id)
                           .filter(Shows.start_time < current_time))

  # - Create list objects for upcoming and past shows
  upcoming_shows = []
  past_shows = []

  for show in venue.shows:
    temp_show = {
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
    }
    if show.start_time <= datetime.now():
      past_shows.append(temp_show)
    else:
      upcoming_shows.append(temp_show)

  # - Create the data object required to fill the respective template
  data = vars(venue)
  data['genres'] = ''.join(data['genres']).replace('{', '').replace('}','').split(',')
  data['past_shows'] = past_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows'] = upcoming_shows
  data['upcoming_shows_count'] = len(upcoming_shows)

  # - Render respective template with given data
  return render_template('pages/show_venue.html', venue=data)


# - Decorates create_venue_form to be the callback of client request of
# - '/venues/create' - GET
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

# - Decorates create_venue_submission to be the callback of client request of
# - '/venues/create' - POST 
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  # - Pass data trough VenueForm for validation
  form = VenueForm(request.form)

  # - Create error tracking object
  error = False

  # - Try to create a venue record and add it to the database, rollback in 
  # - case of failure
  try:
    venue = Venue()
    form.populate_obj(venue)  # Automates Venue('name': form.name.data, ...)
    db.session.add(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  
  # - Inform client wether venue was created or not
  if error:
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
  else:
    flash('Venue ' + form.name.data + ' was successfully listed!')

  # - Render respective template
  return render_template('pages/home.html')


# - Decorates delete_venue to be the callback of client request of
# - '/venues/<venue_id>' - DELETE
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  # - Create error tracking object
  error = False

  # - Try to delete the respective venue record and add it to the database, 
  # - rollback in case of failure
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
  
  # - Inform client wether venue was deleted or not
  if error:
    flash('An error occurred. Venue ' + venue_name + ' could not be deleted.')
  else:
    flash('Venue ' + venue_name + ' was successfully deleted!') 

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, 
  # have it so that clicking that button delete it from the db then redirect 
  # the user to the homepage
  return None


# - Decorates edit_venue to be the callback of client request of
# - '/venue/<int:venue_id>/edit' - GET
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  # - Query the Venue table
  venue = Venue.query.get(venue_id)

  # - Populate the respective form with data
  form = VenueForm(obj = venue)

  # - Render the respective template with given data
  return render_template('forms/edit_venue.html', form=form, venue=venue)


# - Decorates edit_venue to be the callback of client request of
# - '/venue/<int:venue_id>/edit' - POST
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  # - Create error tracking object
  error = False
  
  # - Try to update an venue record in the database, rollback in caser of
  # - failure. Check for differences beforehand and update only different 
  # - attributes
  try:
    venue = Venue.query.get(venue_id)

    seeking_talent = True if request.form.get('seeking_talent', False) == 'y' else False

    if(venue.name != request.form.get('name')): 
      venue.name = request.form.get('name')
    if(venue.city != request.form.get('city')): 
      venue.city = request.form.get('city')
    if(venue.state != request.form.get('state')): 
      venue.state = request.form.get('state')
    if(venue.address != request.form.get('address')): 
      venue.address = request.form.get('address')
    if(venue.phone != request.form.get('phone')): 
      venue.phone = request.form.get('phone')
    if(venue.image_link != request.form.get('image_linke')): 
      venue.image_link = request.form.get('image_link')
    if(venue.facebook_link != request.form.get('facebook_link')): 
      venue.facebook_link = request.form.get('facebook_link')
    if(venue.genres != request.form.get('genres')): 
      venue.genres = request.form.get('genres')
    if(venue.website_link != request.form.get('website_link')): 
      venue.website_link = request.form.get('website_link')
    if(venue.seeking_description != request.form.get('seeking_description')): 
      venue.seeking_description = request.form.get('seeking_description') 
    if(venue.seeking_talent != seeking_talent): 
      venue.seeking_talent = seeking_talent

    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info)
  finally:
    db.session.close()

# - Inform client wether edit was successfull or not
  if error:
    flash('An error occurred. Venue ' + request.form.get('name') 
          + ' could not be edited.')
  else:
    flash('Venue ' + request.form.get('name') + ' was successfully edited!') 
  
  # - Render respective template with given data
  return redirect(url_for('Shows_venue', venue_id=venue_id))


#----------------------------------------------------------------------------#
# - Artist Controllers.
#----------------------------------------------------------------------------#


# - Decorates artists to be the callback of client request of '/artists'
@app.route('/artists')
def artists():

  # - Query the Artist table
  artists = Artist.query.all()
  
  # - Create a list object
  data = []

  # - Add artist information to the data list
  for artist in artists:
    data.append({'id': artist.id, 'name': artist.name})

  # - Render respective template with relevant data
  return render_template('pages/artists.html', artists=data)


# - Decorates search_artists to be the callback of client request of
# - '/artists/search'
@app.route('/artists/search', methods=['POST'])
def search_artists():
  
  # - Query artists and filter for values like the search term
  artists = Artist.query.filter(Artist.name.ilike(
                                f'%{request.form.get("search_term", "")}%')
                                )
  
  # - Create a list object
  data = []
  
  # - Get the current time from datetime
  current_time = datetime.utcnow()

  # - Add queried artists to list object
  for artist in artists:
    data.append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_Shows': Shows.query.filter(Shows.artist == artist.id)
                                       .filter(Shows.start_time 
                                                > current_time).count()
    })
  
  # - Create a response
  response = {
    'count': artists.count(),
    'data': data
  }

  # - Render respective template with giben data
  return render_template('pages/search_artists.html', results=response, 
                         search_term=request.form.get('search_term', ''))


# - Decorates Shows_artist to be the callback of client request of
# - '/artists/<int:artist_id>'
@app.route('/artists/<int:artist_id>')
def Shows_artist(artist_id):

  # - Query the artist table
  artist = Artist.query.get(artist_id)

  # - Get the current time from datetime
  current_time = datetime.utcnow()

  # - Filter Shows for upcoming and past Shows for given artist
  upcoming_shows = (Shows.query.filter(Shows.artist_id == artist_id)
                               .filter(Shows.start_time > current_time))
  past_shows = (Shows.query.filter(Shows.artist_id == artist_id)
                           .filter(Shows.start_time < current_time))

  # - Create list objects for upcoming and past Shows
  upcoming_shows_list = []
  past_shows_list = []

  # - Add required information to the list objects for upcoming and past Shows
  for upcoming_show in upcoming_shows:
    upcoming_shows_list.append({
      'venue_id': upcoming_show.venue.id,
      'venue_name': upcoming_show.venue.name,
      'venue_image_link': upcoming_show.venue.image_link,
      'start_time': upcoming_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  for past_show in past_shows:
    past_shows_list.append({
      'venue_id': past_show.venue.id,
      'venue_name': past_show.venue.name,
      'venue_image_link': past_show.venue.image_link,
      'start_time': past_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
 
  # - Create the data object required to fill the respective template
  data = vars(artist)
  data['genres'] = ''.join(data['genres']).replace('{', '').replace('}','').split(',')
  data['past_shows'] = past_shows_list
  data['past_shows_count'] = past_shows.count()
  data['upcoming_shows'] = upcoming_shows_list
  data['upcoming_shows_count'] = upcoming_shows.count()

# - Render respective template with given data
  return render_template('pages/show_artist.html', artist=data)


# - Decorates edit_artist to be the callback of client request of
# - '/artists/<int:artist_id>/edit' - GET
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  # - Query the Artist table
  artist = Artist.query.get(artist_id)

  # - Populate the respective form with data
  form = ArtistForm(obj = artist)

  # - Render respective template with given data
  return render_template('forms/edit_artist.html', form=form, artist=artist)


# - Decorates edit_artist to be the callback of client request of
# - '/artists/<int:artist_id>/edit' - POST
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  # - Create error tracking object
  error = False
  
  # - Try to update an artist record in the database, rollback in caser of
  # - failure. Check for differences beforehand and update only different 
  # - attributes
  try:
    artist = Artist.query.get(artist_id)

    seeking_venue = (True if request.form.get('seeking_venue', False) 
                     == 'y' else False
                     )

    # - Check which values changed and adapt respective values
    if(artist.name != request.form.get('name')): 
      artist.name = request.form.get('name')
    if(artist.city != request.form.get('city')): 
      artist.city = request.form.get('city')
    if(artist.state != request.form.get('state')): 
      artist.state = request.form.get('state')
    if(artist.phone != request.form.get('phone')): 
      artist.phone = request.form.get('phone')
    if(artist.image_link != request.form.get('image_linke')): 
      artist.image_link = request.form.get('image_link')
    if(artist.facebook_link != request.form.get('facebook_link')): 
      artist.facebook_link = request.form.get('facebook_link')
    if(artist.genres != request.form.get('genres')): 
      artist.genres = request.form.get('genres')
    if(artist.website_link != request.form.get('website_link')): 
      artist.website_link = request.form.get('website_link')
    if(artist.seeking_description != request.form.get('seeking_description')): 
      artist.seeking_description = request.form.get('seeking_description') 
    if(artist.seeking_venue != seeking_venue): 
      artist.seeking_venue = seeking_venue

    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info)
  finally:
    db.session.close()

  # - Inform client wether edit was successfull or not
  if error:
    flash('An error occurred. Venue ' + request.form.get('name') 
          + ' could not be edited.')
  else:
    flash('Venue ' + request.form.get('name') + ' was successfully edited!')

  # - Render respective template
  return redirect(url_for('Shows_artist', artist_id=artist_id))


# - Decorates create_artist to be the callback of client request of
# - '/artists/create' - GET
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


# - Decorates create_artist to be the callback of client request of
# - '/artists/create' - POST
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  # - Pass data trough VenueForm for validation
  form = ArtistForm(request.form)

  # - Create error tracking object
  error = False

  # - Try to create an artist record and add it to the database, rollback in 
  # - case of failure
  try:
    artist = Artist()
    form.populate_obj(artist) # Automates Venue('name': form.name.data, ...)
    print(artist.genres)
    print(form.genres.data)
    artist.genres = form.genres.data
    print(artist.genres)
    db.session.add(artist)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

  # - Inform client wether artist was created or not
  if error:
    flash('An error occurred. Artist ' + request.form['name'] 
          + ' could not be listed.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  # - Render respective template
  return render_template('pages/home.html')




#----------------------------------------------------------------------------#
# - Shows Controllers.
#----------------------------------------------------------------------------#


# - Decorates shows to be the callback of client request of
# - '/shows'
@app.route('/shows')
def shows():

  # - Create a list object
  data = []

  # - Query Shows table
  shows = Shows.query.all()

  # - Iterate over shows and add respective data to the shows table
  for show in shows:
    data.append({
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'artist_id': show.artist.id,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  # - Render respective template with given data
  return render_template('pages/shows.html', shows=data)


# - Decorates create_show to be the callback of client request of
# - '/shows/create' GET
@app.route('/shows/create', methods = ['GET'])
def create_Shows():

  # - Query venue and artist table
  venues = Venue.query.all()
  artists = Artist.query.all()

  # - Pass data to ShowForm
  form = ShowForm(venues = venues, artists = artists)

  # - Render respective template with given data
  return render_template('forms/new_show.html', form=form)


# - Decorates create_show_submission to be the callback of client request of
# - '/shows/create' POST
@app.route('/shows/create', methods=['POST'])
def create_Shows_submission():
  
  # - Query venue and artist table
  venues = Venue.query.all()
  artists = Artist.query.all()

  # - Pass data to ShowForm for validation
  form = ShowForm(request.form, venues = venues, artists = artists)

  # - Create error tracking object
  error = False 

  # - Try to create a show record and add it to the database, rollback in 
  # - case of failure
  try:
    show = Shows()
    form.populate_obj(show)

    db.session.add(show)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  
  # - Inform the client if a show was created or not
  if error:
    flash('An error occurred. Shows could not be listed.')
  else:
    flash('Shows was successfully listed!')

  # - Render respective template
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
