from datetime import date, datetime
import os
import pytz

import plotly.graph_objects as go
import psycopg2
import streamlit as st

import pandas as pd

USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
DATABASE = os.getenv("DB_DATABASE")
HOST = os.getenv("DB_HOST")

# Page naming config
st.set_page_config(page_title="Predict AUS Dashboard", page_icon=":airplane_departure:")

# Title
st.title("AUS Airport TSA Wait Time Prediction")
st.write("A data-driven approach to getting you ready for your next trip!")
st.write("Created by Charlie Henry")


def get_data(table):
    conn = psycopg2.connect(host=HOST, database=DATABASE, user=USER, password=PASSWORD)

    cur = conn.cursor()

    query = f"SELECT * FROM {table}"
    cur.execute(query)
    data = cur.fetchall()
    field_names = [i[0] for i in cur.description]
    df = pd.DataFrame(data, columns=field_names)
    cur.close()
    conn.close()

    return df


def prediction_timeline_chart(df):
    df["date"] = pd.to_datetime(df["date"])

    y = df[df["passengers"] > 0]
    y["passengers"] = y["passengers"].astype(float)
    min_val = y["passengers"].min()
    max_val = y["passengers"].max()

    lowest = y["passengers"].median() - (2 * y["passengers"].std())
    highest = y["passengers"].median() + (2 * y["passengers"].std())

    v_low = y["passengers"].median() - (1.0 * y["passengers"].std())
    v_high = y["passengers"].median() + (1.0 * y["passengers"].std())

    low = y["passengers"].median() - (0.5 * y["passengers"].std())
    high = y["passengers"].median() + (0.5 * y["passengers"].std())

    today_data = df[
        df["date"]
        == date.strftime(
            datetime.now(tz=pytz.timezone("US/Central")), format="%Y-%m-%d"
        )
        ]

    fig = go.Figure()

    # Shading for the background of line plot
    fig.add_hrect(y0=0, y1=v_low, line_width=0, fillcolor="#1a9641", opacity=0.1)
    fig.add_hrect(y0=v_low, y1=low, line_width=0, fillcolor="#a6d96a", opacity=0.1)
    fig.add_hrect(y0=low, y1=high, line_width=0, fillcolor="#ffffbf", opacity=0.1)
    fig.add_hrect(y0=high, y1=v_high, line_width=0, fillcolor="#fdae61", opacity=0.1)
    fig.add_hrect(
        y0=v_high, y1=max_val * 1.2, line_width=0, fillcolor="#d7191c", opacity=0.1
    )

    # Past data line
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["passengers"],
            mode="lines",
            name="Data",
            line=dict(color="rgb(49,130,189)", width=4),
        )
    )
    # Prediction line
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["mean"],
            mode="lines",
            name="Prediction",
            line=dict(color="rgb(67,67,67)", width=2),
        )
    )

    # Error bands
    fig.add_trace(
        go.Scatter(
            x=today_data["date"],
            y=today_data["mean"],
            mode="markers",
            name="Today's prediction",
            marker=dict(
                color="rgb(161, 32, 41)",
                size=10,
                line=dict(color="MediumPurple", width=2),
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["mean"] + df["mean_se"],  # Upper error bound
            mode="lines",
            name="upper_bound",
            line=dict(color="rgba(0,0,0,0)"),  # Invisible line
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["mean"] - df["mean_se"],  # Lower error bound
            mode="lines",
            name="lower_bound",
            fill="tonexty",
            fillcolor="rgba(0,176,246,0.2)",
            line=dict(color="rgba(0,0,0,0)"),  # Invisible line
            showlegend=False,
        )
    )
    # Layout config
    fig.update_layout(
        xaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True,
            linecolor="rgb(204, 204, 204)",
            linewidth=2,
            ticks="outside",
            tickfont=dict(
                family="Arial",
                size=12,
                color="rgb(82, 82, 82)",
            ),
        ),
        yaxis=dict(
            range=[min_val * 0.80, max_val * 1.2],
            showline=True,
            showgrid=False,
            showticklabels=True,
            linecolor="rgb(204, 204, 204)",
            linewidth=2,
            ticks="outside",
            tickfont=dict(
                family="Arial",
                size=12,
                color="rgb(82, 82, 82)",
            ),
            title=dict(
                text="Total Daily Passengers",
                font=dict(
                    family="Arial",
                    color="rgb(82, 82, 82)",
                ),
            ),
        ),
        autosize=True,
        showlegend=True,
        title="AUS Passengers Last 90 Days and Prediction",
    )

    # Gauge plot
    today_val = today_data["mean"].iloc[0]
    if today_val <= low:
        title_text = "Below normal wait times expected today"

    elif today_val > low and today_val <= high:
        title_text = "Relatively normal wait times expected today"

    elif today_val > high and today_val <= v_high:
        title_text = "Above normal wait times expected today"

    elif today_val > v_high:
        title_text = "Long wait times expected today"

    fig_2 = go.Figure(
        go.Indicator(
            mode="gauge",
            value=today_val,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title_text},
            gauge={
                "axis": {"range": [lowest, highest], "visible": False},
                "bar": {"color": "black"},
                "steps": [
                    {"range": [lowest, v_low], "color": "#1a9641"},
                    {"range": [v_low, low], "color": "#a6d96a"},
                    {"range": [low, high], "color": "#ffffbf"},
                    {"range": [high, v_high], "color": "#fdae61"},
                    {"range": [v_high, highest], "color": "#d7191c"},
                ],
            },
        )
    )

    return fig, fig_2


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True


def main():
    if check_password():
        df = get_data("data_plus_prediction")
        line_plot, gauge_plot = prediction_timeline_chart(df)
        st.plotly_chart(gauge_plot)
        st.plotly_chart(line_plot)


main()
