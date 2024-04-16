# Import the dependencies.

from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session 
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import scoped_session, sessionmaker

import datetime as dt 
import pandas as pd

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite", 
                       echo=True, connect_args={"check_same_thread": False})

# reflect an existing database into a new model
base = automap_base()
# reflect the tables
base.prepare(autoload_with=engine)

# Save references to each table
station = base.classes.station
measurement = base.classes.measurement

# Create our session (link) from Python to the DB
dp_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, 
                                      bind=engine))

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;"
    )
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = dp_session()
    try:
        # Calculate the date one year ago from the last data point in the database
        latest_date = session.query(func.max(measurement.date)).scalar()
        latest_date = dt.datetime.strptime(latest_date, "%Y-%m-%d")
        one_year_ago = latest_date - dt.timedelta(days=365)

        # Query precipitation data
        results = session.query(measurement.date, measurement.prcp).\
            filter(measurement.date >= one_year_ago).all()

        # Convert list of tuples into a dictionary
        precipitation = {date: prcp for date, prcp in results}
        return jsonify(precipitation)
    finally:
        session.close()  # Properly remove/dispose the session

@app.route("/api/v1.0/stations")
def stations():
    session = dp_session()
    results = session.query(station.station).all()
    session.close()

    # Convert list of tuples into normal list
    stations = [station[0] for station in results]
    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def tobs():
    session = dp_session()
    # Find the most active station
    most_active_station = session.query(measurement.station).\
        group_by(measurement.station).\
        order_by(func.count(measurement.station).desc()).first().station

    # Calculate the date one year ago from the last data point in the database
    latest_date = session.query(func.max(measurement.date)).scalar()
    latest_date = dt.datetime.strptime(latest_date, "%Y-%m-%d")
    one_year_ago = latest_date - dt.timedelta(days=365)

    # Query the last year of temperature observation data for this station
    results = session.query(measurement.tobs).\
        filter(measurement.date >= one_year_ago).\
        filter(measurement.station == most_active_station).all()
    session.close()

    # Convert list of tuples into normal list
    temperatures = [temp[0] for temp in results]
    return jsonify(temperatures)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def start(start, end=None):
    session = dp_session()
    # Construct a basic select statement
    sel = [func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)]

    if end:
        results = session.query(*sel).\
            filter(measurement.date >= start).\
            filter(measurement.date <= end).all()
    else:
        results = session.query(*sel).\
            filter(measurement.date >= start).all()
    session.close()

    temps = results[0]
    temp_dict = {'TMIN': temps[0], 'TAVG': temps[1], 'TMAX': temps[2]}
    return jsonify(temp_dict)

if __name__ == '__main__':
    app.run(debug=True)

