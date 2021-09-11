import datetime
import json
import os

import requests
from flask import Flask
from flask import flash
from flask import redirect, url_for
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy

import config

# To run the page
# cd <dir>, flask run, go to the server

app = Flask(__name__, template_folder="templates")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TESTING'] = True
app.config.update(SECRET_KEY=os.urandom(24))
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return '<Name %r>' % self.name


db.create_all()


@app.route("/")
def index():
    weather_dict_storage = []
    all_cities = City.query.all()
    for city in all_cities:
        weather_dict = json.loads(get_city_weather(city.name).text)
        time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=weather_dict['timezone'])).strftime("%H")
        day_state = "day"
        if 17 <= int(time) <= 23:
            day_state = "evening-morning"
        elif 0 <= int(time) <= 5:
            day_state = "night"

        updated_dict = {"id": city.id, "city_name": weather_dict["name"], "temp": weather_dict["main"]["temp"],
                        "feel": weather_dict["weather"][0]["main"], "day_state": day_state}
        weather_dict_storage.append(updated_dict)
    return render_template("index.html", weather=weather_dict_storage)


@app.route("/add", methods=["POST"])
def add_city():
    if City.query.filter_by(name=request.form["city_name"].lower()).first() is None:  # If the city is not in our DB
        city = City(name=request.form["city_name"].lower())
        if json.loads(get_city_weather(city.name).text)["cod"] == "404":
            flash("The city doesn't exist!")
        else:
            db.session.add(city)
            db.session.commit()
            flash("Added {}".format(city.name.upper()))
    else:
        flash("The city has already been added to the list!")
    return redirect(url_for('index'))  # Redirects back to the main page (under "index" view)


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = City.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    flash("Deleted {}".format(city.name.upper()))
    return redirect(url_for('index'))


def get_city_weather(city_name):  # Returns weather info in JSON format
    return requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={config.api_key}&units=imperial")
