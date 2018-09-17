import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask_caching import Cache
from csv import DictReader
from toolz import compose, pluck, groupby, valmap, first, unique, get, countby
import datetime as dt
import numpy as np
import pandas as pd
#from dotenv import find_dotenv,load_dotenv
import os

#import pdb; pdb.set_trace() 

################################################################################
# HELPERS
################################################################################

listpluck = compose(list, pluck)
listfilter = compose(list, filter)
listmap = compose(list, map)
listunique = compose(list, unique)

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"


df = pd.read_csv('/Users/WilliamStevens/Documents/deplorable_snowflake/ds/app_7/ufo_sightings.csv')
date_time = df['date_time']
print(date_time.isna().any())

# Datetime helpers.
def sighting_year(sighting):
    return dt.datetime.strptime(sighting['date_time'], TIMESTAMP_FORMAT).year

def sighting_state(sighting):
    return sighting['state']

def count_dow(sighting):
    states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "OH", "OK", "OR", "PA", "RI", "SC", 
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
    for sighting['state'] in states:
        return sighting['state']


################################################################################
# PLOTS
################################################################################


def ufo_map(sightings):
    #print(sightings)
    classifications = groupby('shape', sightings)
    return {
        "data": [
                {
                    "type": "scattermapbox",
                    "lat": listpluck("city_latitude", class_sightings),
                    "lon": listpluck("city_longitude", class_sightings),
                    "text": listpluck("summary", class_sightings),
                    "mode": "markers",
                    "name": shape,
                    "marker": {
                        "size": 3,
                        "opacity": 1.0
                    }
                }
                for shape, class_sightings in classifications.items()
            ],
        "layout": {
            "autosize": True,
            "hovermode": "closest",
            "mapbox": {
                "accesstoken": 'pk.eyJ1IjoiYnVsbHliZWFyIiwiYSI6ImNqbDB1M2dnaDE4cWQza2xlazE3Z2t4ZnUifQ.m3UgrvGKwKUsPFDUa1MT5w',
                "bearing": 0,
                "center": {
                    "lat": 40,
                    "lon": -98.5
                },
                "pitch": 0,
                "zoom": 2,
                "style": "outdoors"
            }
        }
    }


def ufo_by_year(sightings):
    # Create a dict mapping the 
    # classification -> [(year, count), (year, count) ... ]
    sightings_by_year = {
        shape: 
            sorted(
                list(
                    # Group by year -> count.
                    countby(sighting_year, class_sightings).items()
                ),
                # Sort by year.
                key=first
            )
        for shape, class_sightings 
        in groupby('shape', sightings).items()
    }

    # Build the plot with a dictionary.
    return {
        "data": [
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": shape,
                "x": listpluck(0, class_sightings_by_year),
                "y": listpluck(1, class_sightings_by_year)
            }
            for shape, class_sightings_by_year 
            in sightings_by_year.items()
        ],
        "layout": {
            "title": "Sightings by Year",
            "showlegend": True
        }
    }




def ufo_class_shape(sightings):
    sightings_by_class = countby("shape", sightings)

    return {
        "data": [
            {
                "type": "pie",
                "labels": list(sightings_by_class.keys()),
                "values": list(sightings_by_class.values()),
                "hole": 0.4
            }
        ],
        "layout": {
            "title": "Sightings by Shape",
            "showlegend": True
        }
    }


def ufo_class_state(sightings):
    states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
    "NM", "NY", "NC", "OH", "OK", "OR", "PA", "RI", "SC", 
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

    # Produces a dict (year, dow) => count.
    sightings_state = countby("states", 
        [
            {
                #"state": count_dow(sighting)
                "states": sighting_state(sighting)
            } 
            for sighting in sightings
        ]
    )

    return {
        "data": [
            {
                "type": "bar",
                #"x": states,
                "text": states,
                "y": [get(d, sightings_state, 0) for d in states]
            }
        ],
        "layout": {
            "title": "Sightings by State",
        }
    }



'''
def ufo_class_state(sightings):
    df_new = pd.read_csv('/Users/WilliamStevens/Documents/deplorable_snowflake/ds/app_7/ufo_cities.csv')
    sightings_by_class = countby(df_new(df_new["city"]), sightings)

    return {
        "data": [
            {
                "type": "pie",
                "labels": list(sightings_by_class.keys()),
                "values": list(sightings_by_class.values()),
                "hole": 0.4
            }
        ],
        "layout": {
            "title": "Sightings by City"
        }
    }

'''

