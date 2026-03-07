/**
 * chart-helpers.js — Chart.js wrappers for Live Canvas
 * Depends on: Chart.js (loaded via CDN before this file)
 */

const LC_CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: 'rgba(255,255,255,0.6)', font: { size: 12 }, boxWidth: 12 },
    },
    tooltip: {
      backgroundColor: 'rgba(15,20,35,0.95)',
      borderColor: 'rgba(255,255,255,0.12)',
      borderWidth: 1,
      titleColor: 'rgba(255,255,255,0.9)',
      bodyColor: 'rgba(255,255,255,0.7)',
      padding: 10,
    },
  },
  scales: {
    x: {
      ticks: { color: 'rgba(255,255,255,0.45)', font: { size: 11 } },
      grid:  { color: 'rgba(255,255,255,0.06)' },
    },
    y: {
      ticks: { color: 'rgba(255,255,255,0.45)', font: { size: 11 } },
      grid:  { color: 'rgba(255,255,255,0.06)' },
    },
  },
};

const PALETTE = [
  '#3ecf8e', '#f5c542', '#7fb5ff', '#ff8888',
  '#c084fc', '#34d399', '#fb923c', '#60a5fa',
];

/**
 * Create a Chart.js chart on a canvas element.
 * @param {HTMLCanvasElement} canvas
 * @param {'bar'|'line'} type
 * @param {string[]} labels
 * @param {Array} datasets  Each: { label, data, color? }
 * @returns {Chart}
 */
function createChart(canvas, type, labels, datasets) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not loaded yet');
    return null;
  }

  // Destroy existing chart on this canvas if any
  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();

  const processedDatasets = datasets.map((ds, i) => {
    const color = ds.color || PALETTE[i % PALETTE.length];
    const alpha = `${color}33`; // 20% opacity for fill

    const base = {
      label: ds.label || `Series ${i + 1}`,
      data: ds.data || [],
      borderColor: color,
      backgroundColor: type === 'bar' ? color : alpha,
      borderWidth: type === 'bar' ? 0 : 2,
    };

    if (type === 'line') {
      base.tension = 0.4;
      base.fill = ds.fill !== undefined ? ds.fill : false;
      base.pointBackgroundColor = color;
      base.pointRadius = 3;
      base.pointHoverRadius = 5;
    }

    return base;
  });

  return new Chart(canvas, {
    type,
    data: { labels, datasets: processedDatasets },
    options: LC_CHART_DEFAULTS,
  });
}
