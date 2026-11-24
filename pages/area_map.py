"""Map of the electricity areas and the latest selected reservoir month."""
import json
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from utils.data_utils import load_reservoirs, AREA_DETAILS
from utils.forecast_utils import monthly_reservoir
from utils.price_utils import daily_spot_price
from utils.quality_utils import load_electricity_areas, load_nve_regions, load_open_meteo_region


@st.cache_data(show_spinner=False)
def map_boundaries():
    areas = load_electricity_areas()[['area_code', 'geometry']].copy()
    regions = load_nve_regions()[['reg_code', 'reg_name', 'geometry']].copy()
    # Simplification keeps the browser responsive while retaining the region outlines.
    for frame in (areas, regions):
        frame['geometry'] = frame.geometry.simplify(0.005, preserve_topology=True)
    return areas, regions


def choose_area():
    points = st.session_state.area_map.selection.points
    if points:
        code = points[0].get('location')
        if code in {'NO1', 'NO2', 'NO3', 'NO4', 'NO5'}:
            st.session_state.electricity_area = code


st.title('Area map')
st.write('Choose a month to compare reservoir filling. Click an electricity area to use it on the weather and forecast pages.')
try:
    with st.spinner('Loading area boundaries and reservoir data…'):
        areas, regions = map_boundaries()
        data = load_reservoirs()
        monthly = pd.concat({code: monthly_reservoir(data, code) for code in areas.area_code}, axis=1)
except (requests.RequestException, ValueError, OSError) as error:
    st.error(f'The map data could not be loaded: {error}')
    st.stop()
monthly = monthly.dropna(how='all')
if monthly.empty:
    st.warning('No monthly reservoir values are available.')
    st.stop()
months = monthly.index.strftime('%Y-%m').tolist()
if st.session_state.get('selected_month') not in months:
    st.session_state.selected_month = months[-1]
if st.session_state.get('map_month') != st.session_state.selected_month:
    st.session_state.map_month = st.session_state.selected_month

def save_month():
    st.session_state.selected_month = st.session_state.map_month

month = st.selectbox('Last month in the history', months, key='map_month', on_change=save_month)
# Share the training length and forecast horizon with the forecast page.
selected = st.session_state.electricity_area
available_history = monthly.loc[:pd.Timestamp(month + '-01'), selected].dropna()
max_history = min(240, len(available_history))
if max_history:
    min_history = min(36, max_history)
    st.session_state.selected_history = max(min_history, min(max_history, st.session_state.get('selected_history', 120)))
    if st.session_state.get('map_history') != st.session_state.selected_history:
        st.session_state.map_history = st.session_state.selected_history
    def save_history():
        st.session_state.selected_history = st.session_state.map_history
    history = st.slider('Months of history', min_history, max_history,
                        key='map_history', on_change=save_history) if min_history < max_history else max_history
    st.caption(f'History: {available_history.tail(history).index[0]:%Y-%m} to {month}.')
if 'selected_horizon' not in st.session_state:
    st.session_state.selected_horizon = 3
if st.session_state.get('map_horizon') != st.session_state.selected_horizon:
    st.session_state.map_horizon = st.session_state.selected_horizon
def save_horizon():
    st.session_state.selected_horizon = st.session_state.map_horizon
st.slider('Months to forecast', 1, 12, key='map_horizon', on_change=save_horizon)
colour = st.selectbox('Map colour', ['Reservoir fill', 'Electricity price', 'Temperature', 'Precipitation'])
overlay = st.selectbox('Extra region outlines', ['None', 'NVE regions', 'Combined weather regions'])
first_day = pd.Timestamp(month + '-01')
last_day = first_day + pd.offsets.MonthEnd()
if colour == 'Electricity price':
    # The selected date stays inside the same month as the reservoir data.
    day_default = (first_day + pd.Timedelta(days=14)).date()
    if not first_day.date() <= st.session_state.get('price_day', day_default) <= last_day.date():
        st.session_state.price_day = day_default
    chosen_day = st.date_input('Day for spot prices', value=day_default,
                               min_value=first_day.date(), max_value=last_day.date(), key='price_day')