################################################################################
# APP INITIALIZATION
################################################################################


fin = open('ufo_sightings.csv','r')


reader = DictReader(fin)
BFRO_LOCATION_DATA = \
[
    line for line in reader 
    #if (sighting_year(line) <= 2000) and (sighting_year(line) >= 2018)
]
fin.close()


app = dash.Dash()
server = app.server
server.secret_key = os.environ.get("SECRET_KEY", "secret")

app.title = "UFO Sightings"
cache = Cache(app.server, config={"CACHE_TYPE": "simple"})


@cache.memoize(10)
def filter_sightings(filter_text):
    return listfilter(
            lambda x: filter_text.lower() in x['summary'].lower(),
            BFRO_LOCATION_DATA
            
        )


################################################################################
# LAYOUT
################################################################################

app.css.append_css({
    "external_url": "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"
})

app.css.append_css({
    "external_url": 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

app.scripts.append_script({
    "external_url": "https://code.jquery.com/jquery-3.2.1.min.js"
})

app.scripts.append_script({
    "external_url": "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"
})


app.layout = html.Div([
    # Row: Title
    html.Div([
        # Column: Title
        html.Div([
            html.H1("UFO Sightings", className="text-center")
        ], className="col-md-12")
    ], className="row"),
    # Row: Filter + References
    html.Div([
        # Column: Filter
        html.Div([
            html.P([
                html.B("Filter the titles:  "),
                dcc.Input(
                    placeholder="Try 'saw'",
                    id="ufo-text-filter",
                    value="sky")
            ]),
        ], className="col-md-6"),
        # Column: References.
        html.Div([
            html.P([
                "Data pulled from ",
                html.A("nuforc.org", href="http://www.nuforc.org/"),
                ". Grab it at ",
                html.A("data.world", href="https://data.world/timothyrenner/ufo-sightings"),
                "."
            ], style={"text-align": "right"})
        ], className="col-md-6")
    ], className="row"),
    # Row: Map + Bar Chart
    html.Div([
        # Column: Map
        html.Div([
            dcc.Graph(id="ufo-map")
        ], className="col-md-8"),
        # Column: Bar Chart
        html.Div([
            dcc.Graph(id="ufo-dow")
        ], className="col-md-4")
    ], className="row"),
    # Row: Line Chart + Donut Chart
    html.Div([
        # Column: Line Chart
        html.Div([
            dcc.Graph(id="ufo-by-year")
        ], className="col-md-8"),
        # Column: Donut Chart
        html.Div([
            dcc.Graph(id="ufo-class")
        ], className="col-md-4")
    ], className="row"),
    # Row: Footer
    html.Div([
        html.Hr(),
        html.P([
            "A Deplorable Snowflake Production",
            html.A("Deplorable Snowflake", href="https://deplorablesnowflake.org"),

        ])      
    ], className="row",
        style={
            "textAlign": "center",
            "color": "Gray"
        })
], className="container-fluid")


################################################################################
# INTERACTION CALLBACKS
################################################################################


@app.callback(
    Output('ufo-map', 'figure'),
    [
        Input('ufo-text-filter', 'value')
    ]
)
def filter_ufo_map(filter_text):
    return ufo_map(filter_sightings(filter_text))




@app.callback(
    Output('ufo-by-year', 'figure'),
    [
        Input('ufo-text-filter', 'value')
    ]
)
def filter_ufo_by_year(filter_text):
    return ufo_by_year(filter_sightings(filter_text))



@app.callback(
    Output('ufo-dow', 'figure'),
    [
        Input('ufo-text-filter', 'value')
    ]
)
def filter_ufo_class(filter_text):
    return ufo_class_shape(filter_sightings(filter_text))



@app.callback(
    Output('ufo-class', 'figure'),
    [
        Input('ufo-text-filter', 'value')
    ]
)
def filter_ufo_class(filter_text):
    return ufo_class_state(filter_sightings(filter_text))




if __name__ == "__main__":
    app.run_server(debug=True)