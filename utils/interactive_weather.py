"""Interactive versions of the weather checks."""
import numpy as np
import plotly.graph_objects as go
from scipy.fft import dct, idct
from sklearn.neighbors import LocalOutlierFactor
from utils.quality_utils import robust_limits

PROPERTIES = {'Temperature': ('temperature_2m', '°C'), 'Precipitation': ('precipitation', 'mm/hour')}


def weather_check(weather, property_name, method, cutoff=0.08, n_sd=3.0, contamination=0.01):
    column, unit = PROPERTIES[property_name]
    data = weather.dropna(subset=[column]).sort_values('time')
    values = data[column].to_numpy(dtype=float)
    if len(values) < 20:
        raise ValueError('At least 20 hourly observations are needed.')
    fig = go.Figure()
    fig.add_scatter(x=data['time'], y=values, mode='lines', name=property_name,
                    line={'color': '#2F6F73', 'width': 1})
    if method == 'SPC':
        coefficients = dct(values, type=2, norm='ortho')
        keep = max(1, int(np.ceil(len(values) * cutoff)))
        background = idct(np.r_[coefficients[:keep], np.zeros(len(values)-keep)], type=2, norm='ortho')
        residual = values - background
        center, _, low, high = robust_limits(residual, n_sd)
        flags = (residual < low) | (residual > high)
        fig.add_scatter(x=data['time'], y=background + center, name='Background', line={'color': '#777'})
        for i, limit in enumerate((low, high)):
            fig.add_scatter(x=data['time'], y=background + limit, name='Limits',
                            showlegend=i == 0, line={'color': '#A45A52', 'dash': 'dash'})
    elif method == 'LOF':
        series = data[column].astype(float)
        baseline = series.rolling(24, center=True, min_periods=6).median().bfill().ffill()
        features = np.column_stack((values, (series - baseline).to_numpy()))
        flags = LocalOutlierFactor(n_neighbors=min(20, len(data)-1), contamination=contamination).fit_predict(features) == -1
    else:
        raise ValueError('Choose SPC or LOF.')
    fig.add_scatter(x=data.loc[flags, 'time'], y=values[flags], mode='markers', name='Flagged hours',
                    marker={'color': '#D06A2E', 'size': 6})
    fig.update_layout(title=f'{property_name}: {method} check', xaxis_title='Date',
                      yaxis_title=f'{property_name} ({unit})', hovermode='x unified')
    return fig, int(flags.sum()), len(data)
