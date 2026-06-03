import pandas as pd
import streamlit as st

# Load your CSV
df = pd.read_csv("FA26_CASS_Classes.csv", skiprows=1)
df["Section Meet Begin Time"] = pd.to_numeric(df["Section Meet Begin Time"], errors="coerce")
df["Section Meet End Time"] = pd.to_numeric(df["Section Meet End Time"], errors="coerce")
df.columns = df.columns.str.strip()

# Map full day → schedule letters
day_map = {
    "Monday": "M",
    "Tuesday": "T",
    "Wednesday": "W",
    "Thursday": "R"
}

# Expand MW/TR into lists
def expand_days(schedule):
    if pd.isna(schedule) or str(schedule).strip() == "":
        return []
    return list(schedule)

df["Days_List"] = df["Section Meet Schedule"].apply(expand_days)

# Time of Day
def get_time_of_day(start_time):
    if pd.isna(start_time):
        return "Other"
    if 800 <= start_time <= 1159:
        return "Morning"
    elif 1200 <= start_time <= 1659:
        return "Afternoon"
    else:
        return "Evening"
        
df["TimeOfDay"] = df["Section Meet Begin Time"].apply(get_time_of_day)

# Modality 
def clean_modality(value):
    value = str(value).lower()

    if "face" in value:
        return "Face to Face"
    elif "hybrid" in value:
        return "Hybrid"
    elif "online" in value or "onln" in value:
        return "Online"
    else:
        return "Other"

df["Modality_Clean"] = df["Modality"].apply(clean_modality)

# ACC Group Map
group_map = {

    # Arts & Media
    "ARTH": "Arts & Media",
    "ART": "Arts & Media",
    "DGME": "Arts & Media",
    "MUS.": "Arts & Media",

    # Business & Public Service
    "ECON": "Business & Public Service",
    
    # Health & Wellness
    "ADS": "Health & Wellness",

    # Language Arts & Social Science
    "ANTH": "Language Arts & Social Science",
    "ETHN": "Language Arts & Social Science",
    "GBST": "Language Arts & Social Science",
    "HIST": "Language Arts & Social Science",
    "PHIL": "Language Arts & Social Science",
    "POLS": "Language Arts & Social Science",
    "PSYC": "Language Arts & Social Science",
    "SOCI": "Language Arts & Social Science"
}

# Color Map
color_map = { 
    "Arts & Media": "#7D6AC8",    
    "Business & Public Service": "#f7e356",
    "Health & Wellness": "#f79256", 
    "Language Arts & Social Science": "#1d4e89", 
    "Other": "#7f7f7f"             
}

# Group Icons
group_icons = {
    "Arts & Media": "🎨",
    "Business & Public Service": "📈",
    "Health & Wellness": "🧡",
    "Language Arts & Social Science": "📘",
    "Other": "⚪"
}

timeofday_icons = {
    "Morning": "🌅",
    "Afternoon": "☀️",
    "Evening": "🌙"
}

modality_icons = {
    "Face to Face": "🏫",
    "Hybrid": "🧑‍💻",
    "Online": "🖥️"
}

# Extract building number (everything before '-')
df["Building"] = (
    df["Section Building Code"]
    .astype(str)
    .str.split("-").str[0]
    .replace({"0": "Unknown", "UNKN": "Unknown"})
)

# Extract prefix from "DGME-100-AA"
def get_prefix(course):
    return course.split("-")[0]

# Extract prefix
df["Prefix"] = df["Course"].apply(get_prefix)

# Assign group
df["Group"] = df["Prefix"].map(group_map).fillna("Other")

# UI
st.title("FA26 CASS Class Finder")

# Day Select
day_input = st.selectbox("Select Day", list(day_map.keys()))
time_input = st.number_input("Enter Time (HHMM)", value=900)

selected_day_letter = day_map[day_input]

st.caption("Use 24-hour time input without a colon. For example, if you're looking for a 2:10 pm class, type 1410.")

# ACC Filter (MULTI-SELECT)
group_input = st.multiselect(
    "Filter by ACC",
    ["Arts & Media", "Business & Public Service", "Health & Wellness", "Language Arts & Social Science", "Other"]
)
st.caption("Select one or more categories. Leave blank to show all.")

modality_input = st.multiselect(
    "Filter by Modality",
    ["Face to Face", "Hybrid", "Online", "Other"]
)

time_input_filter = st.multiselect(
    "Filter by Time of Day",
    ["Morning", "Afternoon", "Evening", "Other"]
)

# Filtering
results = df[
    df["Days_List"].apply(lambda days: selected_day_letter in days)
    & (df["Section Meet Begin Time"] <= time_input)
    & (df["Section Meet End Time"] >= time_input)
]

# ACC filter
if len(group_input) > 0:
    results = results[results["Group"].isin(group_input)]

# Modality Filter
if len(modality_input) > 0:
    results = results[results["Modality_Clean"].isin(modality_input)]

# Time of Day Filter
if len(time_input_filter) > 0:
    results = results[results["TimeOfDay"].isin(time_input_filter)]

# Sort results by time
results = results.sort_values(by="Section Meet Begin Time")

# Display results
st.subheader("Classes Happening Now")

if results.empty:
    st.write("No classes found.")
else:
    for _, row in results.iterrows():
        group = row["Group"]
        color = color_map.get(group, "#333333")
        icon = group_icons.get(group, "⚪")
        modality_icon = modality_icons.get(row["Modality_Clean"], "")
        timeofday_icon = timeofday_icons.get(row["TimeOfDay"], "")


        st.markdown(f"""
        <div style="
            border-left: 8px solid {color};
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
            background-color: {color}22;
        ">
            <h4 style="color:{color}; margin-bottom:5px;">
                {icon} {row['Course']} – {row['Title']}
            </h4>
            <b>CRN:</b> {row['CRN']} <b>Modality:</b> {modality_icon} {row.get('Modality_Clean', 'N/A')}<br>
            <b>Time of Day:</b> {timeofday_icon} {row.get('TimeOfDay', 'N/A')}<br>
            <b>Category:</b> {group}<br>
            <b>Instructor:</b> {row['Instructor']}<br>
            <b>Email:</b> <a href="mailto:{row['Instructor Email']}">{row['Instructor Email']}</a><br>
            <b>Location:</b> Bldg {row['Building']}, Room {row['Room']}<br>
            <b>Time:</b> {row['Section Meet Begin Time']}–{row['Section Meet End Time']}<br>
            <b>Term Length:</b> {row.get('Term Length', 'N/A')}<br>
            <b>CalGETC Attribute:</b> {row.get('CalGETC Attribute', 'This course does not appear in any CalGETC areas. It may still satisfy a Local or CSU requirement.  For best results, check with your counselor.')}<br>
            <a href="{row.get('Class Hyperlink', '#')}" target="_blank">🔗 View Class Page</a>            
        </div>
        """, unsafe_allow_html=True)
