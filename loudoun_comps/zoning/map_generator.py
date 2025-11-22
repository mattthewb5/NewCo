#!/usr/bin/env python3
"""
Interactive Map Generator (Google Maps API-Ready)

Generates interactive HTML maps using Leaflet.js with data structures designed
for seamless migration to Google Maps API.

CRITICAL: All data structures use Google Maps naming conventions (lat/lng).
Migration path documented for future Google Maps integration.

Author: Property Valuation System
Version: 1.0.0
Date: November 2025
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List
from geopy.distance import geodesic
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MapGenerator:
    """Generate Google Maps-ready interactive maps."""

    def __init__(self, dev_db_path: str = "loudoun_development.db"):
        """Initialize map generator."""
        self.dev_db_path = dev_db_path

    def create_map_data(
        self,
        subject_lat: float,
        subject_lon: float,
        subject_address: str,
        radius_miles: float = 5.0
    ) -> Dict:
        """
        Create Google Maps-compatible map data structure.

        Args:
            subject_lat: Subject property latitude
            subject_lon: Subject property longitude
            subject_address: Subject property address
            radius_miles: Search radius

        Returns:
            Google Maps-ready map data dictionary
        """
        logger.info("Generating Google Maps-ready map data...")

        # Initialize map data (Google Maps format)
        map_data = {
            "center": {"lat": subject_lat, "lng": subject_lon},  # Google Maps uses "lng"
            "zoom": 13,
            "markers": [],
            "circles": [],
            "polylines": [],
            "metadata": {
                "generated": datetime.now().isoformat(),
                "map_engine": "leaflet",
                "google_maps_ready": True,
                "migration_notes": "Structure compatible with Google Maps API. See migration guide."
            }
        }

        # Add subject property marker
        map_data["markers"].append({
            "id": "subject_001",
            "lat": subject_lat,
            "lng": subject_lon,
            "type": "subject_property",
            "icon": "red_home",
            "title": "Subject Property",
            "address": subject_address,
            "popup_html": f"<b>Subject Property</b><br>{subject_address}"
        })

        # Add distance circles
        for radius in [1, 3, 5]:
            color = "#90EE90" if radius == 1 else "#FFD700" if radius == 3 else "#87CEEB"
            map_data["circles"].append({
                "center": {"lat": subject_lat, "lng": subject_lon},
                "radius_miles": radius,
                "radius_meters": radius * 1609.34,  # For Leaflet
                "color": color,
                "fillColor": color,
                "opacity": 0.3 if radius == 1 else 0.2 if radius == 3 else 0.1,
                "fillOpacity": 0.1
            })

        # Add development markers
        self._add_permit_markers(map_data, subject_lat, subject_lon, radius_miles)
        self._add_rezoning_markers(map_data, subject_lat, subject_lon, radius_miles)
        self._add_land_sale_markers(map_data, subject_lat, subject_lon, radius_miles)

        logger.info(f"✓ Generated map with {len(map_data['markers'])} markers")

        return map_data

    def _add_permit_markers(
        self,
        map_data: Dict,
        subject_lat: float,
        subject_lon: float,
        radius_miles: float
    ):
        """Add building permit markers."""
        conn = sqlite3.connect(self.dev_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM building_permits")
        permits = cursor.fetchall()
        conn.close()

        for i, permit in enumerate(permits):
            distance = geodesic(
                (subject_lat, subject_lon),
                (permit['latitude'], permit['longitude'])
            ).miles

            if distance <= radius_miles:
                icon = "yellow_construction" if permit['project_type'] == 'Commercial' else "blue_construction"

                popup_html = f"""
                <b>{permit['project_type']} Development</b><br>
                {permit['address']}<br>
                Size: {permit['sqft']:,} sqft<br>
                Valuation: ${permit['valuation']:,}<br>
                Status: {permit['status']}<br>
                Distance: {distance:.2f} miles
                """

                map_data["markers"].append({
                    "id": f"permit_{permit['id']}",
                    "lat": permit['latitude'],
                    "lng": permit['longitude'],
                    "type": "commercial_permit" if permit['project_type'] == 'Commercial' else "residential_permit",
                    "icon": icon,
                    "title": f"{permit['project_type']}: {permit['address'][:30]}...",
                    "distance_miles": round(distance, 2),
                    "popup_html": popup_html.strip()
                })

    def _add_rezoning_markers(
        self,
        map_data: Dict,
        subject_lat: float,
        subject_lon: float,
        radius_miles: float
    ):
        """Add rezoning markers."""
        conn = sqlite3.connect(self.dev_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM rezonings")
        rezonings = cursor.fetchall()
        conn.close()

        for i, rezoning in enumerate(rezonings):
            distance = geodesic(
                (subject_lat, subject_lon),
                (rezoning['latitude'], rezoning['longitude'])
            ).miles

            if distance <= radius_miles:
                popup_html = f"""
                <b>Rezoning</b><br>
                {rezoning['address']}<br>
                {rezoning['previous_zoning']} → {rezoning['new_zoning']}<br>
                Result: {rezoning['vote_result']}<br>
                Date: {rezoning['decision_date']}<br>
                Distance: {distance:.2f} miles
                """

                map_data["markers"].append({
                    "id": f"rezoning_{rezoning['id']}",
                    "lat": rezoning['latitude'],
                    "lng": rezoning['longitude'],
                    "type": "rezoning",
                    "icon": "purple_zoning",
                    "title": f"Rezoning: {rezoning['address'][:30]}...",
                    "distance_miles": round(distance, 2),
                    "popup_html": popup_html.strip()
                })

    def _add_land_sale_markers(
        self,
        map_data: Dict,
        subject_lat: float,
        subject_lon: float,
        radius_miles: float
    ):
        """Add large parcel sale markers."""
        conn = sqlite3.connect(self.dev_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM large_parcel_sales")
        sales = cursor.fetchall()
        conn.close()

        for i, sale in enumerate(sales):
            distance = geodesic(
                (subject_lat, subject_lon),
                (sale['latitude'], sale['longitude'])
            ).miles

            if distance <= radius_miles:
                popup_html = f"""
                <b>Large Parcel Sale</b><br>
                {sale['address']}<br>
                {sale['acreage']} acres<br>
                Price: ${sale['sale_price']:,}<br>
                Buyer: {sale['buyer_type']}<br>
                Date: {sale['sale_date']}<br>
                Distance: {distance:.2f} miles
                """

                map_data["markers"].append({
                    "id": f"land_sale_{sale['id']}",
                    "lat": sale['latitude'],
                    "lng": sale['longitude'],
                    "type": "land_sale",
                    "icon": "green_land",
                    "title": f"Land Sale: {sale['address'][:30]}...",
                    "distance_miles": round(distance, 2),
                    "popup_html": popup_html.strip()
                })

    def generate_html_map(self, map_data: Dict, output_path: str = "development_map.html"):
        """
        Generate interactive HTML map using Leaflet.js.

        Args:
            map_data: Google Maps-ready map data
            output_path: Output HTML file path
        """
        logger.info("Generating interactive HTML map...")

        # Convert map_data to JSON
        map_data_json = json.dumps(map_data, indent=2)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Development Activity Map</title>

    <!-- Leaflet.js CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        #map {{
            height: 600px;
            width: 100%;
        }}
        .map-legend {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            font-size: 14px;
        }}
        .legend-item {{
            margin: 5px 0;
            display: flex;
            align-items: center;
        }}
        .legend-icon {{
            width: 20px;
            height: 20px;
            margin-right: 8px;
            text-align: center;
            font-size: 16px;
        }}
        .custom-marker {{
            font-size: 24px;
            text-align: center;
        }}

        /* Google Maps Migration Note */
        .migration-note {{
            background: #f0f8ff;
            border-left: 4px solid #2196F3;
            padding: 10px 15px;
            margin: 10px;
            font-size: 12px;
            color: #333;
        }}
    </style>
</head>
<body>
    <!-- Google Maps Migration Note -->
    <div class="migration-note">
        ℹ️ <b>Developer Note:</b> This map uses Leaflet.js with Google Maps-compatible data structures.
        To migrate to Google Maps API, see migration guide in code comments. Data format requires no changes!
    </div>

    <div id="map"></div>

    <div class="map-legend">
        <div style="font-weight: bold; margin-bottom: 10px;">Development Activity</div>
        <div class="legend-item">
            <span class="legend-icon">🏠</span>
            <span>Subject Property</span>
        </div>
        <div class="legend-item">
            <span class="legend-icon">🏗️</span>
            <span>Commercial Development</span>
        </div>
        <div class="legend-item">
            <span class="legend-icon">🏘️</span>
            <span>Residential Development</span>
        </div>
        <div class="legend-item">
            <span class="legend-icon">📋</span>
            <span>Rezoning</span>
        </div>
        <div class="legend-item">
            <span class="legend-icon">🌳</span>
            <span>Large Parcel Sale</span>
        </div>
        <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd;">
            <div style="font-size: 12px; color: #666;">
                🟢 0-1 mile | 🟡 1-3 miles | 🔵 3-5 miles
            </div>
        </div>
    </div>

    <!-- Leaflet.js JavaScript -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <script>
        /*
         * GOOGLE MAPS MIGRATION GUIDE
         * ==========================
         *
         * To migrate this map to Google Maps API:
         *
         * 1. Replace Leaflet script with Google Maps:
         *    <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY"></script>
         *
         * 2. Update map initialization:
         *    const map = new google.maps.Map(document.getElementById('map'), {{
         *      center: {{lat: mapData.center.lat, lng: mapData.center.lng}},
         *      zoom: mapData.center.zoom
         *    }});
         *
         * 3. Update markers (data structure already compatible!):
         *    mapData.markers.forEach(marker => {{
         *      new google.maps.Marker({{
         *        position: {{lat: marker.lat, lng: marker.lng}},
         *        map: map,
         *        title: marker.title
         *      }});
         *    }});
         *
         * 4. Update circles:
         *    mapData.circles.forEach(circle => {{
         *      new google.maps.Circle({{
         *        center: {{lat: circle.center.lat, lng: circle.center.lng}},
         *        radius: circle.radius_meters,
         *        map: map
         *      }});
         *    }});
         *
         * 5. NO CHANGES TO mapData JSON structure needed!
         */

        // Load Google Maps-ready data
        const mapData = {map_data_json};

        // Initialize Leaflet map (temporary, replace with Google Maps later)
        const map = L.map('map').setView(
            [mapData.center.lat, mapData.center.lng],
            mapData.zoom
        );

        // Add OpenStreetMap tiles
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }}).addTo(map);

        // Add distance circles
        mapData.circles.forEach(circle => {{
            L.circle([circle.center.lat, circle.center.lng], {{
                radius: circle.radius_meters,
                color: circle.color,
                fillColor: circle.fillColor,
                fillOpacity: circle.fillOpacity,
                weight: 2,
                opacity: circle.opacity
            }}).addTo(map);
        }});

        // Icon mapping
        const iconMap = {{
            'subject_property': '🏠',
            'commercial_permit': '🏗️',
            'residential_permit': '🏘️',
            'rezoning': '📋',
            'land_sale': '🌳'
        }};

        // Add markers
        mapData.markers.forEach(marker => {{
            const icon = L.divIcon({{
                html: iconMap[marker.type] || '📍',
                className: 'custom-marker',
                iconSize: [30, 30]
            }});

            L.marker([marker.lat, marker.lng], {{icon: icon}})
                .bindPopup(marker.popup_html)
                .addTo(map);
        }});

        console.log('Map generated with Google Maps-compatible data structure');
        console.log('Markers:', mapData.markers.length);
        console.log('Circles:', mapData.circles.length);
    </script>
</body>
</html>"""

        # Write HTML file
        with open(output_path, 'w') as f:
            f.write(html)

        logger.info(f"✓ Interactive map saved to: {output_path}")

        return output_path


if __name__ == "__main__":
    print("\nInteractive Map Generator Test (Google Maps-Ready)")
    print("="*60)

    generator = MapGenerator()

    # Test property
    test_lat = 39.0437
    test_lon = -77.4875
    test_address = "43500 Cloister Pl, Ashburn, VA 20147"

    # Create map data
    map_data = generator.create_map_data(test_lat, test_lon, test_address)

    print(f"\nMap Data Summary:")
    print(f"  Center: ({map_data['center']['lat']}, {map_data['center']['lng']})")
    print(f"  Markers: {len(map_data['markers'])}")
    print(f"  Circles: {len(map_data['circles'])}")
    print(f"  Google Maps Ready: {map_data['metadata']['google_maps_ready']}")

    # Generate HTML
    output_path = generator.generate_html_map(map_data)

    print(f"\n✓ Map generated: {output_path}")
    print(f"\nOpen {output_path} in a browser to view the interactive map!")
    print("\n✓ Data structure is Google Maps API-ready!")
