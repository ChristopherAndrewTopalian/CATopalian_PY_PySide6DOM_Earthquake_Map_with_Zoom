# CATopalian_PY_PySide6DOM_Earthquake_Map_with_Zoom.pyw

#import os
import urllib.request
#import json
from pyside6dom import *

my_icon = os.path.join("src", "media", "textures", "icons", "001.png")
init_window('CATopalian PY PySide6DOM Earthquake Map with Zoom', 1100, 850, my_icon)

set_theme('''
    body {
        background-color: rgb(20, 20, 25); 
        color: white;
        font-family: 'Segoe UI', Arial; 
        margin: 0px;
        padding: 0px;
    }
    .header_panel {
        background-color: rgb(15, 15, 20);
        padding: 10px;
        border-bottom: 2px solid #333;
    }
    .map_canvas {
        background-color: rgb(30, 35, 45);
    }
    .eq_dot {
        background-color: rgba(255, 50, 50, 0.7);
        border-radius: 5px;
    }
    .list_row {
        padding: 10px;
        border-bottom: 1px solid #444;
    }
    .list_row:hover {
        background-color: #333;
    }
    .mag_badge {
        background-color: #ff3333;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        margin-right: 10px;
    }
    button {
        padding: 5px 15px;
        margin-left: 20px;
        background-color: #444;
        color: white;
        font-weight: bold;
        border-radius: 4px;
        border: 1px solid #555;
    }
    button:hover {
        background-color: #555;
        border: 1px solid #00ffcc;
    }
    button:pressed {
        background-color: #222;
        border: 1px solid #ff3333;
    }
''')

# STATE VARIABLES
BASE_WIDTH = 1000
BASE_HEIGHT = 500
MAP_WIDTH = BASE_WIDTH
MAP_HEIGHT = BASE_HEIGHT

# We store references to the actual DOM elements here so we can just move them!
live_dots = [] 

live_rows = [] # Track the list rows so we can clear them!

# ===
# UI LAYOUT
# ===
header = ce('div')
header.className = 'header_panel'
header.style.display = 'flex'
header.style.flexDirection = 'row'
header.style.alignItems = 'center'
ba(header)

app_title = ce('h2')
app_title.textContent = "Earthquakes"
app_title.style.color = '#00ffcc'
app_title.style.marginRight = '20px'
header.append(app_title)

count_lbl = ce('h3')
count_lbl.id = 'count_lbl'
count_lbl.textContent = "Loading live data..."
count_lbl.style.color = '#ff3333'
count_lbl.style.marginRight = '40px'
header.append(count_lbl)

zoom_lbl = ce('text')
zoom_lbl.textContent = "Zoom: 1.0x"
zoom_lbl.style.fontWeight = 'bold'
zoom_lbl.style.marginRight = '2px'
header.append(zoom_lbl)

zoom_slider = ce('slider')
zoom_slider.style.width = '200px'
zoom_slider.raw.setMinimum(10) # 1.0x
zoom_slider.raw.setMaximum(50) # 5.0x
zoom_slider.value = 1.0
header.append(zoom_slider)

# The Refresh Button
update_btn = ce('button')
update_btn.textContent = "🔄 Refresh"
header.append(update_btn)

map_viewport = ce('scroll_div')
map_viewport.style.width = BASE_WIDTH
map_viewport.style.height = BASE_HEIGHT
map_viewport.style.borderBottom = '3px solid rgb(100, 100, 120)'
ba(map_viewport)

map_view = ce('div')
map_view.className = 'map_canvas'
map_view.style.width = MAP_WIDTH
map_view.style.height = MAP_HEIGHT
map_view.style.position = 'relative' 
map_viewport.append(map_view)

map_bg = ce('img')
map_bg.src = os.path.join("src", "media", "textures", "maps", "Earthmap1000x500.jpg")
map_bg.style.position = 'absolute'
map_bg.style.left = 0
map_bg.style.top = 0
map_bg.width = MAP_WIDTH
map_bg.height = MAP_HEIGHT
map_view.append(map_bg)

list_view = ce('scroll_div')
list_view.style.width = BASE_WIDTH
list_view.style.height = 300
list_view.style.padding = 10
ba(list_view)

# ===
# MATH & RENDERING LOGIC
# ===
def lat_lon_to_xy(lat, lon):
    x = (lon + 180.0) * (MAP_WIDTH / 360.0)
    y = (90.0 - lat) * (MAP_HEIGHT / 180.0)
    return x, y

