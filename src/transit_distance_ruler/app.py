import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.express as px
from dash import Dash, Input, Output, callback, dcc, html
from dash.development.base_component import Component
from sklearn.metrics.pairwise import haversine_distances

from transit_distance_ruler.gtfs import TransitDB

KM_PER_MILE = 1.609344
EARTH_RADIUS_MILES = 3959
EARTH_RADIUS_KM = 6371

db = TransitDB()
db.load()

app = Dash(title="Transit Distance Ruler")


def Grid(*rows: list[list[Component]]):
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [comp],
                        style={
                            "display": "inline-block",
                            "width": f"{90 // len(row)}%",
                        },
                    )
                    for comp in row
                ]
            )
            for row in rows
        ],
        style={"align-items": "center"},
    )


app.layout = [
    html.H1(children="Transit Distance Ruler", style={"textAlign": "center"}),
    html.Div(
        [
            html.Label("Agency", id="agency-label"),
            dcc.Dropdown(db.all_agencies, id="agency-selection"),
            html.Label("Mode", id="mode-label"),
            dcc.Dropdown([], id="mode-selection"),
            html.Label("Route", id="route-label"),
            dcc.Dropdown([], id="route-selection"),
            html.Label("Direction", id="direction-sel-label"),
            Grid(
                [
                    html.Label(
                        "---",
                        id="left-direction-label",
                        style={"textAlign": "left"},
                    ),
                    daq.ToggleSwitch(
                        id="direction-switch",
                    ),
                    html.Label(
                        "---",
                        id="right-direction-label",
                        style={"textAlign": "right"},
                    ),
                ]
            ),
            html.Label("From", id="start-label"),
            dcc.Dropdown([], id="start-selection"),
            html.Label("To", id="end-label"),
            dcc.Dropdown([], id="end-selection"),
            Grid(
                [
                    html.Label(
                        "miles",
                        id="unit-miles-label",
                        style={"textAlign": "right"},
                    ),
                    daq.ToggleSwitch(
                        id="unit-switch",
                    ),
                    html.Label(
                        "km",
                        id="unit-km-label",
                        style={"textAlign": "left"},
                    ),
                ]
            ),
        ],
        style={
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": "16rem",
            "padding": "2rem 1rem",
            "background-color": "#f8f9fa",
        },
    ),
    html.Div(
        [
            dcc.Graph(id="map-display"),
            dcc.Textarea(id="text-output"),
        ],
        style={
            "margin-left": "18rem",
            "margin-right": "2rem",
            "padding": "2rem 1rem",
        },
    ),
]


@callback(Output("mode-selection", "options"), Input("agency-selection", "value"))
def update_available_modes(agency):
    if agency is None:
        return []
    return db.get_supported_modes(agency)


@callback(
    Output("route-selection", "options"),
    Input("agency-selection", "value"),
    Input("mode-selection", "value"),
)
def update_available_routes(agency, mode):
    if agency is None:
        return []
    return db.get_routes(agency, mode)


@callback(
    Output("left-direction-label", "children"),
    Output("right-direction-label", "children"),
    Input("agency-selection", "value"),
    Input("route-selection", "value"),
)
def update_direction_switch_label(agency, route):
    if None in (agency, route):
        return "---", "---"
    return db.get_route_directions(agency, route)


@callback(
    Output("start-selection", "options"),
    Output("end-selection", "options"),
    Input("agency-selection", "value"),
    Input("route-selection", "value"),
    Input("direction-switch", "value"),
)
def update_available_stops(agency, route, direction):
    if None in (agency, route):
        return [], []
    stops = db.get_stops(agency, route, direction)
    return stops, stops


@callback(
    Output("map-display", "figure"),
    Output("text-output", "value"),
    Input("agency-selection", "value"),
    Input("route-selection", "value"),
    Input("direction-switch", "value"),
    Input("start-selection", "value"),
    Input("end-selection", "value"),
    Input("unit-switch", "value"),
)
def update_graph(agency, route, direction, start, end, is_km):
    if None in (agency, route, start, end):
        return px.scatter_map(), ""
    df = db.get_route_frame(agency, route, direction, start, end)
    # TODO: more precise metrics. For now, use great-circle distance between stops.
    segments = haversine_distances(df.loc[["latitude", "longitude"]].to_numpy())
    length = segments[0, :].sum()
    direct_length = segments[0, -1]
    if is_km:
        length *= KM_PER_MILE
        direct_length *= EARTH_RADIUS_KM
    else:
        direct_length *= EARTH_RADIUS_MILES
    text_content = f"""Total distance: {length}
As the crow flies: {direct_length}
EDI: {length / direct_length if direct_length >= 0.1 else "undefined"}
"""
    fig = px.scatter_map(
        df,
        lat="latitude",
        lon="longitude",
        mode="markers+lines",
        hover_name="stop_name",
    )
    return fig, text_content


if __name__ == "__main__":
    app.run(debug=True)
