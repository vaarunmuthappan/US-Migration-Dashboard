from utility_functions import get_data_from_file, get_ny_data, plot_map, get_df_cleaned, make_choropleth
import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import subprocess


code_to_name = get_data_from_file('data/code_to_name.pkl')
sorted_pairs_by_exemptions = get_data_from_file(
    'data/sorted_pairs_by_exemptions.pkl')
out_migration_sorted = get_data_from_file('data/out_migration_sorted.pkl')
in_migration_sorted = get_data_from_file('data/in_migration_sorted.pkl')
out_migration = get_data_from_file('data/exemption_count.pkl')

st.set_page_config(
    page_title="2003-2004 US Migration Patterns", layout="wide")

st.title("US Migration Patterns in 2003-2004")

st.subheader("County pairs with the most interaction (by exemption)")
df_interactions = pd.DataFrame(sorted_pairs_by_exemptions, columns=[
    'County_Code', 'Migration_Count'])
df_interactions['County_Name1'] = df_interactions['County_Code'].map(
    lambda x: code_to_name.get(x[0:5], f"Unknown ({x})"))
df_interactions['County_Name2'] = df_interactions['County_Code'].map(
    lambda x: code_to_name.get(x[5:], f"Unknown ({x})"))
df_out_migration = df_interactions[[
    'County_Name1', 'County_Name2', 'Migration_Count', 'County_Code']]

df_interactions = get_df_cleaned(sorted_pairs_by_exemptions, code_to_name)
df_out_migration = get_df_cleaned(out_migration_sorted, code_to_name)
df_in_migration = get_df_cleaned(in_migration_sorted, code_to_name)

st.dataframe(df_interactions, hide_index=True, use_container_width=True, column_config={
    "County_Name1": "County",
    "County_Name2": "County",
    "Migration_Count": "Interactions",
    "County_Code": None
})


col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("Top Counties by Out-Migration")
    out_data = plot_map(out_migration_sorted, code_to_name)
    st.pydeck_chart(
        pdk.Deck(
            map_style=None,  # Uses Streamlit's theme automatically
            initial_view_state=pdk.ViewState(
                latitude=38.0,  # Center point between the two locations
                longitude=-103.0,
                zoom=4,
                pitch=50,
            ),
            layers=[
                # Hexagon layer to show migration density
                pdk.Layer(
                    "ColumnLayer",
                    data=out_data,
                    get_position=["long", "lat"],
                    get_elevation="migration",
                    elevation_scale=1,  # Adjust this value to control tower height
                    radius=5000,  # Adjust for column width
                    pickable=True,
                    auto_highlight=True,
                    # Orange-ish color like in the image
                    get_fill_color=[255, 0, 0],
                    coverage=1,
                ),
                # Scatterplot layer to show exact points
                pdk.Layer(
                    "ScatterplotLayer",
                    data=out_data,
                    get_position="[long, lat]",
                    get_color="[255, 0, 0]",
                    get_radius="migration/5000",  # Size based on migration value
                    pickable=True,
                ),
            ],
        )
    )

    with st.expander("See data"):
        st.dataframe(df_out_migration, hide_index=True, use_container_width=True, column_config={
            "County_Name1": "County",
            "Migration_Count": "Out-Migration",
            "County_Name2": None,
            "County_Code": None
        })

with col2:
    st.subheader("Top Counties by In-Migration")
    in_data = plot_map(in_migration_sorted, code_to_name)
    st.pydeck_chart(
        pdk.Deck(
            map_style=None,  # Uses Streamlit's theme automatically
            initial_view_state=pdk.ViewState(
                latitude=38.0,  # Center point between the two locations
                longitude=-103.0,
                zoom=4,
                pitch=50,
            ),
            layers=[
                # Hexagon layer to show migration density
                pdk.Layer(
                    "ColumnLayer",
                    data=in_data,
                    get_position=["long", "lat"],
                    get_elevation="migration",
                    elevation_scale=1,  # Adjust this value to control tower height
                    radius=5000,  # Adjust for column width
                    pickable=True,
                    auto_highlight=True,
                    # Orange-ish color like in the image
                    get_fill_color=[0, 255, 0],
                    coverage=1,
                ),
                # Scatterplot layer to show exact points
                pdk.Layer(
                    "ScatterplotLayer",
                    data=in_data,
                    get_position="[long, lat]",
                    get_color="[0, 255, 0]",
                    get_radius="migration/5000",  # Size based on migration value
                    pickable=True,
                ),
            ],
        )
    )

    with st.expander("See data"):
        st.dataframe(df_in_migration, hide_index=True, use_container_width=True, column_config={
            "County_Name1": "County",
            "Migration_Count": "In-Migration",
            "County_Name2": None,
            "County_Code": None
        })

