import streamlit as st
import pandas as pd
import requests
from io import StringIO
import altair as alt 
import folium
from streamlit_folium import folium_static


# Function to retrieve and preprocess data.
@st.cache_data(show_spinner = "Loading data from API...")
def load_data():
    api_url = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/controle_techn/exports/csv?delimiter=%2C&list_separator=%2C&quote_all=false&with_bom=true"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        try:
            data = pd.read_csv(StringIO(response.text), low_memory = False)
            return data
        except pd.errors.ParserError as e:
            st.error(f"Failed to parse data. Parser error: {str(e)}")
            return None
    else:
        st.error(f"Failed to fetch data. Status code: {response.status_code}")
        return None

# Function to create a bar chart for department distribution
@st.cache_data(show_spinner="Calculating distribution...")
def create_dept_distribution_chart(data):
    st.subheader("Distribution of Inspection Centers by Department")
    department_count = data['cct_code_dept'].value_counts().reset_index()
    department_count.columns = ['Department', 'Count']

    # Internal Streamlit bar chart
    st.bar_chart(department_count.set_index('Department'))

# Function to create bar charts for vehicle categories and energy types
@st.cache_data(show_spinner = "Making the charts...")
def create_category_energy_charts(data, column_name, chart_title):
    st.subheader(f"Distribution of {chart_title}")
    category_count = data[column_name].value_counts().reset_index()
    category_count.columns = [chart_title, 'Count']
    
    chart = alt.Chart(category_count).mark_bar().encode(
        x=alt.X(f'{chart_title}:O', sort='-y'),
        y='Count',
        tooltip=[chart_title, 'Count']
    ).properties(
        width=600
    )
    
    st.altair_chart(chart)

# Function to create a bar chart for inspection prices (prix_visite)
@st.cache_data(show_spinner = "Calculating price distribution...")
def create_price_distribution_bar_chart(data):
    st.subheader("Distribution of Inspection Prices (prix_visite)")
    chart = alt.Chart(data).mark_bar().encode(
        alt.X("prix_visite:Q", bin=True, title="Price"),
        alt.Y("count()", title="Count"),
        tooltip=["prix_visite:Q", "count()"]
    ).properties(
        width=600
    )
    
    st.altair_chart(chart)

# Function to create a time series line chart for inspection prices over time
@st.cache_data(show_spinner="Calculating time series...")
def create_price_time_series_chart(data):
    st.subheader("Temporal Analysis: Inspection Prices Over Time (Streamlit Plot)")

    chart_data = data.groupby('date_application_visite')['prix_visite'].mean().reset_index()
    
    st.line_chart(chart_data.set_index('date_application_visite'))




# Function to create a time series line chart for inspection prices over a specified time period
@st.cache_data(show_spinner = "Calculating time period...")
def create_price_time_period_chart(data, start_date, end_date):
    st.subheader("Temporal Analysis: Inspection Prices Over Time")

    # Filter the data based on the specified time period
    filtered_data = data[(pd.to_datetime(data['date_application_visite'], format='mixed', errors='coerce') >= start_date) & (pd.to_datetime(data['date_application_visite'], format='mixed', errors='coerce') <= end_date)]
    chart = alt.Chart(filtered_data).mark_bar().encode(
        x=alt.X('yearmonth(date_application_visite):O', title="Date"),
        y=alt.Y('mean(prix_visite):Q', title="Mean Inspection Price"),
        tooltip=['yearmonth(date_application_visite):O', 'mean(prix_visite):Q']
    ).properties(
        width=800
    )
    
    st.altair_chart(chart)

# Extract latitude and longitude from the coordgeo column
def extract_coordinates(coordgeo):
    try:
        latitude, longitude = map(float, coordgeo.split(","))
        return latitude, longitude
    except ValueError:
        return None, None

# Function to display the map
@st.cache_resource(show_spinner="Creating Map...")
def display_inspection_centers_map(data):
    # Create a Folium map centered on France
    m = folium.Map(location=[46.603354, 1.888334], zoom_start=6)

    # Create a set to keep track of unique centers
    unique_centers = set()

    # Add markers for each center using the coordinates from the coordgeo column
    for index, row in data.iterrows():
        center_name = row['cct_denomination']
        if center_name not in unique_centers:
            latitude, longitude = extract_coordinates(row['coordgeo'])
            if latitude is not None and longitude is not None:
                folium.Marker(
                    location=[latitude, longitude],
                    popup=center_name,
                ).add_to(m)
            unique_centers.add(center_name)

    return m

# Guide or Help Section
def guide_sidebar():
    st.sidebar.title("User Guide")
    st.sidebar.write("Welcome to the Inspection Center Finder! Here's how to use the app:")

    st.sidebar.subheader("1. Load Data")
    st.sidebar.write("Start by clicking 'Click Here to Load the Data' to load inspection center data.")
    
    st.sidebar.subheader("2. Filter by Department")
    st.sidebar.write("Use the 'Filter by Department' dropdown to select one or more departments or 'All'.")

    st.sidebar.subheader("3. Display Map")
    st.sidebar.write("Check the 'Display Map' checkbox to see inspection centers on the map.")
    
    st.sidebar.subheader("4. Show more options")
    st.sidebar.write("Enable 'Show more options' to apply additional filters and and get more visualization.")
    
    st.sidebar.subheader("5. Visualizations")
    st.sidebar.write("Use the checkboxes in the sidebar to show/hide different charts.")
    
    st.sidebar.subheader("6. Date Range Filter")
    st.sidebar.write("Select a time frame for price variation and click 'Show Price Variation'.")

    st.sidebar.subheader("7. Refresh Data")
    st.sidebar.write("If needed, you can refresh the data using the 'Refresh Data' button.")