def handle_zoom(val):
    global MAP_WIDTH, MAP_HEIGHT
    zoom_lbl.textContent = f"Zoom: {val:.1f}x"
    
    MAP_WIDTH = int(BASE_WIDTH * val)
    MAP_HEIGHT = int(BASE_HEIGHT * val)
    
    map_view.style.width = MAP_WIDTH
    map_view.style.height = MAP_HEIGHT
    map_bg.width = MAP_WIDTH
    map_bg.height = MAP_HEIGHT
    
    for item in live_dots:
        dot_element = item['dom_node']
        x, y = lat_lon_to_xy(item['lat'], item['lon'])
        
        # Calculate new exact position
        new_left = int(x) - 5
        new_top = int(y) - 5
        
        # THE ZOOM FIX: Store it on the dot so the hover function knows where it is!
        dot_element.base_x = new_left
        dot_element.base_y = new_top
        
        dot_element.style.left = new_left
        dot_element.style.top = new_top

zoom_slider.onchange = handle_zoom

####

def refresh_data():
    count_lbl.textContent = "Fetching fresh data..."

    # Destroy old elements from the C++ memory
    for item in live_dots:
        item['dom_node'].raw.deleteLater()
    for row in live_rows:
        row.raw.deleteLater()

    # Clear the Python tracking lists
    live_dots.clear()
    live_rows.clear()

    # Reload the map!
    load_earthquakes()

update_btn.onclick = refresh_data

# ===
# FETCH DATA (Runs ONLY Once!)
# ===
def load_earthquakes():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
    
    try:
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        features = data.get('features', [])
        
        count_lbl.textContent = f"Total Past 24h: {len(features)}"
        
        for eq in features:
            props = eq['properties']
            coords = eq['geometry']['coordinates'] 
            mag = props['mag']
            place = props['place']
            lon = coords[0]
            lat = coords[1]

            x, y = lat_lon_to_xy(lat, lon)
            dot = ce('div')
            dot.title = f"<b>{place}</b><br>Magnitude: {mag:.1f}"
            dot.titleFontSize = "16px"
            dot.className = 'eq_dot'
            dot.style.position = 'absolute'
            
            # Set the initial base positions
            dot.base_x = int(x) - 5
            dot.base_y = int(y) - 5
            dot.style.left = dot.base_x
            dot.style.top = dot.base_y
            
            size = max(6, int(mag * 2)) 
            dot.style.width = size
            dot.style.height = size
            
            dot.raw.setCursor(Qt.CursorShape.PointingHandCursor)
            def open_maps(lt=lat, ln=lon):
                QDesktopServices.openUrl(QUrl(f"https://www.google.com/maps/search/?api=1&query={lt},{ln}"))
            dot.onclick = open_maps
            
            map_view.append(dot)
            
            live_dots.append({
                'dom_node': dot,
                'lat': lat,
                'lon': lon
            })

            row = ce('div')
            row.className = 'list_row'
            row.style.display = 'flex'
            row.style.flexDirection = 'row'
            row.style.alignItems = 'center'
            row.raw.setCursor(Qt.CursorShape.PointingHandCursor)

            badge = ce('text')
            badge.className = 'mag_badge'
            badge.textContent = f"M {mag:.1f}"
            badge.raw.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) 
            row.append(badge)

            info = ce('text')
            info.textContent = place
            info.style.fontSize = '16px'
            info.raw.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) 
            row.append(info)
            row.onclick = open_maps
            list_view.append(row)
            # Track this row so the Refresh button can delete it later!
            live_rows.append(row)

            # ===
            # THE HOVER INTERACTIVITY
            # ===
            def hover_in(d=dot, r=row, s=size):
                d.style.backgroundColor = 'rgb(0, 255, 255)'
                d.style.width = s + 6
                d.style.height = s + 6
                # Safely use the dynamic base_x so zoom isn't broken!
                d.style.left = d.base_x - 3  
                d.style.top = d.base_y - 3
                d.style.border = '2px solid white'
                d.raw.raise_() 
                r.style.backgroundColor = '#444'

            def hover_out(d=dot, r=row, s=size):
                d.style.backgroundColor = 'rgba(255, 50, 50, 0.7)'
                d.style.width = s
                d.style.height = s
                # Snap back to current zoomed coordinates
                d.style.left = d.base_x
                d.style.top = d.base_y
                d.style.border = 'none'
                r.style.backgroundColor = 'transparent'

            row.addEventListener('mouseenter', hover_in)
            row.addEventListener('mouseleave', hover_out)
            dot.addEventListener('mouseenter', hover_in)
            dot.addEventListener('mouseleave', hover_out)

    except Exception as e:
        print(f"Failed to load earthquake data: {e}")

load_earthquakes()

run_app()

####

# Dedicated to God the Father
# (c) Copyright 2026 Christopher Andrew Topalian All Rights Reserved
# https://github.com/ChristopherTopalian
# https://github.com/ChristopherAndrewTopalian
# https://sites.google.com/view/CollegeOfScripting

