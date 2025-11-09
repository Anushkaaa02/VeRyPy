# my_project/app.py
import streamlit as st
import pandas as pd
from rules import assign_students_to_bus
from streamlit_folium import st_folium
import folium
from io import StringIO

# ---------- PAGE / THEME ----------
st.set_page_config(page_title="School Bus Allocation", layout="wide")

CUSTOM_CSS = """
<style>
    /* MAIN BACKGROUND */
    .stApp {
        background: linear-gradient(135deg, #A8C0FF 0%, #FFD6A5 100%);
        color: #1a1a1a !important;
        font-family: "Segoe UI", sans-serif;
    }

    /* HEADER */
    .main-header {
        text-align: center;
        font-size: 40px;
        font-weight: bold;
        padding: 10px;
        background: rgba(255, 255, 255, 0.45);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        color: #0A2463;
    }

    /* CARDS */
    .metric-card {
        background: rgba(255,255,255,.65);
        padding: 15px;
        border-radius: 14px;
        box-shadow: 0 3px 12px rgba(0,0,0,0.10);
        text-align: center;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] > div {
        background: rgba(255,255,255,0.55);
        backdrop-filter: blur(12px);
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.6);
        padding: 10px;
        border-radius: 12px;
        font-weight: 600;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center;'>🚌 Rule-Based School Bus Allocation (Interactive)</h1>", unsafe_allow_html=True)

# ---------- SIDEBAR: INPUTS ----------
st.sidebar.header("📥 Input Options")

mode = st.sidebar.radio("Provide student data via:", ["Upload CSV", "Enter Manually"])
st.sidebar.caption("CSV columns required: id, lat, lon (no headers = error).")

# sample CSV for users to copy
SAMPLE_CSV = "id,lat,lon\n1,28.7055,77.1012\n2,28.7061,77.1029\n3,28.7074,77.1031\n4,28.7089,77.1052\n5,28.7098,77.0994\n"

with st.sidebar.expander("📄 Sample CSV"):
    st.code(SAMPLE_CSV, language="text")

students = []

if mode == "Upload CSV":
    file = st.sidebar.file_uploader("Upload Student CSV", type=["csv"])
    if file:
        try:
            df_students = pd.read_csv(file)
            # validate columns
            req = {"id", "lat", "lon"}
            if not req.issubset({c.strip().lower() for c in df_students.columns}):
                st.sidebar.error("CSV must have columns: id, lat, lon")
            else:
                # normalize columns (lower-case)
                df_students.columns = [c.strip().lower() for c in df_students.columns]
                students = df_students[["id", "lat", "lon"]].to_dict(orient="records")
                st.sidebar.success("✅ CSV uploaded")
        except Exception as e:
            st.sidebar.error(f"CSV error: {e}")
else:
    st.sidebar.write("Enter student pickup coords:")
    count = st.sidebar.number_input("Number of students", 1, 200, 5)
    for i in range(count):
        with st.sidebar.expander(f"Student {i+1}", expanded=(i<3)):
            lat = st.number_input(f"Latitude {i+1}", value=28.7041 + (i*0.001), key=f"lat{i}")
            lon = st.number_input(f"Longitude {i+1}", value=77.1025 + (i*0.001), key=f"lon{i}")
            students.append({"id": i+1, "lat": float(lat), "lon": float(lon)})

st.sidebar.markdown("---")

# buses
bus_count = st.sidebar.number_input("Number of buses", 1, 20, 2)
buses = []
for i in range(bus_count):
    with st.sidebar.expander(f"Bus {i+1}", expanded=(i<2)):
        cap = st.number_input(f"Capacity (Bus {i+1})", 1, 100, 20, key=f"cap{i}")
        buses.append({"id": f"Bus-{i+1}", "capacity": int(cap)})

# school location (editable)
st.sidebar.markdown("---")
st.sidebar.subheader("🏫 School Location")
school_lat = st.sidebar.number_input("School Latitude", value=28.7041)
school_lon = st.sidebar.number_input("School Longitude", value=77.1025)
school = {"lat": float(school_lat), "lon": float(school_lon)}

# strategy
st.sidebar.markdown("---")
strategy = st.sidebar.selectbox("Allocation strategy", ["round_robin", "nearest_first"])

# ---------- TABS ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Dashboard", "👨‍🎓 Students", "🚌 Buses", "🗺 Map", "ℹ️ About"]
)

# ---------- TAB 1: DASHBOARD ----------
with tab1:
    st.subheader("📊 Allocation Result")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='metric-card'><h4>Total Students</h4><h2>{}</h2></div>".format(len(students)), unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='metric-card'><h4>Total Buses</h4><h2>{}</h2></div>".format(len(buses)), unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='metric-card'><h4>Strategy</h4><h2>{}</h2></div>".format(strategy.replace("_"," ").title()), unsafe_allow_html=True)

    run = st.button("🚦 Run Allocation")
    if run:
        results = assign_students_to_bus(buses, students, school=school, strategy=strategy)

        # format table
        formatted = []
        for bus_id, studs in results.items():
            formatted.append({
                "Bus ID": bus_id,
                "Students Assigned": len(studs),
                "Student IDs": ", ".join(str(s['id']) for s in studs)
            })
        st.write("")
        st.dataframe(pd.DataFrame(formatted), use_container_width=True)

        # unassigned (if any)
        assigned_ids = {s["id"] for lst in results.values() for s in lst}
        unassigned = [s for s in students if s["id"] not in assigned_ids]
        if unassigned:
            st.warning(f"Unassigned students (no capacity left): {[s['id'] for s in unassigned]}")
        else:
            st.success("All students assigned ✅")

# ---------- TAB 2: STUDENTS ----------
with tab2:
    st.subheader("👨‍🎓 Students")
    if students:
        st.dataframe(pd.DataFrame(students), use_container_width=True)
        st.caption("Tip: Use CSV upload for a larger list.")
    else:
        st.info("No student data yet. Upload CSV or add manually in the sidebar.")

# ---------- TAB 3: BUSES ----------
with tab3:
    st.subheader("🚌 Buses")
    if buses:
        st.dataframe(pd.DataFrame(buses), use_container_width=True)
    else:
        st.info("No buses defined.")

# ---------- TAB 4: MAP ----------
with tab4:
    st.subheader("🗺 Map View")
    if students:
        m = folium.Map(location=[school["lat"], school["lon"]], zoom_start=13, tiles="CartoDB positron")
        # school marker
        folium.Marker([school["lat"], school["lon"]], popup="🏫 School", icon=folium.Icon(color="red")).add_to(m)
        # student markers
        for s in students:
            folium.CircleMarker(
                [s["lat"], s["lon"]],
                radius=6, fill=True, fill_opacity=0.9, color="#2563eb",
                popup=f"Student {s['id']}"
            ).add_to(m)
        st_folium(m, width=1000, height=520)
    else:
        st.info("No students to plot.")

# ---------- TAB 5: ABOUT ----------
with tab5:
    st.subheader("ℹ️ About Project")
    st.markdown("""
This is a **Rule-Based School Bus Route Allocation** demo.

**Key features**
- CSV upload **and** manual entry
- Two allocation strategies:
  - **Round-robin** (balanced distribution)
  - **Nearest-first** (by distance to school)
- Map view for student locations
- Dark, modern UI

> Next improvements: real road distances, stop clustering, time windows.
""")
st.markdown("<div class='footer-note'>Made with ❤️ using Python + Streamlit</div>", unsafe_allow_html=True)
