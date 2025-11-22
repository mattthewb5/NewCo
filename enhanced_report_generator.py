"""
Enhanced Property Report Generator

Generates beautiful, interactive HTML reports combining:
- Location Quality Analysis
- Property Valuation
- Development Pressure Analysis
- Interactive maps (Leaflet.js)
- Charts (Chart.js)
- Mobile-responsive design

Author: NewCo Real Estate Intelligence
Date: November 2024
"""

import json
from typing import Dict, List, Optional
from datetime import datetime


class EnhancedReportGenerator:
    """Generates comprehensive property analysis reports"""

    def __init__(self):
        """Initialize report generator"""
        self.report_date = datetime.now().strftime("%B %d, %Y")

    def generate_comprehensive_report(
        self,
        property_data: Dict,
        valuation_result: Dict,
        location_result: Dict,
        development_result: Dict,
        output_path: str
    ) -> str:
        """
        Generate complete property report

        Args:
            property_data: Address, lat, lon, basic info
            valuation_result: From property_valuator.py
            location_result: From location_analyzer.py
            development_result: From development_pressure_analyzer.py
            output_path: Where to save HTML

        Returns:
            Path to generated report
        """
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            valuation_result, location_result, development_result
        )

        # Prepare chart data
        chart_data = self._prepare_chart_data(development_result)

        # Prepare map data
        map_data = self._prepare_map_data(
            property_data, valuation_result, development_result
        )

        # Render HTML template
        html = self._render_template(
            property_data=property_data,
            executive_summary=executive_summary,
            valuation=valuation_result,
            location=location_result,
            development=development_result,
            charts=chart_data,
            map_data=map_data
        )

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_path

    def _generate_executive_summary(self, valuation: Dict, location: Dict,
                                    development: Dict) -> Dict:
        """Generate executive summary"""
        # Extract key points
        value = valuation.get('estimated_value', 0)
        confidence = valuation.get('confidence_score', 0)
        location_score = location.get('quality_score', 0)
        location_rating = location.get('rating', 'Unknown')
        dev_score = development.get('pressure_score', 0)
        dev_class = development.get('classification', 'Unknown')

        # Build summary paragraph
        summary = f"This property is estimated at ${value:,} with {confidence}% confidence. "
        summary += f"The location quality is rated {location_rating} ({location_score}/10), "
        summary += f"with a {location.get('value_impact_pct', 0):+d}% value impact compared to similar properties. "
        summary += f"Development pressure in the area is {dev_class} ({dev_score}/100), "
        summary += self._pressure_interpretation(dev_score)

        # Collect strengths
        strengths = []
        if location_score >= 8:
            strengths.append(f"Excellent location quality ({location_score}/10)")
        if confidence >= 90:
            strengths.append(f"High valuation confidence ({confidence}%)")
        if dev_score < 40:
            strengths.append("Stable area with minimal development pressure")
        if location.get('value_impact_pct', 0) > 0:
            strengths.append(f"Location provides {location.get('value_impact_pct')}% value premium")

        # Collect concerns
        concerns = []
        if location.get('warnings'):
            # Take first 2-3 warnings
            concerns.extend([w.replace('⚠️ ', '') for w in location['warnings'][:3]])
        if dev_score > 70:
            concerns.append("High development activity in area may impact neighborhood character")

        if not concerns:
            concerns = ['No significant concerns identified']

        # Calculate overall rating
        overall_rating = self._calculate_overall_rating(location_score, confidence, dev_score)

        return {
            'summary': summary,
            'strengths': strengths,
            'concerns': concerns,
            'overall_rating': overall_rating
        }

    def _pressure_interpretation(self, score: float) -> str:
        """Interpret development pressure score"""
        if score < 20:
            return "indicating a very stable residential area."
        elif score < 40:
            return "indicating normal residential development activity."
        elif score < 60:
            return "indicating moderate growth and development."
        elif score < 75:
            return "indicating significant ongoing development."
        else:
            return "indicating very active development and growth."

    def _calculate_overall_rating(self, location_score: float, confidence: int,
                                  dev_score: float) -> str:
        """Calculate overall property rating"""
        # Weighted score
        # Location: 50%, Confidence: 30%, Development (inverse): 20%
        normalized_dev = (100 - dev_score) / 10  # Invert and normalize to 0-10

        overall = (location_score * 0.5 +
                  (confidence / 10) * 0.3 +
                  normalized_dev * 0.2)

        if overall >= 8.5:
            return "Excellent"
        elif overall >= 7.0:
            return "Very Good"
        elif overall >= 5.5:
            return "Good"
        elif overall >= 4.0:
            return "Fair"
        else:
            return "Caution"

    def _prepare_chart_data(self, development_result: Dict) -> Dict:
        """Prepare data for Chart.js"""
        components = development_result.get('components', {})

        return {
            'score_breakdown': {
                'labels': ['Rezoning', 'Permits', 'Land Sales', 'Appreciation', 'Proximity'],
                'data': [
                    components.get('rezoning_score', 0),
                    components.get('permit_score', 0),
                    components.get('land_sale_score', 0),
                    components.get('appreciation_score', 0),
                    components.get('proximity_score', 0)
                ],
                'weights': [30, 25, 20, 15, 10]
            },
            'activity_by_distance': self._prepare_activity_chart(development_result)
        }

    def _prepare_activity_chart(self, development_result: Dict) -> Dict:
        """Prepare activity by distance chart data"""
        zone_0_1 = development_result.get('zone_0_1', [])
        zone_1_3 = development_result.get('zone_1_3', [])
        zone_3_5 = development_result.get('zone_3_5', [])

        def count_by_type(activities, search_term):
            return len([a for a in activities if search_term in a.get('description', '')])

        return {
            'labels': ['0-1 mile', '1-3 miles', '3-5 miles'],
            'residential': [
                count_by_type(zone_0_1, 'Residential') + count_by_type(zone_0_1, 'Home'),
                count_by_type(zone_1_3, 'Residential') + count_by_type(zone_1_3, 'Home'),
                count_by_type(zone_3_5, 'Residential') + count_by_type(zone_3_5, 'Home')
            ],
            'commercial': [
                count_by_type(zone_0_1, 'Commercial') + count_by_type(zone_0_1, 'Data Center'),
                count_by_type(zone_1_3, 'Commercial') + count_by_type(zone_1_3, 'Data Center'),
                count_by_type(zone_3_5, 'Commercial') + count_by_type(zone_3_5, 'Data Center')
            ]
        }

    def _prepare_map_data(self, property_data: Dict, valuation_result: Dict,
                         development_result: Dict) -> Dict:
        """Prepare map markers and configuration"""
        markers = []

        # Subject property
        markers.append({
            'lat': property_data['lat'],
            'lng': property_data['lon'],
            'type': 'subject',
            'title': 'Subject Property',
            'popup': f"<b>Subject Property</b><br>{property_data['address']}"
        })

        # Comparable sales
        if 'comparables' in valuation_result:
            for i, comp in enumerate(valuation_result['comparables'][:5], 1):
                markers.append({
                    'lat': comp.get('lat'),
                    'lng': comp.get('lon'),
                    'type': 'comparable',
                    'title': f"Comp #{i}",
                    'popup': f"<b>Comp Sale #{i}</b><br>{comp.get('address')}<br>Sold: ${comp.get('sale_price', 0):,}<br>{comp.get('sale_date')}"
                })

        # Development activities
        all_activities = (development_result.get('zone_0_1', [])[:10] +
                         development_result.get('zone_1_3', [])[:10])

        for activity in all_activities:
            markers.append({
                'lat': activity.get('lat'),
                'lng': activity.get('lon'),
                'type': 'development',
                'title': activity.get('type', 'Development'),
                'popup': f"<b>{activity.get('type')}</b><br>{activity.get('description')}<br>{activity.get('address')}<br>Distance: {activity.get('distance')} mi"
            })

        return {
            'center': {'lat': property_data['lat'], 'lng': property_data['lon']},
            'zoom': 13,
            'markers': markers
        }

    def _render_template(self, property_data: Dict, executive_summary: Dict,
                        valuation: Dict, location: Dict, development: Dict,
                        charts: Dict, map_data: Dict) -> str:
        """Render complete HTML template"""
        address = property_data.get('address', 'Property')

        # Convert data to JSON for JavaScript
        chart_data_json = json.dumps(charts)
        map_data_json = json.dumps(map_data)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Property Analysis - {address}</title>

    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f7fa;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        /* Hero Section */
        .hero {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 20px;
            text-align: center;
            margin-bottom: 40px;
        }}

        .hero h1 {{
            font-size: 2.5em;
            margin-bottom: 20px;
            font-weight: 700;
        }}

        .key-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
            max-width: 1000px;
            margin-left: auto;
            margin-right: auto;
        }}

        .metric-card {{
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
        }}

        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}

        .metric-value {{
            font-size: 2em;
            font-weight: bold;
        }}

        /* Sections */
        .section {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .section h2 {{
            color: #1e40af;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        .section h3 {{
            color: #374151;
            margin-top: 25px;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}

        /* Executive Summary */
        .executive-summary {{
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        }}

        .overall-rating {{
            display: inline-block;
            padding: 10px 30px;
            border-radius: 25px;
            font-size: 1.2em;
            font-weight: bold;
            margin: 20px 0;
        }}

        .rating-excellent {{ background: #10b981; color: white; }}
        .rating-very-good {{ background: #3b82f6; color: white; }}
        .rating-good {{ background: #8b5cf6; color: white; }}
        .rating-fair {{ background: #f59e0b; color: white; }}
        .rating-caution {{ background: #ef4444; color: white; }}

        .strength-list, .concern-list {{
            list-style: none;
            margin: 15px 0;
        }}

        .strength-list li {{
            padding: 10px;
            margin: 8px 0;
            background: #d1fae5;
            border-left: 4px solid #10b981;
            border-radius: 5px;
        }}

        .concern-list li {{
            padding: 10px;
            margin: 8px 0;
            background: #fee2e2;
            border-left: 4px solid #ef4444;
            border-radius: 5px;
        }}

        /* Score Display */
        .score-display {{
            text-align: center;
            margin: 30px 0;
        }}

        .score-circle {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 3em;
            font-weight: bold;
            margin: 20px;
            color: white;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}

        .score-excellent {{ background: linear-gradient(135deg, #10b981, #059669); }}
        .score-very-good {{ background: linear-gradient(135deg, #3b82f6, #2563eb); }}
        .score-good {{ background: linear-gradient(135deg, #8b5cf6, #7c3aed); }}
        .score-fair {{ background: linear-gradient(135deg, #f59e0b, #d97706); }}
        .score-poor {{ background: linear-gradient(135deg, #ef4444, #dc2626); }}

        .rating-badge {{
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin: 10px;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}

        th {{
            background-color: #f3f4f6;
            font-weight: 600;
            color: #374151;
        }}

        tr:hover {{
            background-color: #f9fafb;
        }}

        /* Map */
        #map {{
            height: 500px;
            border-radius: 10px;
            margin: 20px 0;
        }}

        /* Charts */
        .chart-container {{
            position: relative;
            height: 300px;
            margin: 30px 0;
        }}

        /* Grid Layouts */
        .two-column {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        /* Warning/Positive Items */
        .warning-item, .positive-item {{
            padding: 12px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid;
        }}

        .warning-item {{
            background: #fef3c7;
            border-color: #f59e0b;
        }}

        .positive-item {{
            background: #d1fae5;
            border-color: #10b981;
        }}

        /* Footer */
        .report-footer {{
            text-align: center;
            padding: 40px 20px;
            color: #6b7280;
            font-size: 0.9em;
        }}

        /* Print Styles */
        @media print {{
            .hero {{
                background: #667eea !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .section {{
                page-break-inside: avoid;
            }}
        }}

        /* Mobile Responsive */
        @media (max-width: 768px) {{
            .hero h1 {{
                font-size: 1.8em;
            }}
            .key-metrics {{
                grid-template-columns: 1fr;
            }}
            .section {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>

    <!-- Hero Section -->
    <div class="hero">
        <h1>🏠 {address}</h1>
        <div class="key-metrics">
            <div class="metric-card">
                <div class="metric-label">Estimated Value</div>
                <div class="metric-value">${valuation.get('estimated_value', 0):,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Location Quality</div>
                <div class="metric-value">{location.get('quality_score', 0)}/10</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Development Pressure</div>
                <div class="metric-value">{development.get('pressure_score', 0)}/100</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Confidence</div>
                <div class="metric-value">{valuation.get('confidence_level', 'N/A')}</div>
            </div>
        </div>
    </div>

    <div class="container">

        <!-- Executive Summary -->
        <div class="section executive-summary">
            <h2>📋 Executive Summary</h2>
            <div class="overall-rating rating-{executive_summary['overall_rating'].lower().replace(' ', '-')}">
                Overall Rating: {executive_summary['overall_rating']}
            </div>

            <p style="font-size: 1.1em; line-height: 1.8; margin: 20px 0;">
                {executive_summary['summary']}
            </p>

            <h3>✅ Key Strengths</h3>
            <ul class="strength-list">
                {self._list_items(executive_summary['strengths'])}
            </ul>

            <h3>⚠️ Important Considerations</h3>
            <ul class="concern-list">
                {self._list_items(executive_summary['concerns'])}
            </ul>
        </div>

        <!-- Location Quality Analysis -->
        <div class="section">
            <h2>📍 Location Quality Analysis</h2>

            <div class="score-display">
                <div class="score-circle score-{self._get_score_class(location.get('quality_score', 0))}">
                    {location.get('quality_score', 0)}
                </div>
                <div>
                    <span class="rating-badge score-{self._get_score_class(location.get('quality_score', 0))}">
                        {location.get('rating', 'N/A')}
                    </span>
                </div>
                <div style="margin-top: 15px; font-size: 1.2em;">
                    <strong>Value Impact:</strong>
                    <span style="color: {'#10b981' if location.get('value_impact_pct', 0) > 0 else '#ef4444'};">
                        {location.get('value_impact_pct', 0):+d}%
                    </span>
                    vs comparable properties
                </div>
            </div>

            <h3>Overall Assessment</h3>
            <p style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 15px 0;">
                {location.get('overall_assessment', 'No assessment available')}
            </p>

            <h3>🚨 Location Warnings</h3>
            {self._render_location_warnings(location.get('warnings', []))}

            <h3>✅ Location Positives</h3>
            {self._render_location_positives(location.get('positives', []))}

            <div class="two-column">
                <div>
                    <h3>🛣️ Highway Proximity</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Highway</th>
                                <th>Distance</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._render_distance_table(location.get('highway_distances', {}))}
                        </tbody>
                    </table>
                </div>

                <div>
                    <h3>🚇 Metro Stations</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Station</th>
                                <th>Distance</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._render_distance_table(location.get('metro_distances', {}))}
                        </tbody>
                    </table>
                </div>
            </div>

            <h3>🛤️ Road Classification</h3>
            <p style="background: #e0f2fe; padding: 15px; border-radius: 8px; font-weight: 500;">
                {location.get('road_classification', 'Unknown')}
            </p>
        </div>

        <!-- Property Valuation -->
        <div class="section">
            <h2>💰 Property Valuation</h2>

            <div style="text-align: center; margin: 30px 0;">
                <div style="font-size: 3em; font-weight: bold; color: #1e40af;">
                    ${valuation.get('estimated_value', 0):,}
                </div>
                <div style="font-size: 1.2em; color: #6b7280; margin-top: 10px;">
                    Range: ${valuation.get('valuation_range', {}).get('low', 0):,} -
                    ${valuation.get('valuation_range', {}).get('high', 0):,}
                </div>
                <div style="margin-top: 15px;">
                    <span class="rating-badge score-{self._get_confidence_class(valuation.get('confidence_score', 0))}">
                        {valuation.get('confidence_level', 'N/A')} Confidence ({valuation.get('confidence_score', 0)}%)
                    </span>
                </div>
            </div>

            <h3>📊 Valuation Details</h3>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Price per Square Foot</td>
                    <td>${valuation.get('price_per_sqft', 0)}</td>
                </tr>
                <tr>
                    <td>Methodology</td>
                    <td>{valuation.get('methodology', 'N/A')}</td>
                </tr>
                <tr>
                    <td>Comparable Sales Used</td>
                    <td>{valuation.get('comp_count', 0)}</td>
                </tr>
                <tr>
                    <td>Analysis Date</td>
                    <td>{valuation.get('analysis_date', self.report_date)}</td>
                </tr>
            </table>

            <h3>🏘️ Comparable Sales (Top 5)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Address</th>
                        <th>Sale Price</th>
                        <th>Sqft</th>
                        <th>$/Sqft</th>
                        <th>Date</th>
                        <th>Distance</th>
                    </tr>
                </thead>
                <tbody>
                    {self._render_comparables_table(valuation.get('comparables', [])[:5])}
                </tbody>
            </table>
        </div>

        <!-- Development Context -->
        <div class="section">
            <h2>🏗️ Development Context</h2>

            <div class="score-display">
                <div class="score-circle score-{self._get_dev_score_class(development.get('pressure_score', 0))}">
                    {development.get('pressure_score', 0)}
                </div>
                <div>
                    <span class="rating-badge score-{self._get_dev_score_class(development.get('pressure_score', 0))}">
                        {development.get('classification', 'N/A')} Development Pressure
                    </span>
                </div>
            </div>

            <p style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                {development.get('interpretation', 'No interpretation available')}
            </p>

            <h3>📊 Component Breakdown</h3>
            <div class="chart-container">
                <canvas id="componentChart"></canvas>
            </div>

            <h3>📍 Activity by Distance</h3>
            <div class="chart-container">
                <canvas id="activityChart"></canvas>
            </div>

            <div class="two-column">
                <div>
                    <h4>Activity Count by Zone</h4>
                    <table>
                        <tr>
                            <td><strong>0-1 mile</strong></td>
                            <td>{development.get('activity_counts', {}).get('zone_0_1_miles', 0)} activities</td>
                        </tr>
                        <tr>
                            <td><strong>1-3 miles</strong></td>
                            <td>{development.get('activity_counts', {}).get('zone_1_3_miles', 0)} activities</td>
                        </tr>
                        <tr>
                            <td><strong>3-5 miles</strong></td>
                            <td>{development.get('activity_counts', {}).get('zone_3_5_miles', 0)} activities</td>
                        </tr>
                    </table>
                </div>

                <div>
                    <h4>Component Weights</h4>
                    <table>
                        {self._render_component_weights_table(development.get('component_weights', {}))}
                    </table>
                </div>
            </div>

            <h3>🔨 Nearby Permits (0-1 mile)</h3>
            {self._render_permits_table(development.get('zone_0_1', [])[:5])}
        </div>

        <!-- Interactive Map -->
        <div class="section">
            <h2>🗺️ Interactive Map</h2>
            <div id="map"></div>
            <div style="margin-top: 15px; font-size: 0.9em; color: #6b7280;">
                <strong>Legend:</strong>
                🔴 Subject Property |
                🔵 Comparable Sales |
                🟡 Development Activity
            </div>
        </div>

        <!-- Report Footer -->
        <div class="report-footer">
            <p><strong>NewCo Real Estate Intelligence</strong></p>
            <p>Report Generated: {self.report_date}</p>
            <p style="margin-top: 15px; font-size: 0.85em;">
                This report is for informational purposes only and should not be considered as professional advice.
                Property values, location assessments, and development activity are estimates based on available data.
                Always consult with licensed real estate professionals for official valuations and investment decisions.
            </p>
        </div>

    </div>

    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

    <script>
        // Initialize Map
        const mapData = {map_data_json};
        const map = L.map('map').setView([mapData.center.lat, mapData.center.lng], mapData.zoom);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }}).addTo(map);

        // Add markers
        mapData.markers.forEach(marker => {{
            let iconColor = 'blue';
            if (marker.type === 'subject') iconColor = 'red';
            if (marker.type === 'development') iconColor = 'orange';

            const icon = L.divIcon({{
                className: 'custom-marker',
                html: `<div style="background-color: ${{iconColor}}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
                iconSize: [20, 20]
            }});

            L.marker([marker.lat, marker.lng], {{ icon: icon }})
                .bindPopup(marker.popup)
                .addTo(map);
        }});

        // Distance circles
        const center = [mapData.center.lat, mapData.center.lng];
        L.circle(center, {{ radius: 1609, color: '#90EE90', fillOpacity: 0.1 }}).addTo(map);
        L.circle(center, {{ radius: 4828, color: '#FFD700', fillOpacity: 0.05 }}).addTo(map);
        L.circle(center, {{ radius: 8047, color: '#87CEEB', fillOpacity: 0.03 }}).addTo(map);

        // Initialize Charts
        const chartData = {chart_data_json};

        // Component Breakdown Chart
        const componentCtx = document.getElementById('componentChart').getContext('2d');
        new Chart(componentCtx, {{
            type: 'doughnut',
            data: {{
                labels: chartData.score_breakdown.labels,
                datasets: [{{
                    data: chartData.score_breakdown.data,
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#4facfe',
                        '#43e97b'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }},
                    title: {{
                        display: true,
                        text: 'Development Pressure Components'
                    }}
                }}
            }}
        }});

        // Activity by Distance Chart
        const activityCtx = document.getElementById('activityChart').getContext('2d');
        new Chart(activityCtx, {{
            type: 'bar',
            data: {{
                labels: chartData.activity_by_distance.labels,
                datasets: [
                    {{
                        label: 'Residential',
                        data: chartData.activity_by_distance.residential,
                        backgroundColor: '#3b82f6'
                    }},
                    {{
                        label: 'Commercial',
                        data: chartData.activity_by_distance.commercial,
                        backgroundColor: '#f59e0b'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ stacked: true }},
                    y: {{ stacked: true, beginAtZero: true }}
                }},
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }},
                    title: {{
                        display: true,
                        text: 'Development Activity by Distance'
                    }}
                }}
            }}
        }});
    </script>

</body>
</html>
"""
        return html

    def _list_items(self, items: List[str]) -> str:
        """Render list items"""
        if not items:
            return "<li>None</li>"
        return "\n".join(f"<li>{item}</li>" for item in items)

    def _get_score_class(self, score: float) -> str:
        """Get CSS class for location score"""
        if score >= 8.5:
            return "excellent"
        elif score >= 7.0:
            return "very-good"
        elif score >= 5.5:
            return "good"
        elif score >= 4.0:
            return "fair"
        else:
            return "poor"

    def _get_confidence_class(self, confidence: int) -> str:
        """Get CSS class for confidence"""
        if confidence >= 90:
            return "excellent"
        elif confidence >= 75:
            return "very-good"
        elif confidence >= 60:
            return "good"
        else:
            return "fair"

    def _get_dev_score_class(self, score: float) -> str:
        """Get CSS class for development score (inverse logic)"""
        if score < 20:
            return "excellent"
        elif score < 40:
            return "very-good"
        elif score < 60:
            return "good"
        elif score < 75:
            return "fair"
        else:
            return "poor"

    def _render_location_warnings(self, warnings: List[str]) -> str:
        """Render location warnings"""
        if not warnings:
            return "<div class='positive-item'>No significant warnings</div>"

        html = ""
        for warning in warnings:
            html += f"<div class='warning-item'>{warning}</div>\n"
        return html

    def _render_location_positives(self, positives: List[str]) -> str:
        """Render location positives"""
        if not positives:
            return "<div class='warning-item'>No notable positive factors identified</div>"

        html = ""
        for positive in positives:
            html += f"<div class='positive-item'>{positive}</div>\n"
        return html

    def _render_distance_table(self, distances: Dict[str, float]) -> str:
        """Render distance table rows"""
        if not distances:
            return "<tr><td colspan='2'>No data available</td></tr>"

        html = ""
        for name, dist in sorted(distances.items(), key=lambda x: x[1]):
            html += f"<tr><td>{name}</td><td>{dist} miles</td></tr>\n"
        return html

    def _render_comparables_table(self, comps: List[Dict]) -> str:
        """Render comparables table"""
        if not comps:
            return "<tr><td colspan='6'>No comparables available</td></tr>"

        html = ""
        for comp in comps:
            html += f"""<tr>
                <td>{comp.get('address', 'N/A')}</td>
                <td>${comp.get('sale_price', 0):,}</td>
                <td>{comp.get('sqft', 0):,}</td>
                <td>${comp.get('price_per_sqft', 0)}</td>
                <td>{comp.get('sale_date', 'N/A')}</td>
                <td>{comp.get('distance', 0)} mi</td>
            </tr>\n"""
        return html

    def _render_component_weights_table(self, weights: Dict[str, int]) -> str:
        """Render component weights table"""
        if not weights:
            return "<tr><td colspan='2'>No data available</td></tr>"

        html = ""
        for component, weight in weights.items():
            html += f"<tr><td>{component.title()}</td><td>{weight}%</td></tr>\n"
        return html

    def _render_permits_table(self, permits: List[Dict]) -> str:
        """Render permits table"""
        if not permits:
            return "<p>No recent permits within 1 mile</p>"

        html = "<table><thead><tr><th>Type</th><th>Description</th><th>Address</th><th>Distance</th><th>Date</th></tr></thead><tbody>"
        for permit in permits:
            html += f"""<tr>
                <td>{permit.get('type', 'N/A')}</td>
                <td>{permit.get('description', 'N/A')}</td>
                <td>{permit.get('address', 'N/A')}</td>
                <td>{permit.get('distance', 0)} mi</td>
                <td>{permit.get('date', 'N/A')}</td>
            </tr>"""
        html += "</tbody></table>"
        return html


# Example usage
if __name__ == "__main__":
    print("Enhanced Report Generator module loaded successfully")
    print("Use generate_comprehensive_report() to create HTML reports")
