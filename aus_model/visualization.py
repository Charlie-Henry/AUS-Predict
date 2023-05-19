from datetime import date, datetime
import os
import pytz

import plotly.graph_objects as go
import psycopg2

import pandas as pd

USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
DATABASE = os.getenv("DB_DATABASE")
HOST = os.getenv("DB_HOST")

conn = psycopg2.connect(
    host=HOST,
    database=DATABASE,
    user=USER,
    password=PASSWORD)

cur = conn.cursor()

query = "SELECT * FROM data_plus_prediction"
cur.execute(query)
data = cur.fetchall()
field_names = [i[0] for i in cur.description]
df = pd.DataFrame(data, columns=field_names)
df['date'] = pd.to_datetime(df['date'])

today_data = df[df["date"] == date.strftime(datetime.now(tz=pytz.timezone('US/Central')), format="%Y-%m-%d")]

fig = go.Figure()
fig.add_trace(go.Scatter(x=df["date"], y=df["passengers"],
                    mode='lines',
                    name='Data',
                    line=dict(color='rgb(49,130,189)', width=4)))
fig.add_trace(go.Scatter(x=df["date"], y=df["mean"],
                    mode='lines',
                    name='Prediction',
                    line=dict(color='rgb(67,67,67)', width=2, dash="dash")))
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["mean"] + df["mean_se"],  # Upper error bound
    mode='lines',
    name='upper_bound',
    line=dict(color='rgba(0,0,0,0)'),  # Invisible line
    showlegend=False
))

fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["mean"] - df["mean_se"],  # Lower error bound
    mode='lines',
    name='lower_bound',
    fill='tonexty',
    fillcolor='rgba(0,176,246,0.2)',
    line=dict(color='rgba(0,0,0,0)'),  # Invisible line
    showlegend=False
))
fig.update_layout(
    xaxis=dict(
        showline=True,
        showgrid=False,
        showticklabels=True,
        linecolor='rgb(204, 204, 204)',
        linewidth=2,
        ticks='outside',
        tickfont=dict(
            family='Arial',
            size=12,
            color='rgb(82, 82, 82)',
        ),
    ),
    yaxis=dict(
        showline=True,
        showgrid=False,
        showticklabels=True,
        linecolor='rgb(204, 204, 204)',
        linewidth=2,
        ticks='outside',
        tickfont=dict(
            family='Arial',
            size=12,
            color='rgb(82, 82, 82)',
        ),
        title=dict(
            text="Total Daily Passengers",
            font=dict(
                family='Arial',
                color='rgb(82, 82, 82)',
            )
        )
    ),
    autosize=True,
    showlegend=True,
    plot_bgcolor='white',
    title="AUS Passengers Last 90 Days and Prediction"
)

fig.write_image("pred_plot.png")
#fig.show()

cur.close()
conn.close()