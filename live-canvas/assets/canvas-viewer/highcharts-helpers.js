/**
 * highcharts-helpers.js — Highcharts wrappers for Live Canvas
 * Depends on: Highcharts (loaded via CDN before this file)
 */

const HC_PALETTE = [
  '#3ecf8e', '#f5c542', '#7fb5ff', '#ff8888',
  '#c084fc', '#34d399', '#fb923c', '#60a5fa',
];

const HC_DEFAULTS = {
  chart: {
    backgroundColor: 'transparent',
    style: { fontFamily: 'var(--font, sans-serif)' }
  },
  title: {
    style: { color: 'rgba(255,255,255,0.92)', fontSize: '16px' }
  },
  legend: {
    itemStyle: { color: 'rgba(255,255,255,0.7)' }
  },
  xAxis: {
    labels: { style: { color: 'rgba(255,255,255,0.45)' } },
    title: { style: { color: 'rgba(255,255,255,0.45)' } }
  },
  yAxis: {
    labels: { style: { color: 'rgba(255,255,255,0.45)' } },
    title: { style: { color: 'rgba(255,255,255,0.45)' } }
  },
  tooltip: {
    backgroundColor: 'rgba(15,20,35,0.95)',
    borderColor: 'rgba(255,255,255,0.12)',
    style: { color: 'rgba(255,255,255,0.9)' }
  },
  plotOptions: {
    series: {
      dataLabels: {
        style: { color: 'rgba(255,255,255,0.8)' }
      }
    }
  }
};

/**
 * Create a Highcharts pie chart
 * @param {HTMLElement} container - Container element
 * @param {Object} options - Chart options
 * @param {string} options.title - Chart title
 * @param {Array} options.data - Array of {name, y} objects
 * @param {Array} options.colors - Optional color array
 * @returns {Highcharts.Chart}
 */
function createHighchartsPie(container, options = {}) {
  if (typeof Highcharts === 'undefined') {
    console.warn('Highcharts not loaded yet');
    return null;
  }

  const colors = options.colors || HC_PALETTE;

  const chartConfig = {
    ...HC_DEFAULTS,
    chart: { ...HC_DEFAULTS.chart, type: 'pie' },
    title: { text: options.title || 'Pie Chart' },
    plotOptions: {
      pie: {
        dataLabels: {
          format: '<b>{point.name}</b>: {point.percentage:.1f}%',
          style: { color: 'rgba(255,255,255,0.9)' }
        }
      }
    },
    series: [{
      colorByPoint: true,
      data: options.data || [],
      colors: colors
    }]
  };

  return Highcharts.chart(container, chartConfig);
}

/**
 * Create a Highcharts gauge chart
 * @param {HTMLElement} container - Container element
 * @param {Object} options - Chart options
 * @param {string} options.title - Chart title
 * @param {number} options.value - Current value (0-100)
 * @param {Array} options.bands - Color bands [{from, to, color}]
 * @returns {Highcharts.Chart}
 */
function createHighchartsGauge(container, options = {}) {
  if (typeof Highcharts === 'undefined') {
    console.warn('Highcharts not loaded yet');
    return null;
  }

  const defaultBands = [
    { from: 0, to: 60, color: '#4CAF50' },    // Green
    { from: 60, to: 80, color: '#FFC107' },   // Yellow
    { from: 80, to: 100, color: '#F44336' }   // Red
  ];

  const bands = options.bands || defaultBands;

  const chartConfig = {
    ...HC_DEFAULTS,
    chart: { ...HC_DEFAULTS.chart, type: 'gauge' },
    pane: {
      startAngle: -90,
      endAngle: 89.9
    },
    title: { text: options.title || 'Gauge' },
    exporting: { enabled: false },
    plotOptions: {
      gauge: {
        dataLabels: {
          y: 25,
          borderWidth: 0,
          style: { fontSize: '20px', color: 'rgba(255,255,255,0.9)' }
        },
        dial: { radius: '85%' },
        pivot: { radius: '7%' }
      }
    },
    yAxis: {
      min: 0,
      max: 100,
      tickPixelInterval: 72,
      tickPosition: 'inside',
      tickColor: 'rgba(255,255,255,0.2)',
      tickLength: 20,
      labels: {
        distance: 20,
        style: { color: 'rgba(255,255,255,0.45)' }
      },
      plotBands: bands.map(b => ({
        from: b.from,
        to: b.to,
        color: b.color,
        thickness: 20
      }))
    },
    series: [{
      name: options.title || 'Value',
      data: [options.value || 0],
      tooltip: { valueSuffix: ' %' }
    }]
  };

  return Highcharts.chart(container, chartConfig);
}

/**
 * Create a Highcharts line chart
 * @param {HTMLElement} container - Container element
 * @param {Object} options - Chart options
 * @param {string} options.title - Chart title
 * @param {Array} options.labels - X-axis labels
 * @param {Array} options.series - Array of {name, data} objects
 * @returns {Highcharts.Chart}
 */
function createHighchartsLine(container, options = {}) {
  if (typeof Highcharts === 'undefined') {
    console.warn('Highcharts not loaded yet');
    return null;
  }

  const series = (options.series || []).map((s, i) => ({
    name: s.name || `Series ${i + 1}`,
    data: s.data || [],
    color: s.color || HC_PALETTE[i % HC_PALETTE.length]
  }));

  const chartConfig = {
    ...HC_DEFAULTS,
    chart: { ...HC_DEFAULTS.chart, type: 'line' },
    title: { text: options.title || 'Line Chart' },
    xAxis: {
      categories: options.labels || [],
      ...HC_DEFAULTS.xAxis
    },
    yAxis: {
      ...HC_DEFAULTS.yAxis,
      title: { text: options.yAxisTitle || '' }
    },
    plotOptions: {
      line: {
        dataLabels: { enabled: options.dataLabels !== false }
      }
    },
    series: series
  };

  return Highcharts.chart(container, chartConfig);
}

/**
 * Create a Highcharts bar chart
 * @param {HTMLElement} container - Container element
 * @param {Object} options - Chart options
 * @param {string} options.title - Chart title
 * @param {Array} options.labels - X-axis labels
 * @param {Array} options.series - Array of {name, data} objects
 * @returns {Highcharts.Chart}
 */
function createHighchartsBar(container, options = {}) {
  if (typeof Highcharts === 'undefined') {
    console.warn('Highcharts not loaded yet');
    return null;
  }

  const series = (options.series || []).map((s, i) => ({
    name: s.name || `Series ${i + 1}`,
    data: s.data || [],
    color: s.color || HC_PALETTE[i % HC_PALETTE.length]
  }));

  const chartConfig = {
    ...HC_DEFAULTS,
    chart: { ...HC_DEFAULTS.chart, type: 'column' },
    title: { text: options.title || 'Bar Chart' },
    xAxis: {
      categories: options.labels || [],
      ...HC_DEFAULTS.xAxis
    },
    yAxis: {
      ...HC_DEFAULTS.yAxis,
      title: { text: options.yAxisTitle || '' }
    },
    plotOptions: {
      column: {
        dataLabels: { enabled: options.dataLabels !== false }
      }
    },
    series: series
  };

  return Highcharts.chart(container, chartConfig);
}
