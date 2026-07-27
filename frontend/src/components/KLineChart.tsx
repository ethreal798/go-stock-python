import React, { useEffect, useRef } from "react";
import { createChart, ColorType, CrosshairMode } from "lightweight-charts";
import type {
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
} from "lightweight-charts";
import type { KLineData } from "@/types/stock";

interface KLineChartProps {
  data: KLineData[];
  height?: number;
  symbol?: string;
}

const KLineChart: React.FC<KLineChartProps> = ({
  data,
  height = 400,
  symbol,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "#ffffff" },
        textColor: "#333",
      },
      grid: {
        vertLines: { color: "#f0f0f0" },
        horzLines: { color: "#f0f0f0" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: "#f0f0f0",
      },
      timeScale: {
        borderColor: "#f0f0f0",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#f5222d",
      downColor: "#52c41a",
      borderUpColor: "#f5222d",
      borderDownColor: "#52c41a",
      wickUpColor: "#f5222d",
      wickDownColor: "#52c41a",
    });
    candleSeriesRef.current = candleSeries;

    const volumeSeries = chart.addHistogramSeries({
      color: "#26a69a",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [height]);

  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current || !data.length)
      return;

    const candleData: CandlestickData[] = data.map((d) => ({
      time: d.time as import("lightweight-charts").Time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    const volumeData: HistogramData[] = data.map((d) => ({
      time: d.time as import("lightweight-charts").Time,
      value: d.volume,
      color: d.close >= d.open ? "rgba(245,34,45,0.5)" : "rgba(82,196,26,0.5)",
    }));

    candleSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  return (
    <div>
      {symbol && (
        <div style={{ padding: "6px 0", fontWeight: 600, color: "#1d2129" }}>
          {symbol} K线图
        </div>
      )}
      <div ref={containerRef} style={{ width: "100%" }} />
    </div>
  );
};

export default KLineChart;