elif colour in {'Temperature', 'Precipitation'}:
    weather_period = st.radio('Weather period', ['Whole month', 'Selected day'], horizontal=True)
    if weather_period == 'Selected day':
        day_default = (first_day + pd.Timedelta(days=14)).date()
        if not first_day.date() <= st.session_state.get('weather_day', day_default) <= last_day.date():
            st.session_state.weather_day = day_default
        chosen_day = st.date_input('Day for weather (UTC)', value=day_default,
                                   min_value=first_day.date(), max_value=last_day.date(), key='weather_day')
if colour == 'Reservoir fill':
    values = monthly.loc[pd.Timestamp(month + '-01')].reindex(areas.area_code)
    color_title, color_scale, color_range = 'Fill %', 'Teal', (0, 100)
    details = 'monthly average of NVE weekly fill levels'
elif colour == 'Electricity price':
    day = chosen_day.isoformat()
    try:
        with st.spinner(f'Loading spot prices for {day}…'):
            values = pd.Series({code: daily_spot_price(code, day) for code in areas.area_code}).reindex(areas.area_code)
    except (requests.RequestException, ValueError) as error:
        st.error(f'The spot prices could not be loaded: {error}')
        st.stop()
    color_title, color_scale, color_range = 'NOK/kWh', 'Viridis', (None, None)
    details = f'daily average spot price on {day}, excluding grid fees and taxes'
else:
    # Five fixed points per area give a quick, reproducible comparison.
    start_day = first_day.date().isoformat() if weather_period == 'Whole month' else chosen_day.isoformat()
    end_day = last_day.date().isoformat() if weather_period == 'Whole month' else chosen_day.isoformat()
    property_column = 'temperature_2m' if colour == 'Temperature' else 'precipitation'
    try:
        with st.spinner(f'Loading weather from {start_day} to {end_day}…'):
            values = pd.Series({code: load_open_meteo_region(code, start_day, end_day, 5)[property_column].mean()
                                for code in areas.area_code}).reindex(areas.area_code)
    except (requests.RequestException, ValueError) as error:
        st.error(f'The weather data could not be loaded: {error}')
        st.stop()
    color_title = '°C' if colour == 'Temperature' else 'mm/hour'
    color_scale, color_range = 'Viridis', (None, None)
    details = f'mean {colour.lower()} from {start_day} to {end_day} UTC, using five sampled points per area'
geojson = json.loads(areas.to_json())
fig = go.Figure(go.Choroplethmap(
    geojson=geojson, locations=areas.area_code, featureidkey='properties.area_code',
    z=values.to_numpy(), zmin=color_range[0], zmax=color_range[1], colorscale=color_scale,
    marker={'opacity': 0.75, 'line': {'width': 1, 'color': 'white'}},
    colorbar={'title': color_title},
    hovertemplate=f'%{{location}}<br>{colour}: %{{z:.3f}} {color_title}<extra></extra>',
))
# A second outline highlights the selected electricity area without changing its value.
chosen = areas.loc[areas.area_code == selected]
fig.add_trace(go.Choroplethmap(
    geojson=json.loads(chosen.to_json()), locations=chosen.area_code,
    featureidkey='properties.area_code', z=[1], showscale=False,
    colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
    marker={'opacity': 0.8, 'line': {'width': 4, 'color': '#FFD166'}},
    hovertemplate=f'{selected} (selected)<extra></extra>',
))
if overlay != 'None':
    if overlay == 'Combined weather regions':
        regions['group'] = regions.reg_code.map({'RS': 'East', 'RØ': 'East', 'RV': 'West', 'RM': 'North', 'RN': 'North'})
        outlines = regions.dissolve(by='group').reset_index()
        label = 'group'
    else:
        outlines = regions
        label = 'reg_name'
    for _, region in outlines.iterrows():
        geometry = region.geometry
        polygons = list(geometry.geoms) if geometry.geom_type == 'MultiPolygon' else [geometry]
        longitude, latitude = [], []
        for polygon in polygons:
            x, y = polygon.exterior.xy
            longitude.extend([*x, None])
            latitude.extend([*y, None])
        fig.add_trace(go.Scattermap(lon=longitude, lat=latitude, mode='lines',
                                    line={'color': '#E77942', 'width': 2},
                                    name=str(region[label]), hoverinfo='skip'))
