import Plotly from "plotly.js-basic-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";
import type { TimeSeriesPoint } from "../api/schema";

const Plot = createPlotlyComponent(Plotly);

/** Props for the shared Plotly time-series chart. */
interface TimeSeriesChartProps {
  points: TimeSeriesPoint[];
  title: string;
  unit?: string;
}

/** Renders numeric observations against their timestamps. */
export function TimeSeriesChart({
  points,
  title,
  unit = "",
}: TimeSeriesChartProps) {
  const seriesNames = [...new Set(points.map((point) => point.series ?? title))];
  const data = seriesNames.map((series) => {
    const values = points.filter((point) => (point.series ?? title) === series);
    return {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: series,
      x: values.map((point) => point.timestamp),
      y: values.map((point) => point.value),
      hovertemplate: `%{y}${unit}<extra>${series}</extra>`,
    };
  });

  return (
    <Plot
      data={data}
      layout={{
        autosize: true,
        height: 320,
        margin: { l: 48, r: 18, t: 18, b: 46 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: "#b9c8dc", family: "Inter, system-ui, sans-serif" },
        xaxis: { gridcolor: "#23344c", title: { text: "Time" } },
        yaxis: { gridcolor: "#23344c", title: { text: unit } },
        legend: { orientation: "h" },
      }}
      config={{
        displayModeBar: false,
        responsive: true,
      }}
      useResizeHandler
      className="plot"
      aria-label={title}
    />
  );
}
