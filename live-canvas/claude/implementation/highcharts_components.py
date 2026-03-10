"""
Highcharts component builders for Live Canvas
Provides helper functions to create Highcharts charts as canvas components
"""

def hc_pie(title="", data=None, colors=None, component_id=None):
    """
    Create a Highcharts pie chart component

    Args:
        title: Chart title
        data: List of {"name": "Label", "y": value} dicts
        colors: Optional list of hex color strings
        component_id: Optional component ID for updates

    Returns:
        Component dict for canvas.render()
    """
    comp = {
        "type": "hc_pie",
        "title": title,
        "data": data or [],
    }
    if colors:
        comp["colors"] = colors
    if component_id:
        comp["id"] = component_id
    return comp


def hc_gauge(title="", value=0, bands=None, component_id=None):
    """
    Create a Highcharts gauge chart component

    Args:
        title: Chart title
        value: Current value (0-100)
        bands: Optional list of {"from": 0, "to": 60, "color": "#4CAF50"} dicts
               Default: green 0-60%, yellow 60-80%, red 80-100%
        component_id: Optional component ID for updates

    Returns:
        Component dict for canvas.render()
    """
    comp = {
        "type": "hc_gauge",
        "title": title,
        "value": value,
    }
    if bands:
        comp["bands"] = bands
    if component_id:
        comp["id"] = component_id
    return comp


def hc_line(title="", labels=None, series=None, y_axis_title="", component_id=None):
    """
    Create a Highcharts line chart component

    Args:
        title: Chart title
        labels: List of X-axis labels
        series: List of {"name": "Series Name", "data": [values]} dicts
        y_axis_title: Y-axis label
        component_id: Optional component ID for updates

    Returns:
        Component dict for canvas.render()
    """
    comp = {
        "type": "hc_line",
        "title": title,
        "labels": labels or [],
        "series": series or [],
        "yAxisTitle": y_axis_title,
    }
    if component_id:
        comp["id"] = component_id
    return comp


def hc_bar(title="", labels=None, series=None, y_axis_title="", component_id=None):
    """
    Create a Highcharts bar/column chart component

    Args:
        title: Chart title
        labels: List of X-axis labels
        series: List of {"name": "Series Name", "data": [values]} dicts
        y_axis_title: Y-axis label
        component_id: Optional component ID for updates

    Returns:
        Component dict for canvas.render()
    """
    comp = {
        "type": "hc_bar",
        "title": title,
        "labels": labels or [],
        "series": series or [],
        "yAxisTitle": y_axis_title,
    }
    if component_id:
        comp["id"] = component_id
    return comp


# Example usage (in homelab_check.py):
#
# from highcharts_components import hc_pie, hc_gauge
#
# c.render([
#     {"type": "heading", "level": 1, "text": "Dashboard"},
#     hc_pie("Memory", [{"name": "Used", "y": 60}, {"name": "Free", "y": 40}]),
#     hc_gauge("CPU", value=45),
#     hc_bar("Network", labels=["Jan", "Feb", "Mar"], series=[
#         {"name": "Download", "data": [100, 120, 110]},
#         {"name": "Upload", "data": [50, 60, 55]},
#     ]),
# ])