st.subheader("Net Migration to the New York metropolitan area counties")
new_york_data = get_ny_data(code_to_name)
st.bar_chart(new_york_data, x="County", y=[
             "In-Migration", "Out-Migration"], color=["#8fbc8f", "#FF7276"])


st.subheader("Explore the migration data:")

out_migration_dict = {code: value for code, value in out_migration_sorted}
in_migration_dict = {code: value for code, value in in_migration_sorted}
county_options = list(code_to_name.values())
county_codes = list(code_to_name.keys())
ny_county_name = "New York County, NY"
default_index = county_options.index(
    ny_county_name) if ny_county_name in county_options else 0
# Create the dropdown for county selection
selected_county_name = st.selectbox(
    "Select a County:",
    options=county_options,
    index=default_index
)

# Get the code for the selected county
selected_county_code = county_codes[county_options.index(selected_county_name)]

# Get migration data for the selected county
out_migration = out_migration_dict.get(selected_county_code, 0)
in_migration = in_migration_dict.get(selected_county_code, 0)
net_migration = in_migration - out_migration
st.subheader(f"Selected County: {selected_county_name}")

# Create three cards in a column
# For the cards showing migration statistics
in_color = "#00cc66"  # Green for in-migration
out_color = "#ff3300"  # Red for out-migration
in_bg_color = "#e6fff2"  # Light green background
out_bg_color = "#ffe6e6"  # Light red background
filtered_df_interactions = df_interactions.loc[df_interactions['County_Name1']
                                               == selected_county_name]

col = st.columns((2, 2, 2), gap="medium")
with col[0]:
    # In-Migration Card (Green)
    st.markdown(f"""
    <div style="padding: 20px; border-radius: 15px; background-color: {in_bg_color}; margin-bottom: 20px;">
        <h3 style="color: {in_color};">In-Migration</h3>
        <h2 style="color: {in_color}; font-size: 36px;">{in_migration:,}</h2>
        <p>People moved into this county</p>
    </div>
    """, unsafe_allow_html=True)

with col[1]:
    # Out-Migration Card (Red)
    st.markdown(f"""
        <div style="padding: 20px; border-radius: 15px; background-color: {out_bg_color}; margin-bottom: 20px;">
            <h3 style="color: {out_color};">Out-Migration</h3>
            <h2 style="color: {out_color}; font-size: 36px;">{out_migration:,}</h2>
            <p>People moved out of this county</p>
        </div>
        """, unsafe_allow_html=True)

with col[2]:
    # Net Migration Card (Green if positive, Red if negative)
    net_migration = in_migration - out_migration
    net_color = in_color if net_migration >= 0 else out_color
    net_bg_color = "whitesmoke"
    net_sign = "+" if net_migration > 0 else ""
    st.markdown(f"""
    <div style="padding: 20px; border-radius: 15px; background-color: {net_bg_color}; margin-bottom: 20px;">
        <h3 style="color: {net_color};">Net Migration</h3>
        <h2 style="color: {net_color}; font-size: 36px;">{net_sign}{net_migration:,}</h2>
        <p>{"Population gain" if net_migration >= 0 else "Population loss"}</p>
    </div>
    """, unsafe_allow_html=True)

col = st.columns((4, 2), gap="medium")
with col[0]:
    with open('data/counties.geojson') as f:
        geojson = json.load(f)
    fig = make_choropleth(
        filtered_df_interactions, selected_county_name, geojson)
    st.plotly_chart(fig, use_container_width=True)

with col[1]:
    st.dataframe(filtered_df_interactions,
                 column_order=("County_Name2", "Migration_Count"),
                 hide_index=True,
                 width=None,
                 use_container_width=True,
                 column_config={
                     "County_Name2": st.column_config.TextColumn(
                         "County",
                     ),
                     "Migration_Count": st.column_config.ProgressColumn(
                         "Interactions",
                         format="%f",
                         min_value=0,
                         max_value=max(
                             filtered_df_interactions.Migration_Count),
                     )}
                 )

st.write("")
st.subheader("Ask a question about the migration data:")

# Path to the downloaded model
model_path = "Llama-3.2-1B-Instruct-Q4_0_4_4.gguf"

# Load the GPT4All model

# Context Prompt
context_prompt = ""
# User input
user_input = st.text_area("Enter your question here:")
# Combined question with context
combined_input = context_prompt + user_input

if st.button("Get Answer"):
    if user_input:

        st.write("### Answer:")
        st.write(combined_input)
    else:
        st.write("Please enter a question.")
