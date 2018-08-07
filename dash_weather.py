# -*- coding: utf-8 -*-

import datetime as dt
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_html_components as html
import plotly
import requests
import serial
import time

ser = serial.Serial('/dev/ttyACM0', 9600)

arduino_data = {'time': [], 'Temperature': [], 'Humidity': []}
city_data = {'time': [], 'Temperature': [], 'Humidity': [], 'city': []}

# weather api
api_key = ''  # ENTER YOUR KEY
city_id = ''  # ENTER YOUR CITY ID
base_url = 'https://api.openweathermap.org/data/2.5/weather?id='
url = f'{base_url}{city_id}&units=metric&APPID={api_key}'
header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Host': 'samples.openweathermap.org',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'}

run_times = [0]


def throttling():
    cond1 = time.time() - run_times[-1] > 600
    cond2 = len(run_times) == 1
    return cond1 or cond2


def get_now():
    """Time to make to plot on x axis."""
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_temp():
    """Read the arduino serial port and parse it to a dictionary."""
    return list(eval(ser.readline().decode()).values())


def get_city_temp():
    """Use the openweather api to get new data every 10 mins."""
    m = requests.request('post', url, headers=header)
    openweather = eval(m.text)
    return [openweather['main']['temp'], openweather['main']['humidity'],
            openweather['name']]


app = dash.Dash()

app.css.append_css({
    'external_url':
    ('https: // maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/'
     'css/bootstrap.min.css')})

app.layout = html.Div([
    dcc.Markdown('''# Should I open the window app.'''.replace('  ', '')),
    dcc.Graph(id='my-graph'),
    dcc.Interval(id='interval-component',
                 interval=1*10000,  # in milliseconds
                 n_intervals=0)])


@app.callback(Output('my-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    temperature, humidity = get_temp()
    arduino_data['Temperature'].append(temperature)
    arduino_data['Humidity'].append(humidity)
    arduino_data['time'].append(get_now())

    if throttling():
        temp, hum, city = get_city_temp()
        city_data['Temperature'].append(temp)
        city_data['Humidity'].append(hum)
        city_data['time'].append(get_now())
        city_data['city'].append(city)
        run_times.append(time.time())

    # Create the graph with subplots
    fig = plotly.tools.make_subplots(rows=2, cols=1, vertical_spacing=0.2)
    fig['layout']['margin'] = {'l': 30, 'r': 10, 'b': 30, 't': 10}
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}

    fig.append_trace({
        'x': arduino_data['time'],
        'y': arduino_data['Temperature'],
        'name': 'Temperature',
        'mode': 'lines+markers',
        'type': 'scatter'}, 1, 1)
    fig.append_trace({
        'x': arduino_data['time'],
        'y': arduino_data['Humidity'],
        'text': arduino_data['time'],
        'name': 'Humidity',
        'mode': 'lines+markers',
        'type': 'scatter'}, 2, 1)
    fig.append_trace({
        'x': city_data['time'],
        'y': city_data['Temperature'],
        'name': city_data['city'][0],
        'mode': 'lines+markers',
        'type': 'scatter'}, 1, 1)
    fig.append_trace({
        'x': city_data['time'],
        'y': city_data['Humidity'],
        'name': city_data['city'][0],
        'mode': 'lines+markers',
        'type': 'scatter'}, 2, 1)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
