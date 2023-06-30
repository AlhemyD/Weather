from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
from pathlib import Path
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import base64
import io
import datetime
import time
import json
import requests
import csv
import sys

px.set_mapbox_access_token('pk.eyJ1IjoieXVwZXN0IiwiYSI6ImNqdWpwOTJ6ZTA5MmQzeW1xeGdrb3VhcjkifQ.UEEIc5yM8s1lfMaREu-p6Q')
operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


def get_weather_by_coords(lat, lon, date):
    # Если температура меньше 30 градусов и
    # относительная влажность воздуха меньше 30%,
    # а также нет никаких осадков, то наблюдается сухая гроза

    # ограничение на число запросов - 10_000 в сутки
    dt = date.replace('/', '-')
    wantes = 'temperature_2m,relativehumidity_2m,dewpoint_2m,precipitation,rain,snowfall,weathercode,cloudcover,windspeed_10m,windspeed_100m'
    response = requests.get('https://archive-api.open-meteo.com/v1/archive',
                            params={"latitude": lat,
                                    "longitude": lon,
                                    "start_date": dt,
                                    "end_date": dt,
                                    "hourly": wantes}).json()
    '''        new_cols=('temperature_2m °C', 'relativehumidity_2m %',
                  'dewpoint_2m °C', 'precipitation mm',
                  'rain mm', 'snowfall cm',
                  'cloudcover %','windspeed_10m km/h',
                  'windspeed_100m km/h')'''
    r = response['hourly']
    dry_thunder = (r['temperature_2m'][11] > 30) and (r['relativehumidity_2m'][11] < 30) and not (
                r['rain'][11] or r['precipitation'][11] or r['snowfall'][11])
    return {
        'temperature_2m °C': r['temperature_2m'][11],
        'relativehumidity_2m %': r['relativehumidity_2m'][11],
        'dewpoint_2m °C': r['dewpoint_2m'][11],
        'precipitation mm': r['precipitation'][11],
        'rain mm': r['rain'][11],
        'snowfall cm': r['snowfall'][11],
        'cloudcover %': r['cloudcover'][11],
        'windspeed_10m km/h': r['windspeed_10m'][11],
        'windspeed_100m km/h': r['windspeed_100m'][11],
        'dry_thunder': dry_thunder
    }


def table_type(df_column):
    if sys.version_info < (3, 0):
        return 'any'

    if isinstance(df_column.dtype, pd.DatetimeTZDtype):
        return 'datetime',
    elif (isinstance(df_column.dtype, pd.StringDtype) or
          isinstance(df_column.dtype, pd.BooleanDtype) or
          isinstance(df_column.dtype, pd.CategoricalDtype) or
          isinstance(df_column.dtype, pd.PeriodDtype)):
        return 'text'
    elif (isinstance(df_column.dtype, pd.SparseDtype) or
          isinstance(df_column.dtype, pd.IntervalDtype) or
          isinstance(df_column.dtype, pd.Int8Dtype) or
          isinstance(df_column.dtype, pd.Int16Dtype) or
          isinstance(df_column.dtype, pd.Int32Dtype) or
          isinstance(df_column.dtype, pd.Int64Dtype)):
        return 'numeric'
    else:
        return 'any'


def parse_contents(contents, filename):  # функция, которая обрабатывает полученный csv файл
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            global df_len
            global Dtable

            Dtable = df
            df_len = len(df)
    except Exception as e:
        print(e, '!1!')

    return df


app = Dash(__name__)

# layout - внешний вид веб-приложения
app.layout = html.Div([
    html.H1("Погодосборник!", style={'margin': '2% 25% 0% 25%',
                                     'color': 'black', 'textAlign': 'center',
                                     'background-color': 'white',
                                     'font-size': '250%', 'width': '50%',
                                     'borderWidth': '1px',
                                     'borderStyle': 'solid',
                                     'borderRadius': '5px',
                                     }),
    html.Div([
        html.Div([
            dcc.Upload(  # кнопка для загрузки файла
                id='upload-data',
                children=html.Div([
                    'Загрузите csv файл'
                ]),
                max_size=10*1024*1024,
                multiple=False,  # можно ли загружать сразу несколько файлов с помощью кнопки
                style={'color': 'white',
                       'font-size': '250%',
                       'cursor': 'pointer',
                       'background-color': 'grey', 'height': '100%', 'width': '98%',
                       'text-align': 'center',
                       'borderColor': 'black',
                       'borderWidth': '2px',
                       'borderStyle': 'solid',
                       'borderRadius': '20px',
                       }
            ),
            html.Img(id='img-manual',src=app.get_asset_url('ins.png'), style={'width':'96%','margin-top':'1.1%'}),
            html.H3(id='manual', children='',
                    style={'color': 'black', 'background-color': 'white',
                           'font-size': '200%', 'height': '100px',
                           'margin-top': '1.1%', 'whiteSpace': 'normal'}),
            html.Button("Скачайте CSV файл", id="btn-csv", style={
                'color': 'white',
                'background-color': 'grey',
                'font-size': '218.5%',
                'width': '98%',
                'text-align': 'center',
                'cursor': 'pointer',
                'border': 'none',
                'margin-top': '-5%',
                'borderColor': 'black',
                'borderWidth': '2px',
                'borderStyle': 'solid',
                'borderRadius': '20px',
            }),
            dcc.Download(id="download-dataframe-csv")],
            style={
                'display': 'flex',
                'flex-direction': 'column',
                'width': '1000px',
                'height': '750px',
                'margin': '0.5% 0% 0 0%'
            }),
        html.Div([
            html.Div(id='output-data-upload'),
            dcc.Store(id='intermediate-value'),
            html.Div(id='output-map')
        ], style={'width': '50%', 'margin-top': '0.25%'})
    ], style={'display': 'flex', 'flex-direction': 'row',
              'width': '100%', 'margin': '0.5% 48% 0.5% 0%',
              })
])


