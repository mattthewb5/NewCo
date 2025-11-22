#!/usr/bin/env python3
"""
Development Analysis Report Generator

Generates beautiful, comprehensive HTML reports combining development pressure
analysis with interactive maps and detailed activity breakdowns.

Author: Property Valuation System
Version: 1.0.0
Date: November 2025
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

from development_pressure_analyzer import DevelopmentPressureAnalyzer
from map_generator import MapGenerator
from location_analyzer import LocationQualityAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DevelopmentReportGenerator:
    """Generate comprehensive development analysis reports."""

    def __init__(
        self,
        dev_db_path: str = "loudoun_development.db",
        sales_db_path: str = "../loudoun_sales_clean.db"
    ):
        """
        Initialize report generator.

        Args:
            dev_db_path: Development database path
            sales_db_path: Sales database path (for property appreciation)
        """
        self.dev_db_path = dev_db_path
        self.sales_db_path = sales_db_path
        self.analyzer = DevelopmentPressureAnalyzer(dev_db_path)
        self.map_generator = MapGenerator(dev_db_path)
        self.location_analyzer = LocationQualityAnalyzer(dev_db_path)

    def generate_report(
        self,
        subject_lat: float,
        subject_lon: float,
        subject_address: str,
        output_path: str = "development_analysis_report.html"
    ) -> str:
        """
        Generate comprehensive development analysis report.

        Args:
            subject_lat: Subject property latitude
            subject_lon: Subject property longitude
            subject_address: Subject property address
            output_path: Output HTML file path

        Returns:
            Path to generated report
        """
        logger.info(f"Generating development analysis report for: {subject_address}")

        # Get development pressure analysis
        pressure_result = self.analyzer.calculate_development_pressure(
            subject_lat, subject_lon
        )

        # Get location quality analysis (NEW - Phase 2!)
        location_result = self.location_analyzer.analyze_location(
            subject_lat, subject_lon, subject_address
        )

        # Create map data
        map_data = self.map_generator.create_map_data(
            subject_lat, subject_lon, subject_address
        )

        # Generate HTML report
        html = self._build_html_report(pressure_result, location_result, map_data, subject_address)

        # Write to file
        with open(output_path, 'w') as f:
            f.write(html)

        logger.info(f"✓ Report saved to: {output_path}")

        return output_path

    def _build_html_report(
        self,
        pressure_result: Dict,
        location_result: Dict,
        map_data: Dict,
        subject_address: str
    ) -> str:
        """Build complete HTML report with location analysis (Phase 2)."""

        # Convert map data to JSON
        map_data_json = json.dumps(map_data, indent=2)

        # Get score details
        total_score = pressure_result['total_score']
        classification = pressure_result['classification']
        components = pressure_result['components']
        details = pressure_result['details']

        # Determine score color
        score_color = self._get_score_color(total_score)

        # Build activity tables
        rezoning_table = self._build_rezoning_table(details['rezonings'])
        permit_table = self._build_permit_table(details['permits'])
        sales_table = self._build_land_sales_table(details['land_sales'])

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Development Analysis Report - {subject_address}</title>

    <!-- Leaflet.js CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}

        /* Header */
        .report-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .report-header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .report-header .address {{
            font-size: 18px;
            opacity: 0.9;
            margin-bottom: 5px;
        }}

        .report-header .generated {{
            font-size: 14px;
            opacity: 0.7;
        }}

        /* Main Content */
        .content {{
            padding: 40px;
        }}

        /* Score Card */
        .score-card {{
            background: linear-gradient(135deg, {score_color}80 0%, {score_color}40 100%);
            border: 3px solid {score_color};
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}

        .score-card .score-label {{
            font-size: 16px;
            color: #555;
            margin-bottom: 10px;
            font-weight: 500;
        }}

        .score-card .score-value {{
            font-size: 72px;
            font-weight: bold;
            color: {score_color};
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}

        .score-card .score-classification {{
            font-size: 24px;
            color: {score_color};
            font-weight: 600;
            margin-bottom: 15px;
        }}

        .score-card .score-description {{
            font-size: 14px;
            color: #666;
            max-width: 600px;
            margin: 0 auto;
        }}

        /* Component Scores */
        .components-section {{
            margin-bottom: 40px;
        }}

        .section-title {{
            font-size: 24px;
            color: #333;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            font-weight: 600;
        }}

        .component-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .component-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .component-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }}

        .component-card .component-name {{
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
            font-weight: 500;
        }}

        .component-card .component-score {{
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .component-card .component-weight {{
            font-size: 12px;
            color: #999;
        }}

        /* Map Section */
        .map-section {{
            margin-bottom: 40px;
        }}

        #map {{
            height: 600px;
            width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}

        /* Activity Details */
        .activity-section {{
            margin-bottom: 40px;
        }}

        .activity-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}

        .activity-tab {{
            padding: 12px 24px;
            background: #f0f0f0;
            border: none;
            border-radius: 8px 8px 0 0;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
        }}

        .activity-tab:hover {{
            background: #e0e0e0;
        }}

        .activity-tab.active {{
            background: #667eea;
            color: white;
        }}

        .activity-content {{
            display: none;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 0 8px 8px 8px;
        }}

        .activity-content.active {{
            display: block;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 500;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}

        tr:hover {{
            background: #f5f5f5;
        }}

        .distance-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }}

        .distance-close {{
            background: #90EE90;
            color: #006400;
        }}

        .distance-medium {{
            background: #FFD700;
            color: #8B6914;
        }}

        .distance-far {{
            background: #87CEEB;
            color: #00008B;
        }}

        /* Chart Section */
        .chart-section {{
            margin-bottom: 40px;
        }}

        .chart-container {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            max-width: 600px;
            margin: 0 auto;
        }}

        /* Footer */
        .report-footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}

        .no-data {{
            text-align: center;
            padding: 40px;
            color: #999;
            font-style: italic;
        }}

        /* Legend */
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
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="report-header">
            <h1>Development Analysis Report</h1>
            <div class="address">{subject_address}</div>
            <div class="generated">Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</div>
        </div>

        <!-- Main Content -->
        <div class="content">
            <!-- Development Pressure Score -->
            <div class="score-card">
                <div class="score-label">Development Pressure Score</div>
                <div class="score-value">{total_score:.1f}</div>
                <div class="score-classification">{classification}</div>
                <div class="score-description">
                    {self._get_classification_description(classification)}
                </div>
            </div>

            <!-- Component Scores -->
            <div class="components-section">
                <h2 class="section-title">Score Breakdown</h2>
                <div class="component-grid">
                    <div class="component-card">
                        <div class="component-name">Rezoning Activity</div>
                        <div class="component-score">{components['rezoning_score']:.1f}</div>
                        <div class="component-weight">Weight: 30%</div>
                    </div>
                    <div class="component-card">
                        <div class="component-name">Building Permits</div>
                        <div class="component-score">{components['permit_score']:.1f}</div>
                        <div class="component-weight">Weight: 25%</div>
                    </div>
                    <div class="component-card">
                        <div class="component-name">Land Sales</div>
                        <div class="component-score">{components['land_sale_score']:.1f}</div>
                        <div class="component-weight">Weight: 20%</div>
                    </div>
                    <div class="component-card">
                        <div class="component-name">Property Appreciation</div>
                        <div class="component-score">{components['appreciation_score']:.1f}</div>
                        <div class="component-weight">Weight: 15%</div>
                    </div>
                    <div class="component-card">
                        <div class="component-name">Infrastructure Proximity</div>
                        <div class="component-score">{components['proximity_score']:.1f}</div>
                        <div class="component-weight">Weight: 10%</div>
                    </div>
                </div>
            </div>

            <!-- Score Visualization Chart -->
            <div class="chart-section">
                <h2 class="section-title">Visual Score Analysis</h2>
                <div class="chart-container">
                    <canvas id="scoreChart"></canvas>
                </div>
            </div>

            <!-- Interactive Map -->
            <div class="map-section">
                <h2 class="section-title">Development Activity Map</h2>
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
            </div>

            <!-- Activity Details -->
            <div class="activity-section">
                <h2 class="section-title">Detailed Activity Analysis</h2>
                <div class="activity-tabs">
                    <button class="activity-tab active" onclick="showTab('rezonings')">
                        Rezonings ({len(details['rezonings'])})
                    </button>
                    <button class="activity-tab" onclick="showTab('permits')">
                        Building Permits ({len(details['permits'])})
                    </button>
                    <button class="activity-tab" onclick="showTab('sales')">
                        Large Parcel Sales ({len(details['land_sales'])})
                    </button>
                </div>

                <div id="rezonings-content" class="activity-content active">
                    {rezoning_table}
                </div>

                <div id="permits-content" class="activity-content">
                    {permit_table}
                </div>

                <div id="sales-content" class="activity-content">
                    {sales_table}
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="report-footer">
            Loudoun County Development Analysis System | Generated by Property Valuation Platform<br>
            Data structures are Google Maps API-ready for easy migration
        </div>
    </div>

    <!-- Leaflet.js -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <script>
        // Tab switching
        function showTab(tabName) {{
            // Hide all content
            document.querySelectorAll('.activity-content').forEach(content => {{
                content.classList.remove('active');
            }});

            // Deactivate all tabs
            document.querySelectorAll('.activity-tab').forEach(tab => {{
                tab.classList.remove('active');
            }});

            // Show selected content
            document.getElementById(tabName + '-content').classList.add('active');

            // Activate selected tab
            event.target.classList.add('active');
        }}

        // Score Chart
        const ctx = document.getElementById('scoreChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: ['Rezoning\\n(30%)', 'Permits\\n(25%)', 'Land Sales\\n(20%)', 'Appreciation\\n(15%)', 'Proximity\\n(10%)'],
                datasets: [{{
                    label: 'Component Score',
                    data: [
                        {components['rezoning_score']:.1f},
                        {components['permit_score']:.1f},
                        {components['land_sale_score']:.1f},
                        {components['appreciation_score']:.1f},
                        {components['proximity_score']:.1f}
                    ],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(118, 75, 162, 0.8)',
                        'rgba(102, 187, 106, 0.8)',
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(244, 67, 54, 0.8)'
                    ],
                    borderColor: [
                        'rgba(102, 126, 234, 1)',
                        'rgba(118, 75, 162, 1)',
                        'rgba(102, 187, 106, 1)',
                        'rgba(255, 193, 7, 1)',
                        'rgba(244, 67, 54, 1)'
                    ],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            callback: function(value) {{
                                return value + '/100';
                            }}
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    title: {{
                        display: true,
                        text: 'Development Pressure Components',
                        font: {{
                            size: 16,
                            weight: 'bold'
                        }}
                    }}
                }}
            }}
        }});

        // Interactive Map
        const mapData = {map_data_json};

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

        console.log('Report generated with', mapData.markers.length, 'markers');
    </script>
</body>
</html>"""

        return html

    def _get_score_color(self, score: float) -> str:
        """Get color based on score."""
        if score >= 70:
            return "#dc3545"  # Red - Very High
        elif score >= 50:
            return "#fd7e14"  # Orange - High
        elif score >= 30:
            return "#ffc107"  # Yellow - Medium
        elif score >= 10:
            return "#28a745"  # Green - Low
        else:
            return "#17a2b8"  # Cyan - Very Low

    def _get_classification_description(self, classification: str) -> str:
        """Get description for classification."""
        descriptions = {
            "Very High": "Significant development activity detected. High potential for neighborhood transformation and value appreciation.",
            "High": "Substantial development pressure. Notable construction and rezoning activity in the area.",
            "Medium": "Moderate development activity. Some new construction and land use changes occurring.",
            "Low": "Limited development pressure. Area shows stable, established character.",
            "Very Low": "Minimal development activity. Very stable neighborhood with little change."
        }
        return descriptions.get(classification, "Development pressure analysis complete.")

    def _build_rezoning_table(self, rezonings: List[Dict]) -> str:
        """Build HTML table for rezonings."""
        if not rezonings:
            return '<div class="no-data">No rezoning activity detected within 5 miles</div>'

        rows = []
        for r in rezonings:
            distance_class = self._get_distance_class(r['distance_miles'])
            rows.append(f"""
                <tr>
                    <td>{r['address']}</td>
                    <td>{r['previous_zoning']} → {r['new_zoning']}</td>
                    <td>{r['vote_result']}</td>
                    <td>{r['decision_date']}</td>
                    <td><span class="distance-badge {distance_class}">{r['distance_miles']:.2f} mi</span></td>
                </tr>
            """)

        return f"""
            <table>
                <thead>
                    <tr>
                        <th>Address</th>
                        <th>Zoning Change</th>
                        <th>Result</th>
                        <th>Date</th>
                        <th>Distance</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        """

    def _build_permit_table(self, permits: List[Dict]) -> str:
        """Build HTML table for permits."""
        if not permits:
            return '<div class="no-data">No building permits detected within 5 miles</div>'

        rows = []
        for p in permits:
            distance_class = self._get_distance_class(p['distance_miles'])
            rows.append(f"""
                <tr>
                    <td>{p['address']}</td>
                    <td>{p['project_type']}</td>
                    <td>{p['sqft']:,} sqft</td>
                    <td>${p['valuation']:,}</td>
                    <td>{p['status']}</td>
                    <td><span class="distance-badge {distance_class}">{p['distance_miles']:.2f} mi</span></td>
                </tr>
            """)

        return f"""
            <table>
                <thead>
                    <tr>
                        <th>Address</th>
                        <th>Type</th>
                        <th>Size</th>
                        <th>Valuation</th>
                        <th>Status</th>
                        <th>Distance</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        """

    def _build_land_sales_table(self, sales: List[Dict]) -> str:
        """Build HTML table for land sales."""
        if not sales:
            return '<div class="no-data">No large parcel sales detected within 5 miles</div>'

        rows = []
        for s in sales:
            distance_class = self._get_distance_class(s['distance_miles'])
            rows.append(f"""
                <tr>
                    <td>{s['address']}</td>
                    <td>{s['acreage']} acres</td>
                    <td>${s['sale_price']:,}</td>
                    <td>{s['buyer_type']}</td>
                    <td>{s['sale_date']}</td>
                    <td><span class="distance-badge {distance_class}">{s['distance_miles']:.2f} mi</span></td>
                </tr>
            """)

        return f"""
            <table>
                <thead>
                    <tr>
                        <th>Address</th>
                        <th>Size</th>
                        <th>Sale Price</th>
                        <th>Buyer</th>
                        <th>Date</th>
                        <th>Distance</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        """

    def _get_distance_class(self, distance: float) -> str:
        """Get CSS class for distance badge."""
        if distance <= 1.0:
            return "distance-close"
        elif distance <= 3.0:
            return "distance-medium"
        else:
            return "distance-far"


if __name__ == "__main__":
    print("\nDevelopment Analysis Report Generator Test")
    print("="*60)

    # Test property
    test_lat = 39.0437
    test_lon = -77.4875
    test_address = "43500 Cloister Pl, Ashburn, VA 20147"

    # Generate report
    generator = DevelopmentReportGenerator()
    output_path = generator.generate_report(
        test_lat,
        test_lon,
        test_address
    )

    print(f"\n✓ Report generated: {output_path}")
    print(f"\nOpen {output_path} in a browser to view the complete analysis!")