# Function to create a sidebar with your information and links to GitHub and LinkedIn
def about_me_sidebar():
    st.sidebar.title("This is the result of project on Data Visualization.")
    st.sidebar.text("Hello! I am Mohamed AALI ANDELLA")
    st.sidebar.write("I am an engineering student at EFREI Paris with a passion for data visualization and analysis.")
    st.sidebar.write("#DataVizEfrei2023")
    st.sidebar.markdown("Find me on:")
    st.sidebar.markdown("[LinkedIn](https://www.linkedin.com/in/aali-andella/)")
    st.sidebar.markdown("[GitHub](https://github.com/Moha78200)")

# Streamlit application
st.set_page_config(
    page_title="Find Inspection Centers Nearby",
    page_icon="🚗",
    layout="wide",
)

st.title("Find The Nearest Inspection Center to You!")

# Load the data lazily
data = None
load_data_button = st.sidebar.checkbox("Click Here to Load the Data")

if load_data_button:
    data = load_data()

# Create a button switch to toggle between "About Me" and "User Guide"
selected_tab = st.radio("Choose a tab:", ["About Me", "User Guide"])

# Display the selected content
if selected_tab == "About Me":
    about_me_sidebar()
else:
    guide_sidebar()


if data is not None:

    # Create custom filters for department, vehicle category, energy type, and price range
    st.sidebar.title("Options")
    st.write("Data is currently loaded!")
    st.write("Please use the filters on the bottom-left side-bar to personnalize your search and find what you need!")
    # Apply filters to the data
    filtered_data = data.copy()
    selected_departments = st.sidebar.multiselect("Filter by Department", ["All"] + list(data['cct_code_dept'].unique()), default=["All"])
    if "All" not in selected_departments:
        filtered_data = filtered_data[filtered_data['cct_code_dept'].isin(selected_departments)]

    # Display the map
    st.sidebar.warning("It is recomended to select the department(s) before loading the map!")
    st.sidebar.write("Use the map to see inspection centers near you.")
    display_map = st.sidebar.checkbox("Display Map")

    if display_map:
        map = display_inspection_centers_map(filtered_data)
        st.subheader("Inspection Center Locations")
        folium_static(map)


    # Add a button to show visualizations
    more_options = st.sidebar.checkbox("Enable more options")
    if more_options:
        st.subheader("Additional filters")

        selected_vehicle_category = st.sidebar.multiselect("Filter by Vehicle Category", ["All"] + list(data['cat_vehicule_libelle'].unique()), default=["All"])
        selected_energy_type = st.sidebar.multiselect("Filter by Energy Type", ["All"] + list(data['cat_energie_libelle'].unique()), default=["All"])
        price_range = st.sidebar.slider("Filter by Price Range", float(data['prix_visite'].min()), float(data['prix_visite'].max()), (float(data['prix_visite'].min()), float(data['prix_visite'].max())))

        if "All" not in selected_vehicle_category:
            filtered_data = filtered_data[filtered_data['cat_vehicule_libelle'].isin(selected_vehicle_category)]

        if "All" not in selected_energy_type:
            filtered_data = filtered_data[filtered_data['cat_energie_libelle'].isin(selected_energy_type)]

        price_min, price_max = price_range
        filtered_data = filtered_data[(filtered_data['prix_visite'] >= price_min) & (filtered_data['prix_visite'] <= price_max)]


        # Check if the user selected the option to display each type of graph
        display_dept_distribution_chart = st.sidebar.checkbox("Display Department Distribution Chart")
        display_vehicle_category_chart = st.sidebar.checkbox("Display Vehicle Category Chart")
        display_energy_type_chart = st.sidebar.checkbox("Display Energy Type Chart")
        display_price_distribution_bar_chart = st.sidebar.checkbox("Display Selected Price Distribution Bar Chart")
        display_price_time_series_chart = st.sidebar.checkbox("Display Price Time Series Chart")

        # Create visualizations based on user selections and the filtered data
        if display_dept_distribution_chart:
            create_dept_distribution_chart(filtered_data)
        if display_vehicle_category_chart:
            create_category_energy_charts(filtered_data, 'cat_vehicule_libelle', 'Vehicle Categories')
        if display_energy_type_chart:
            create_category_energy_charts(filtered_data, 'cat_energie_libelle', 'Energy Types')
        if display_price_distribution_bar_chart:
            create_price_distribution_bar_chart(filtered_data)
        if display_price_time_series_chart:
            create_price_time_series_chart(filtered_data)
            # Calculate the minimum and maximum date values
            min_date = pd.to_datetime(filtered_data['date_application_visite'], format='mixed', errors='coerce').min()
            max_date = pd.to_datetime(filtered_data['date_application_visite'], format='mixed', errors='coerce').max()

            # Date range widgets
            st.subheader("Select a Time Frame:")
            start_date = st.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
            end_date = st.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)
            if start_date > end_date:
                st.error("Please select a valid date range.")
            else:
                if st.button("Show Price Variation"):
                    if filtered_data is not None:
                        create_price_time_period_chart(filtered_data, pd.to_datetime(start_date, format='mixed', errors='coerce'), pd.to_datetime(end_date, format='mixed', errors='coerce'))
                    
    if display_map or more_options:
        # Display the filtered data
        st.subheader("Filtered Inspection Centers")
        st.write("Here is the full list of all the inspection centers for your current filters.")
        st.write(filtered_data)
else:
    st.write("There is nothing loaded yet...")
    st.write("In this website you can explore a map to find the closest inspection center to you, you can check the address of the center as well as the price for inspection and re-inspection and even more information.")
    st.write("There are several options to use, and some are hidden, don't hesitate to explore this helpful tool.")

if st.sidebar.button("Refresh Data"):
    data = load_data()