fig.update_layout(map={'style': 'carto-darkmatter', 'center': {'lat': 64.5, 'lon': 13}, 'zoom': 3.1},
                  height=650, margin={'l': 0, 'r': 0, 't': 0, 'b': 0})
st.plotly_chart(fig, width='stretch', key='area_map', on_select=choose_area, selection_mode='points')
st.caption(f'Selected area: {selected}. The colour shows the {details}.')
st.caption('Orange outlines show the additional NVE region boundaries. Colours refer to electricity areas.')
st.caption('Spot prices: [Hvakosterstrommen.no](https://www.hvakosterstrommen.no/strompris-api). Weather: Open-Meteo ERA5.')

with st.expander('Watercourse areas (VASS)'):
    st.write('NVE publishes reservoir filling for three watercourse areas. '
             'These areas have different boundaries from the electricity areas on the interactive map above.')
    rows = data.loc[(data['area_type'] == 'VASS') &
                    (data['date'].dt.to_period('M') == pd.Period(month, freq='M'))]
    records = []
    for number in (1, 2, 3):
        observed = rows.loc[rows['area_number'] == number, 'fill_fraction'].dropna()
        records.append({'Area': f'VASS {number}', 'Description': AREA_DETAILS[('VASS', number)][0],
                        'Fill level (%)': round(observed.mean() * 100, 1) if not observed.empty else None,
                        'Weekly observations': len(observed)})
    st.caption(f'Monthly averages for {month}, calculated from NVE weekly observations.')
    st.dataframe(pd.DataFrame(records), hide_index=True, width='stretch')
    choice = st.selectbox('Watercourse area', [1, 2, 3],
                          format_func=lambda number: f"VASS {number}: {AREA_DETAILS[('VASS', number)][0]}")
    vass_history = data.loc[(data['area_type'] == 'VASS') & (data['area_number'] == choice) &
                            (data['date'] <= last_day), ['date', 'fill_fraction']].dropna().sort_values('date')
    vass_history = vass_history.tail(104)
    if vass_history.empty:
        st.info('NVE returned no observations for this area and period.')
    else:
        vass_fig = go.Figure(go.Scatter(
            x=vass_history['date'], y=vass_history['fill_fraction'] * 100,
            mode='lines', line={'color': '#56C5C2', 'width': 2},
            hovertemplate='%{x|%d %b %Y}<br>Fill: %{y:.1f}%<extra></extra>',
        ))
        vass_fig.update_layout(title=f'VASS {choice}: weekly reservoir filling',
                               xaxis_title='Date', yaxis_title='Fill level (%)',
                               yaxis_range=[0, 100], hovermode='x unified', height=350,
                               margin={'l': 0, 'r': 0, 't': 50, 'b': 0})
        st.plotly_chart(vass_fig, width='stretch')
        st.caption('Up to 104 weekly observations ending in the selected month. '
                   'Changing this VASS selection does not change the electricity area.')
    st.markdown('[Source: NVE reservoir areas and statistics](https://www.nve.no/nytt-fra-nve/rapporter-vassmagasinstatistikk/)')
    st.image('https://www.nve.no/media/1064/kartmagasinomrader250.jpg',
             caption='NVE overview of the water reservoir areas. This image is a reference map; it is not interactive.',
             width=350)
