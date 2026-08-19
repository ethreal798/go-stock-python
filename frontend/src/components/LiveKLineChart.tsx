import React, { useRef, useEffect, useCallback } from "react";

// ============================================================================
// LiveKLineChart - 纯装饰性 K 线动画组件
// 用途：登录页/首页等场景的视觉装饰，非真实金融数据展示
// 技术：Canvas 2D + requestAnimationFrame，60fps 流畅动画
// ============================================================================

interface LiveKLineChartProps {
  /** 动画速度系数，默认 1.0；越大越快 */
  speed?: number;
  /** K线数量，默认 60 */
  candleCount?: number;
}

interface Candle {
  open: number;
  close: number;
  high: number;
  low: number;
  /** 入场/入场动画进度 0-1 */
  born: number;
}

const LiveKLineChart: React.FC<LiveKLineChartProps> = ({
  speed = 1.0,
  candleCount = 60,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number>(0);
  const candlesRef = useRef<Candle[]>([]);
  const priceRef = useRef<number>(0.5);
  const tickAccumRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);
  const sizeRef = useRef({ w: 0, h: 0, dpr: 1 });

  /** 初始化K线数据 */
  const initCandles = useCallback((count: number) => {
    const candles: Candle[] = [];
    let price = 0.45 + Math.random() * 0.15;
    for (let i = 0; i < count; i++) {
      const { next, candle } = generateCandle(price, 1);
      price = next;
      candle.born = 1;
      candles.push(candle);
    }
    priceRef.current = price;
    candlesRef.current = candles;
  }, []);

  /** 调整Canvas尺寸（含DPR） */
  const resize = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const rect = container.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
    sizeRef.current = { w: rect.width, h: rect.height, dpr };
  }, []);

  /** 主渲染循环 */
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    resize();
    initCandles(candleCount);

    const observer = new ResizeObserver(resize);
    if (containerRef.current) observer.observe(containerRef.current);

    const TICK_MS = 800 / speed;

    const loop = (time: number) => {
      if (!lastTimeRef.current) lastTimeRef.current = time;
      const dt = time - lastTimeRef.current;
      lastTimeRef.current = time;

      tickAccumRef.current += dt;
      while (tickAccumRef.current >= TICK_MS) {
        tickAccumRef.current -= TICK_MS;
        advanceTick();
      }

      draw(ctx);
      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(rafRef.current);
      observer.disconnect();
    };
  }, [candleCount, speed, resize, initCandles]);

  /** 推进一个Tick：更新最后一根K线或生成新K线 */
  const advanceTick = () => {
    const candles = candlesRef.current;
    if (candles.length === 0) return;

    const volatility = 0.008;
    const drift = (Math.random() - 0.5) * volatility;
    let price = priceRef.current + drift;
    price = Math.max(0.15, Math.min(0.85, price));

    const last = candles[candles.length - 1];

    if (Math.random() < 0.22) {
      const { next, candle } = generateCandle(priceRef.current, 0);
      candles.push(candle);
      if (candles.length > candleCount) candles.shift();
      priceRef.current = next;
    } else {
      const newClose = price;
      last.close = newClose;
      last.high = Math.max(last.high, newClose);
      last.low = Math.min(last.low, newClose);
      priceRef.current = price;
    }

    for (let i = 0; i < candles.length; i++) {
      const c = candles[i];
      c.born = Math.min(1, c.born + 0.08);
    }
  };

  /** 渲染函数 */
  const draw = (ctx: CanvasRenderingContext2D) => {
    const { w, h, dpr } = sizeRef.current;
    if (w === 0 || h === 0) return;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    const candles = candlesRef.current;
    if (candles.length === 0) return;

    const padTop = h * 0.08;
    const padBottom = h * 0.12;
    const padLeft = w * 0.06;
    const padRight = w * 0.04;
    const chartW = w - padLeft - padRight;
    const chartH = h - padTop - padBottom;

    // 计算价格范围
    let minP = Infinity,
      maxP = -Infinity;
    for (const c of candles) {
      if (c.low < minP) minP = c.low;
      if (c.high > maxP) maxP = c.high;
    }
    const range = maxP - minP || 0.01;
    const pad = range * 0.15;
    minP -= pad;
    maxP += pad;
    const totalRange = maxP - minP;

    const priceToY = (p: number) =>
      padTop + chartH * (1 - (p - minP) / totalRange);
    const candleW = chartW / candles.length;
    const bodyW = Math.max(2, candleW * 0.55);

    // ---- 淡淡的水平网格线（浅灰） ----
    ctx.strokeStyle = "rgba(0,0,0,0.045)";
    ctx.lineWidth = 1;
    for (let i = 1; i <= 4; i++) {
      const y = padTop + (chartH * i) / 5;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(padLeft + chartW, y);
      ctx.stroke();
    }

    // ---- 绘制K线 ----
    for (let i = 0; i < candles.length; i++) {
      const c = candles[i];
      const x = padLeft + candleW * i + candleW / 2;
      const isUp = c.close >= c.open;

      // 左侧更亮/更饱和，右侧逐渐变淡但仍保持白底可见度
      const t = i / (candles.length - 1);
      const leftFactor = 1 - t;

      // 阳线：品牌蓝系 (#1677ff 为基准，左侧更亮)
      const upR = Math.round(22 + leftFactor * 30);
      const upG = Math.round(119 + leftFactor * 50);
      const upB = Math.round(255);
      const upA = 0.7 + leftFactor * 0.25;

      // 阴线：青色系
      const dnR = Math.round(80 + leftFactor * 20);
      const dnG = Math.round(190 + leftFactor * 30);
      const dnB = Math.round(200 + leftFactor * 30);
      const dnA = 0.6 + leftFactor * 0.2;

      const bodyColor = isUp
        ? `rgba(${upR},${upG},${upB},${upA})`
        : `rgba(${dnR},${dnG},${dnB},${dnA})`;
      const wickColor = isUp
        ? `rgba(${upR},${upG},${upB},${upA * 0.75})`
        : `rgba(${dnR},${dnG},${dnB},${dnA * 0.75})`;

      const yOpen = priceToY(c.open);
      const yClose = priceToY(c.close);
      const yHigh = priceToY(c.high);
      const yLow = priceToY(c.low);
      const bodyTop = Math.min(yOpen, yClose);
      const bodyH = Math.max(1, Math.abs(yClose - yOpen));

      const alpha = c.born;

      ctx.globalAlpha = alpha;

      // 影线
      ctx.strokeStyle = wickColor;
      ctx.lineWidth = Math.max(0.8, bodyW * 0.12);
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(x, yHigh);
      ctx.lineTo(x, yLow);
      ctx.stroke();

      // 实体
      ctx.fillStyle = bodyColor;
      const bw = Math.max(1, bodyW);
      const radius = Math.min(2, bw / 3);
      roundRect(ctx, x - bw / 2, bodyTop, bw, bodyH, radius);
      ctx.fill();

      ctx.globalAlpha = 1;
    }

    // ---- 最后一根K线的呼吸光点（白底适配） ----
    const lastIdx = candles.length - 1;
    if (lastIdx >= 0) {
      const last = candles[lastIdx];
      const x = padLeft + candleW * lastIdx + candleW / 2;
      const y = priceToY(last.close);
      const pulse = 0.5 + 0.5 * Math.sin(Date.now() / 400);
      const dotR = 3 + pulse * 2;
      const isUp = last.close >= last.open;
      const dotCore = isUp ? "rgba(22,119,255,0.9)" : "rgba(80,200,210,0.85)";

      // 外层光晕
      const dotGlow = ctx.createRadialGradient(x, y, 0, x, y, dotR * 5);
      dotGlow.addColorStop(
        0,
        isUp
          ? `rgba(22,119,255,${0.2 + pulse * 0.15})`
          : `rgba(80,200,210,${0.15 + pulse * 0.12})`,
      );
      dotGlow.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = dotGlow;
      ctx.beginPath();
      ctx.arc(x, y, dotR * 5, 0, Math.PI * 2);
      ctx.fill();

      // 中心点
      ctx.fillStyle = dotCore;
      ctx.beginPath();
      ctx.arc(x, y, dotR * 0.8, 0, Math.PI * 2);
      ctx.fill();

      // 白色高光点
      ctx.fillStyle = "rgba(255,255,255,0.95)";
      ctx.beginPath();
      ctx.arc(x, y, dotR * 0.35, 0, Math.PI * 2);
      ctx.fill();
    }

    // ---- 底部白色淡出遮罩 ----
    const bottomFade = ctx.createLinearGradient(0, h - padBottom, 0, h);
    bottomFade.addColorStop(0, "rgba(255,255,255,0)");
    bottomFade.addColorStop(1, "rgba(255,255,255,0.75)");
    ctx.fillStyle = bottomFade;
    ctx.fillRect(0, h - padBottom, w, padBottom);
  };

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          display: "block",
          width: "100%",
          height: "100%",
        }}
      />
    </div>
  );
};

/** 生成一根新K线 */
function generateCandle(
  prevClose: number,
  born: number,
): { next: number; candle: Candle } {
  const volatility = 0.008 + Math.random() * 0.012;
  const direction = Math.random() > 0.49 ? 1 : -1;
  const change = direction * Math.random() * volatility;
  const close = Math.max(0.15, Math.min(0.85, prevClose + change));
  const high = Math.max(prevClose, close) + Math.random() * volatility * 0.8;
  const low = Math.min(prevClose, close) - Math.random() * volatility * 0.8;
  return {
    next: close,
    candle: {
      open: prevClose,
      close,
      high: Math.min(1, high),
      low: Math.max(0, low),
      born,
    },
  };
}

/** Canvas 圆角矩形 */
function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const radius = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + w - radius, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
  ctx.lineTo(x + w, y + h - radius);
  ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
  ctx.lineTo(x + radius, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}

export default LiveKLineChart;
