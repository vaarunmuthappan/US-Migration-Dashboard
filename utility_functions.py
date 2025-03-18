import streamlit as st
import pandas as pd
from collections import defaultdict
import pickle
import plotly.graph_objects as go
import plotly.express as px
from shapely.geometry import shape


def get_data_from_file(file):
    with open(file, 'rb') as file:
        opened = pickle.load(file)
    return opened


def plot_map(migration_sorted, code_to_name):
    columns = ['ID', 'name', 'lat', 'long', 'migration']
    migration_data = pd.DataFrame(columns=columns)
    rows_to_add = []

    location_data = pd.read_csv('data/counties_national.txt',
                                # specify the delimiter (tab in this case)
                                sep='\t',
                                usecols=[1, 3, 8, 9])
    l_dict = defaultdict(list)
    for _, row in location_data.iterrows():
        county = str(row['GEOID']).zfill(5)
        l_dict[county] = [
            row['INTPTLAT'], row[-1]]

    for county_pair in migration_sorted:
        if len(l_dict[county_pair[0]]) > 0:
            rows_to_add.append({
                'ID': county_pair[0],
                'name': code_to_name[county_pair[0]],
                'lat': l_dict[county_pair[0]][0],
                'long': l_dict[county_pair[0]][1],
                'migration': county_pair[1]
            })

    migration_data = pd.concat(
        [migration_data, pd.DataFrame(rows_to_add)], ignore_index=True)

    return migration_data


@st.cache_data
def get_ny_data(code_to_name):
    NY_county_codes = ["36047", "36081", "36061", "36103", "36005", "36059", "36119", "34003", "34023", "36031", "34017", "34025",
                       "34029", "34029", "34039", "34031", "34027", "36085", "36071", "36087", "36027", "34037", "34019", "36079", "42103"]

    out_migration = get_data_from_file('data/out_migration.pkl')
    in_migration = get_data_from_file('data/in_migration.pkl')

    dictionary = defaultdict(defaultdict)

    for code in NY_county_codes:
        dictionary[code] = {
            "name": code_to_name[code],
            "in_migration": in_migration[code],
            "out_migration": out_migration[code]
        }

    records = []
    for code in dictionary:
        records.append({'code': code, 'County': dictionary[code]['name'],
                        'In-Migration': dictionary[code]['in_migration'], 'Out-Migration': dictionary[code]['out_migration']})

    ny_data = pd.DataFrame(records)

    return ny_data


def create_sankey_diagram(dataframe):
    # Create lists of all unique labels (nodes)
    all_nodes = sorted(
        list(set(dataframe["initial"].tolist() + dataframe["final"].tolist())))

    # Create a mapping from node labels to indices
    node_indices = {node: i for i, node in enumerate(all_nodes)}

    # Create source and target arrays
    sources = [node_indices[initial] for initial in dataframe["initial"]]
    targets = [node_indices[final] for final in dataframe["final"]]
    values = dataframe["value"].tolist()

    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=all_nodes,
            color="blue"
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values
        )
    )])

    fig.update_layout(
        title_text=f"Sankey Diagram",
        font_size=12,
        height=600
    )

    return fig


@st.cache_data
def get_df_cleaned(sorted_pairs_by_exemptions, code_to_name):
    df_interactions = pd.DataFrame(sorted_pairs_by_exemptions, columns=[
        'County_Code', 'Migration_Count'])
    df_interactions['County_Name1'] = df_interactions['County_Code'].map(
        lambda x: code_to_name.get(x[0:5], f"Unknown ({x})"))
    df_interactions['County_Name2'] = df_interactions['County_Code'].map(
        lambda x: code_to_name.get(x[5:], f"Unknown ({x})"))
    df_result = df_interactions[[
        'County_Name1', 'County_Name2', 'Migration_Count', 'County_Code']]

    return df_result


def make_choropleth(input_df, selected_county_name, geojson):
    input_df['Trimmed_Names'] = input_df['County_Name2'].str[:-10]

    # Create choropleth map
    fig = px.choropleth(
        input_df,
        geojson=geojson,
        locations="Trimmed_Names",
        featureidkey="properties.NAME",
        color="Migration_Count",
        color_continuous_scale="Blues",
        projection="mercator"
    )

    # Find centroid of selected county for zoom
    selected_county_trimmed = selected_county_name[:-10]
    county_geometry = next(
        (feature["geometry"] for feature in geojson["features"]
         if feature["properties"]["NAME"] == selected_county_trimmed),
        None
    )

    if county_geometry:
        # Calculate centroid using Shapely
        county_shape = shape(county_geometry)
        centroid = county_shape.centroid

        # Set map view to centered on county
        fig.update_geos(
            center={"lon": centroid.x, "lat": centroid.y},
            projection_scale=15,  # Adjust zoom level (higher = more zoomed in)
            showcoastlines=True,
            coastlinecolor="Black",
            showland=True,
            landcolor="LightGray",
            showlakes=True,
            lakecolor="LightBlue",
        )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig
