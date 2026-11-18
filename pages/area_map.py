"""Map of the electricity areas and the latest selected reservoir month."""
import json
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from utils.data_utils import load_reservoirs
from utils.forecast_utils import monthly_reservoir
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

month = st.selectbox('Month', months, key='map_month', on_change=save_month)
colour = st.selectbox('Map colour', ['Reservoir fill', 'Temperature', 'Precipitation'])
overlay = st.selectbox('Extra region outlines', ['None', 'NVE regions', 'Combined weather regions'])
selected = st.session_state.electricity_area
if colour == 'Reservoir fill':
    values = monthly.loc[pd.Timestamp(month + '-01')].reindex(areas.area_code)
    color_title, color_scale, color_range = 'Fill %', 'Teal', (0, 100)
    details = 'monthly average of NVE weekly fill levels'
else:
    # A single day and five points per area keep the first comparison lightweight.
    day = (pd.Timestamp(month + '-01') + pd.Timedelta(days=14)).date().isoformat()
    property_column = 'temperature_2m' if colour == 'Temperature' else 'precipitation'
    try:
        with st.spinner(f'Loading weather for {day}…'):
            values = pd.Series({code: load_open_meteo_region(code, day, day, 5)[property_column].mean()
                                for code in areas.area_code}).reindex(areas.area_code)
    except (requests.RequestException, ValueError) as error:
        st.error(f'The weather data could not be loaded: {error}')
        st.stop()
    color_title = '°C' if colour == 'Temperature' else 'mm/hour'
    color_scale, color_range = 'Viridis', (None, None)
    details = f'mean {colour.lower()} on {day} from five sampled points per area'
geojson = json.loads(areas.to_json())
fig = go.Figure(go.Choroplethmap(
    geojson=geojson, locations=areas.area_code, featureidkey='properties.area_code',
    z=values.to_numpy(), zmin=color_range[0], zmax=color_range[1], colorscale=color_scale,
    marker={'opacity': 0.75, 'line': {'width': 1, 'color': 'white'}},
    colorbar={'title': color_title},
    hovertemplate=f'%{{location}}<br>{colour}: %{{z:.1f}} {color_title}<extra></extra>',
))
# A second outline highlights the selected electricity area without changing its value.
chosen = areas.loc[areas.area_code == selected]
fig.add_trace(go.Choroplethmap(
    geojson=json.loads(chosen.to_json()), locations=chosen.area_code,
    featureidkey='properties.area_code', z=[1], showscale=False,
    colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
    marker={'opacity': 0.8, 'line': {'width': 4, 'color': '#202020'}},
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
fig.update_layout(map={'style': 'carto-positron', 'center': {'lat': 64.5, 'lon': 13}, 'zoom': 3.1},
                  height=650, margin={'l': 0, 'r': 0, 't': 0, 'b': 0})
st.plotly_chart(fig, width='stretch', key='area_map', on_select=choose_area, selection_mode='points')
st.caption(f'Selected area: {selected}. The colour shows the {details}.')
st.caption('Orange outlines show the additional NVE region boundaries. Colours refer to electricity areas.')
st.info('Electricity price is not yet available as a map colour.')
