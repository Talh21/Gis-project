from flask import Blueprint, render_template, jsonify
from sqlalchemy import create_engine, text
from datetime import datetime, date, time

main = Blueprint('main', __name__)
DATABASE_URI = 'postgresql://postgres:210197@localhost/football_matches_db'
engine = create_engine(DATABASE_URI)

@main.route('/')
def home():
    return render_template('home.html')

@main.route('/matchmap')
def matchmap():
    return render_template('index.html')


@main.route('/api/stadium-coordinates')
def api_coordinates():
    query = text('SELECT * FROM stadium_coordinates')
    with engine.connect() as conn:
        result = conn.execute(query)
        # Convert result to a list of dictionaries
        data = [dict(zip(result.keys(), row)) for row in result]
    return jsonify(data)

@main.route('/api/matches')
def api_matches():
    query = text('''
        SELECT f.*, s.field_size, s.opened_date, s.image_url, s.capacity, s.city
        FROM football_fixtures f
        LEFT JOIN stadium_info s ON (f.stadium = s.stadium OR f.city = s.city)
    ''')
    with engine.connect() as conn:
        result = conn.execute(query)
        data = []
        for row in result:
            row_dict = {key: (value.isoformat() if isinstance(value, (datetime, date)) else value.strftime('%H:%M:%S') if isinstance(value, time) else value)
                        for key, value in zip(result.keys(), row)}
            data.append(row_dict)
    return jsonify(data)


