#----------------------------------------------------------------------------#
# - File to hold the models employed in the database.
#----------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
# - Imports.
#----------------------------------------------------------------------------#

from flask_sqlalchemy import SQLAlchemy


#----------------------------------------------------------------------------#
# - Preparations.
#----------------------------------------------------------------------------#

# - Create db object
db = SQLAlchemy()


#----------------------------------------------------------------------------#
# - Classes.
#----------------------------------------------------------------------------#


# - Shows class
class Shows(db.Model):
    __tablename__ = 'Shows'

    id = db.Column(db.Integer, primary_key = True)
    start_time = db.Column(db.DateTime, nullable = False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable = False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable = False)


# - Venue class
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)), nullable = False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable = False, default = False)
    seeking_description = db.Column(db.String(1000))
    shows = db.relationship('Shows', backref = 'venue', lazy = 'joined', 
                            cascade = 'all, delete')

# - Artist class
class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)), nullable = False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, nullable = False, default = False)
    seeking_description = db.Column(db.String(1000))
    shows = db.relationship('Shows', backref = 'artist', lazy = 'joined', 
                            cascade = 'all, delete')
