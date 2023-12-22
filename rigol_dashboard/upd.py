import sys
import time
import threading

import plotly.express as px
import pandas as pd

from ipaddress import IPv4Address

from dash import Dash, html, dcc, callback, Output, Input

from rigol_dashboard.capture_rigol import Datapoints, Rigol

app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1(children="Scope", style={"textAlign": "center"}),
        dcc.Graph(id="graph-content"),
        dcc.Interval(id="interval-component", interval=1 * 500, n_intervals=0),  # in milliseconds
    ]
)

last_data: Datapoints


@callback(Output("graph-content", "figure"), Input("interval-component", "n_intervals"))
def update_graph(_):
    data = last_data.waveform
    x = list(range(len(data)))
    dff = pd.DataFrame(zip(x, data), columns=["x", "y"])
    fig = px.line(dff, x="x", y="y", labels={"x": "time", "y": "V"})
    fig.update_layout(
        xaxis={
            "tickmode": "array",
            "tickvals": list(range(0, last_data.datapoints, last_data.datapoints//last_data.xtick_count)),
            "ticktext": list(map(lambda x: format_xtick(x, last_data.x_scale), range(last_data.xtick_count))),
        }
    )

    return fig


def format_xtick(idx, xscale):
    nanos = xscale / 1e-09

    units = ["ns", "μs", "ms", "s"]
    unit_idx = 0
    while (idx * nanos) >= 999.9999999999999:
        nanos /= 1000
        unit_idx += 1

    unit = units[unit_idx]
    value = nanos * idx
    strval = f"{value:.1f}".replace(".0", "")
    return f"{strval}{unit}"


def update_in_bg(ip: IPv4Address):
    global last_data
    print("THIS STARTS A NEW THREAD")
    r = Rigol(ip)
    r.connect()
    r.setup_channel("CHAN2")
    while True:
        last_data = r.capture_channel("CHAN2")
        time.sleep(0.5)


if __name__ == "__main__":
    t = threading.Thread(target=update_in_bg, args=[IPv4Address(sys.argv[1])])
    t.start()
    app.run(debug=True, host="0.0.0.0")