@app.callback(Output('output-data-upload', 'children'),
              Output('img-manual', 'src'),
              Input('intermediate-value', 'data'), prevent_initial_call=True)
def update_output(data):  # обновляет выходные данные и выводит табличку на экран (обрабатывает JSON файл)
    dataset = json.loads(data)
    df = pd.read_json(dataset, orient='split')
    components = [
        html.Div([
            dcc.Input(id='filter-query-input', placeholder='Введите запрос фильтра', style={
                'color': 'black', 'background-color': 'write',
                'font-size': '100%', 'margin-right': 'auto',
                'width': '50%',
                'text-align': 'center',
                'borderWidth': '1px',
                'borderStyle': 'solid',
                'borderRadius': '5px',
            }),
            html.Button("Reset", id='reset-filters', style={
                'color': 'black',
                'background-color': 'write',
                'font-size': '100%',
                'width': '50%',
                'margin-left': 'auto',
                'text-align': 'center',
                'cursor': 'pointer',
                'border': 'none'
            })], style={
            'display': 'flex',
            'flex-direction': 'row',
            'width': '100%',
            'height': '50px',
            'margin': '0.5% 50% 0.5% 0%'
        }),
        html.Div([
            dash_table.DataTable(
                df.to_dict('records'),
                [{"name": i, "id": i, 'type': table_type(df[i])} for i in df.columns],
                page_size=10,
                filter_action='custom',
                filter_query='',
                style_data={
                    'whiteSpace': 'normal',
                    'background-color': 'white',
                    'color': 'black'},
                style_header={
                    'background-color': 'white',
                    'color': 'black',
                    'fontWeight': 'bold'},
                style_table={'overflowX': 'auto'},
                style_cell={
                    'minWidth': '100px',
                    'width': '150px',
                    'maxWidth': '200px',
                    'whiteSpace': 'normal'},
                id="table_to_filter"
            )
        ], style={'margin': '0.5% 0 0.5%'})
    ]
    children = html.Div(components)
    text = app.get_asset_url('ins2.png')
    return children, text


@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-csv", "n_clicks"),
    State('intermediate-value', 'data'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def download_dataframe(n_clicks, data, filename):
    dataset = json.loads(data)
    dff = pd.read_json(dataset, orient='split')
    return dcc.send_data_frame(dff.to_csv, f'{filename.replace(".csv", "")}_edited.csv')


@app.callback(
    Output('intermediate-value', 'data', allow_duplicate=True),
    Input('upload-data', 'contents'),
    Input('upload-data', 'filename'), prevent_initial_call=True
)
def set_data(contents, filename):  # получает на вход csv файл пользователя и превращает его в JSON файл
    df = parse_contents(contents, filename)
    try:
        '''
        'temperature_2m': '°C'
        'relativehumidity_2m': '%'
        'dewpoint_2m': '°C'
        'precipitation': 'mm'
        'rain': 'mm'
        'snowfall': 'cm'
        'cloudcover': '%'
        'windspeed_10m': 'km/h'
        'windspeed_100m': 'km/h'

'''
        new_cols = ('''temperature_2m °C''', '''relativehumidity_2m %''',
                    '''dewpoint_2m °C''', '''precipitation mm''',
                    '''rain mm''', '''snowfall cm''',
                    '''cloudcover %''', '''windspeed_10m km/h''',
                    '''windspeed_100m km/h''', '''dry_thunder''')
        k = '' * len(df)
        for s in new_cols:
            df[s] = k

        for i in range(len(df)):
            res = get_weather_by_coords(df['lat'][i], df['lon'][i], df['dt'][i])
            for s in new_cols:
                df[s][i] = res[s]

        dataset = df.to_json(orient='split', date_format='iso')
        return json.dumps(dataset)
    except Exception as e:
        print(e, '!2!')


@app.callback(Output('output-map', 'children'),
              Input('intermediate-value', 'data'), prevent_initial_call=True)
def update_map(data):
    dataset = json.loads(data)
    dff = pd.read_json(dataset, orient='split')
    figure = px.scatter_mapbox(
        dff,
        lat="lat",
        lon="lon",
        zoom=8,
        height=500,
        mapbox_style="open-street-map",
        hover_name=dff['lesn3'],
        hover_data={
            "lesn1": True,
            'dt': True,
            "rain mm": True,
            "snowfall cm": True,
            "dry_thunder": True,
            "cloudcover %": True,
            "lat": True,
            "lon": True
        }
    )
    figure.update_layout(margin=dict(b=0, t=0, l=0, r=0))
    children = dcc.Graph(id='map', figure=figure)
    return children


@app.callback(
    Output("intermediate-value", "data"),
    Input("table_to_filter", "filter_query"), prevent_initial_call=True)
def update_table(filter_):
    filtering_expressions = filter_.split(' && ')
    dff = Dtable
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]
    dataset = dff.to_json(orient='split', date_format='iso')
    return json.dumps(dataset)


@app.callback(
    Output('table_to_filter', 'filter_query'),
    Input('filter-query-input', 'value')
)
def write_query(query):
    if query is None:
        return ''
    return query


@app.callback(
    Output('filter-query-input', 'value'),
    Input('reset-filters', 'n_clicks'), prevent_initial_call=True
)
def reset_filters(n_clicks):
    return ''


if __name__ == '__main__':  # этот if запускает веб-приложение
    app.run_server(debug=False)
