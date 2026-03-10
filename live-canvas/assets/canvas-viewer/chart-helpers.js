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

// Chart types that use per-slice colors instead of a single dataset color
const RADIAL_CHART_TYPES = new Set(['pie', 'doughnut', 'polarArea']);

/**
 * Create a Chart.js chart on a canvas element.
 * @param {HTMLCanvasElement} canvas
 * @param {'bar'|'line'|'pie'|'doughnut'|'radar'|'polarArea'|'bubble'|'scatter'} type
 * @param {string[]} labels
 * @param {Array} datasets  Each: { label, data, color?, yAxisID? }
 *   - bubble data items: { x, y, r }
 *   - scatter data items: { x, y }
 * @param {Array} verticalLines - Optional vertical line markers (line/bar only)
 * @param {Object} options - Optional chart options (scales, etc.)
 * @returns {Chart}
 */
function createChart(canvas, type, labels, datasets, verticalLines = [], options = {}) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not loaded yet');
    return null;
  }

  // Destroy existing chart on this canvas if any
  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();

  const isRadial = RADIAL_CHART_TYPES.has(type);

  const processedDatasets = datasets.map((ds, i) => {
    const color = ds.color || PALETTE[i % PALETTE.length];
    const alpha = `${color}33`; // 20% opacity for fill

    // Radial charts (pie/doughnut/polar) get a slice per data point
    if (isRadial) {
      const sliceColors = (ds.data || []).map((_, j) => PALETTE[j % PALETTE.length]);
      return {
        label: ds.label || `Series ${i + 1}`,
        data: ds.data || [],
        backgroundColor: ds.colors || sliceColors,
        borderColor: 'rgba(15,20,35,0.5)',
        borderWidth: 1,
        hoverOffset: 6,
      };
    }

    const base = {
      label: ds.label || `Series ${i + 1}`,
      data: ds.data || [],
      borderColor: color,
      backgroundColor: (type === 'bar') ? color : alpha,
      borderWidth: (type === 'bar') ? 0 : 2,
    };

    // Support yAxisID for dual-axis charts
    if (ds.yAxisID) {
      base.yAxisID = ds.yAxisID;
    }

    if (type === 'line') {
      base.tension = 0.4;
      base.fill = ds.fill !== undefined ? ds.fill : false;
      base.pointBackgroundColor = color;
      base.pointRadius = 3;
      base.pointHoverRadius = 5;
    }

    if (type === 'radar') {
      base.fill = ds.fill !== undefined ? ds.fill : true;
      base.pointBackgroundColor = color;
      base.pointRadius = 3;
    }

    if (type === 'bubble') {
      base.backgroundColor = `${color}99`; // more opaque for bubbles
      base.borderColor = color;
      base.borderWidth = 1;
    }

    if (type === 'scatter') {
      base.backgroundColor = `${color}cc`;
      base.borderColor = color;
      base.borderWidth = 1;
      base.pointRadius = 5;
      base.pointHoverRadius = 7;
    }

    return base;
  });

  const verticalLinePlugin = {
    id: 'liveCanvasVerticalLines',
    afterDatasetsDraw(chart) {
      if (!Array.isArray(verticalLines) || !verticalLines.length) return;
      const xScale = chart.scales.x;
      const area = chart.chartArea;
      if (!xScale || !area) return;

      const ctx = chart.ctx;
      ctx.save();

      for (const marker of verticalLines) {
        const value = typeof marker === 'string' ? marker : marker?.value;
        if (!value) continue;
        const idx = labels.indexOf(value);
        if (idx < 0) continue;

        const color = marker?.color || '#f5c542';
        const width = marker?.width || 1;
        const label = marker?.label || '';
        const dash = marker?.dash || [5, 4];

        const x = xScale.getPixelForValue(idx);
        ctx.beginPath();
        ctx.setLineDash(dash);
        ctx.moveTo(x, area.top);
        ctx.lineTo(x, area.bottom);
        ctx.lineWidth = width;
        ctx.strokeStyle = color;
        ctx.stroke();

        if (label) {
          ctx.setLineDash([]);
          ctx.fillStyle = color;
          ctx.font = '11px var(--font, sans-serif)';
          ctx.textAlign = 'left';
          ctx.fillText(label, x + 4, area.top + 12);
        }
      }

      ctx.restore();
    },
  };

  // Build base options — radial charts don't use x/y scales
  const baseOptions = isRadial
    ? {
        responsive: LC_CHART_DEFAULTS.responsive,
        maintainAspectRatio: LC_CHART_DEFAULTS.maintainAspectRatio,
        plugins: LC_CHART_DEFAULTS.plugins,
      }
    : { ...LC_CHART_DEFAULTS };

  // Radar uses a 'r' (radial) scale instead of x/y
  if (type === 'radar') {
    baseOptions.scales = {
      r: {
        ticks: { color: 'rgba(255,255,255,0.45)', font: { size: 11 }, backdropColor: 'transparent' },
        grid:  { color: 'rgba(255,255,255,0.12)' },
        pointLabels: { color: 'rgba(255,255,255,0.7)', font: { size: 12 } },
        angleLines: { color: 'rgba(255,255,255,0.08)' },
      },
    };
  }

  // Merge user options with base
  const chartOptions = { ...baseOptions, ...options };

  // If user provided custom scales (for dual-axis or radial overrides), merge them in
  if (options.scales) {
    chartOptions.scales = { ...(baseOptions.scales || LC_CHART_DEFAULTS.scales), ...options.scales };
  }

  return new Chart(canvas, {
    type,
    data: { labels, datasets: processedDatasets },
    options: chartOptions,
    plugins: [verticalLinePlugin],
  });
}
