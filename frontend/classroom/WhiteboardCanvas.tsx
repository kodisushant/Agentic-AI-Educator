import React, { useEffect, useRef, useState } from "react";
import { BoardCommand, BoxCommand, TextCommand, ArrowCommand, EquationCommand, MermaidCommand } from "./types";

interface WhiteboardCanvasProps {
  commands: BoardCommand[];
  remediationCommands?: BoardCommand[];
  stepIndex: number;
  highlightId?: string | null;
  onElementClick?: (id: string) => void;
  className?: string;
}

export const WhiteboardCanvas: React.FC<WhiteboardCanvasProps> = ({
  commands,
  remediationCommands = [],
  stepIndex,
  highlightId,
  onElementClick,
  className = "",
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState<boolean>(false);
  const [panStart, setPanStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [renderedMermaid, setRenderedMermaid] = useState<Record<string, string>>({});
  const [isPenActive, setIsPenActive] = useState<boolean>(false);
  const freehandCanvasRef = useRef<HTMLCanvasElement>(null);
  const isDrawingRef = useRef<boolean>(false);
  const lastPointRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Merge regular and remediation commands, handling clear commands
  const activeCommands = React.useMemo(() => {
    const combined = [...commands, ...remediationCommands];
    const result: BoardCommand[] = [];

    for (const cmd of combined) {
      if (cmd.type === "clear") {
        result.length = 0; // Clear all previous commands
      } else {
        result.push(cmd);
      }
    }
    return result;
  }, [commands, remediationCommands]);

  // Load KaTeX if not loaded
  useEffect(() => {
    if (typeof window !== "undefined" && !(window as any).katex) {
      const script = document.createElement("script");
      script.src = "https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js";
      script.async = true;
      document.head.appendChild(script);

      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css";
      document.head.appendChild(link);
    }
  }, []);

  // Dynamically render Mermaid diagrams
  useEffect(() => {
    const mermaidCmds = activeCommands.filter((c): c is MermaidCommand => c.type === "mermaid");
    if (mermaidCmds.length === 0) return;

    const renderCharts = async () => {
      if (typeof window === "undefined") return;

      if (!(window as any).mermaid) {
        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js";
        script.async = true;
        script.onload = () => {
          (window as any).mermaid.initialize({
            startOnLoad: false,
            theme: "dark",
            themeVariables: {
              primaryColor: "#0284c7",
              primaryTextColor: "#f8fafc",
              primaryBorderColor: "#38bdf8",
              lineColor: "#64748b",
              secondaryColor: "#334155",
              tertiaryColor: "#1e293b",
            },
          });
          processMermaid(mermaidCmds);
        };
        document.head.appendChild(script);
      } else {
        processMermaid(mermaidCmds);
      }
    };

    const processMermaid = async (cmds: MermaidCommand[]) => {
      const mermaid = (window as any).mermaid;
      if (!mermaid) return;

      const newRendered: Record<string, string> = {};
      for (const cmd of cmds) {
        try {
          const uniqueId = `mermaid_${cmd.id.replace(/[^a-zA-Z0-9]/g, "_")}_${stepIndex}`;
          const { svg } = await mermaid.render(uniqueId, cmd.chart);
          newRendered[cmd.id] = svg;
        } catch (err) {
          console.warn("Mermaid render error for cmd:", cmd.id, err);
        }
      }
      setRenderedMermaid(newRendered);
    };

    renderCharts();
  }, [activeCommands, stepIndex]);

  // Helper for KaTeX rendering
  const renderLatex = (latex: string): string => {
    if (typeof window !== "undefined" && (window as any).katex) {
      try {
        return (window as any).katex.renderToString(latex, {
          throwOnError: false,
          displayMode: true,
        });
      } catch (e) {
        return latex;
      }
    }
    return latex;
  };

  // Build lookup map for Box element coordinates so arrows can bind by from_id / to_id
  const boxLookup = React.useMemo(() => {
    const map = new Map<string, BoxCommand>();
    for (const cmd of activeCommands) {
      if (cmd.type === "box") {
        map.set(cmd.id, cmd);
      }
    }
    return map;
  }, [activeCommands]);

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button === 0) {
      setIsPanning(true);
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isPanning) {
      setPan({
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.15, 2.5));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.15, 0.5));
  const handleTogglePen = () => {
    setIsPenActive((prev) => !prev);
  };

  const handleClearPen = () => {
    const canvas = freehandCanvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext("2d");
      ctx?.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  const handlePenMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isPenActive) return;
    isDrawingRef.current = true;
    const canvas = freehandCanvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    lastPointRef.current = {
      x: (e.clientX - rect.left) / zoom,
      y: (e.clientY - rect.top) / zoom,
    };
  };

  const handlePenMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawingRef.current || !isPenActive) return;
    const canvas = freehandCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    const curX = (e.clientX - rect.left) / zoom;
    const curY = (e.clientY - rect.top) / zoom;

    ctx.strokeStyle = "#f59e0b"; // warm amber teacher marker
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(lastPointRef.current.x, lastPointRef.current.y);
    ctx.lineTo(curX, curY);
    ctx.stroke();

    lastPointRef.current = { x: curX, y: curY };
  };

  const handlePenMouseUp = () => {
    isDrawingRef.current = false;
  };

  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div
      className={`relative w-full h-[580px] bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col select-none ${className}`}
      ref={containerRef}
    >
      {/* Top Whiteboard Bar */}
      <div className="absolute top-3 left-4 z-20 flex items-center gap-2">
        <div className="flex items-center gap-2 bg-slate-900/90 backdrop-blur px-3 py-1.5 rounded-lg border border-slate-700/80 shadow-md">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-semibold text-slate-200">Interactive Canvas</span>
          <span className="text-[10px] text-sky-400 font-mono bg-sky-950/80 px-1.5 py-0.5 rounded border border-sky-800/60">
            Step {stepIndex + 1}
          </span>
        </div>

        {remediationCommands.length > 0 && (
          <div className="flex items-center gap-1.5 bg-rose-950/90 text-rose-300 text-xs px-2.5 py-1.5 rounded-lg border border-rose-800/80 animate-pulse">
            <svg className="w-3.5 h-3.5 text-rose-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span className="font-medium">Visual Remediation Active</span>
          </div>
        )}
      </div>

      {/* Floating Canvas Controls */}
      <div className="absolute top-3 right-4 z-20 flex items-center gap-1.5 bg-slate-900/90 backdrop-blur p-1 rounded-xl border border-slate-700/80 shadow-lg">
        <button
          onClick={handleZoomIn}
          title="Zoom In"
          className="w-7 h-7 flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <span className="text-[11px] font-mono text-slate-400 px-1">
          {Math.round(zoom * 100)}%
        </span>
        <button
          onClick={handleZoomOut}
          title="Zoom Out"
          className="w-7 h-7 flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
        <div className="w-[1px] h-4 bg-slate-700 mx-0.5" />
        <button
          onClick={handleResetView}
          title="Reset Canvas View"
          className="px-2 h-7 flex items-center justify-center text-xs text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition"
        >
          Reset
        </button>
        <div className="w-[1px] h-4 bg-slate-700 mx-0.5" />
        <button
          onClick={handleTogglePen}
          title="Freehand Pen Tool"
          className={`w-7 h-7 flex items-center justify-center rounded-lg transition ${
            isPenActive
              ? "text-amber-300 bg-amber-500/20 border border-amber-500/40 shadow-sm"
              : "text-slate-400 hover:text-amber-300 hover:bg-slate-800"
          }`}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>
        {isPenActive && (
          <button
            onClick={handleClearPen}
            title="Clear Pen Sketches"
            className="px-1.5 h-7 text-[10px] text-slate-400 hover:text-rose-300 hover:bg-slate-800 rounded-lg transition font-mono"
          >
            Clear Pen
          </button>
        )}
      </div>

      {/* Canvas Viewport (Pannable & Zoomable) */}
      <div
        className="w-full h-full relative cursor-grab active:cursor-grabbing overflow-hidden"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Subtle Engineering Grid Background */}
        <div
          className="absolute inset-0 pointer-events-none opacity-20"
          style={{
            backgroundImage:
              "radial-gradient(circle, #38bdf8 1px, transparent 1px), radial-gradient(circle, #64748b 0.5px, transparent 0.5px)",
            backgroundSize: "40px 40px, 10px 10px",
            backgroundPosition: `${pan.x}px ${pan.y}px`,
          }}
        />

        {/* Scaled & Translated Board Layer */}
        <div
          className="absolute top-0 left-0 w-full h-full transform-gpu origin-top-left transition-transform duration-75"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          }}
        >
          {/* Freehand Drawing Overlay */}
          <canvas
            ref={freehandCanvasRef}
            width={1400}
            height={900}
            onMouseDown={handlePenMouseDown}
            onMouseMove={handlePenMouseMove}
            onMouseUp={handlePenMouseUp}
            onMouseLeave={handlePenMouseUp}
            className={`absolute top-0 left-0 z-10 ${
              isPenActive ? "pointer-events-auto cursor-crosshair" : "pointer-events-none"
            }`}
          />
          {/* SVG Vector Layer for Arrows & Connection Markers */}
          <svg
            className="absolute top-0 left-0 w-[1400px] h-[900px] pointer-events-none"
            style={{ overflow: "visible" }}
          >
            <defs>
              <marker
                id="arrowhead-default"
                markerWidth="8"
                markerHeight="8"
                refX="6"
                refY="4"
                orient="auto"
              >
                <path d="M 0 0 L 8 4 L 0 8 z" fill="#0284c7" />
              </marker>
              <marker
                id="arrowhead-green"
                markerWidth="8"
                markerHeight="8"
                refX="6"
                refY="4"
                orient="auto"
              >
                <path d="M 0 0 L 8 4 L 0 8 z" fill="#16a34a" />
              </marker>
              <marker
                id="arrowhead-red"
                markerWidth="8"
                markerHeight="8"
                refX="6"
                refY="4"
                orient="auto"
              >
                <path d="M 0 0 L 8 4 L 0 8 z" fill="#dc2626" />
              </marker>
              <marker
                id="arrowhead-amber"
                markerWidth="8"
                markerHeight="8"
                refX="6"
                refY="4"
                orient="auto"
              >
                <path d="M 0 0 L 8 4 L 0 8 z" fill="#d97706" />
              </marker>
            </defs>

            {/* Render Arrow Commands */}
            {activeCommands
              .filter((c): c is ArrowCommand => c.type === "arrow")
              .map((cmd) => {
                let sx = cmd.start_x ?? 0;
                let sy = cmd.start_y ?? 0;
                let ex = cmd.end_x ?? 0;
                let ey = cmd.end_y ?? 0;

                // Support from_id and to_id binding if specified
                if (cmd.from_id && boxLookup.has(cmd.from_id)) {
                  const b = boxLookup.get(cmd.from_id)!;
                  sx = b.x + (b.width ?? 80) / 2;
                  sy = b.y + (b.height ?? 50);
                }
                if (cmd.to_id && boxLookup.has(cmd.to_id)) {
                  const b = boxLookup.get(cmd.to_id)!;
                  ex = b.x + (b.width ?? 80) / 2;
                  ey = b.y;
                }

                const color = cmd.color || "#0284c7";
                let markerId = "arrowhead-default";
                if (color.includes("16a34a") || color.includes("green")) markerId = "arrowhead-green";
                else if (color.includes("dc2626") || color.includes("red")) markerId = "arrowhead-red";
                else if (color.includes("d97706") || color.includes("amber")) markerId = "arrowhead-amber";

                const midX = (sx + ex) / 2;
                const midY = (sy + ey) / 2;

                return (
                  <g key={cmd.id} className="transition-all duration-300">
                    <line
                      x1={sx}
                      y1={sy}
                      x2={ex}
                      y2={ey}
                      stroke={color}
                      strokeWidth={2.5}
                      markerEnd={`url(#${markerId})`}
                      strokeDasharray={cmd.id.includes("remed") ? "4,4" : undefined}
                    />
                    {cmd.label && (
                      <text
                        x={midX}
                        y={midY - 8}
                        fill={color}
                        fontSize={13}
                        fontWeight="600"
                        textAnchor="middle"
                        className="bg-slate-900 px-1 font-mono select-none"
                      >
                        {cmd.label}
                      </text>
                    )}
                  </g>
                );
              })}
          </svg>

          {/* Render Box Commands */}
          {activeCommands
            .filter((c): c is BoxCommand => c.type === "box")
            .map((cmd) => {
              const isHighlighted = highlightId === cmd.id;
              const isRemediation = cmd.id.includes("remed") || cmd.id.includes("misconception");

              return (
                <div
                  key={cmd.id}
                  onClick={() => onElementClick?.(cmd.id)}
                  style={{
                    position: "absolute",
                    left: `${cmd.x}px`,
                    top: `${cmd.y}px`,
                    width: `${cmd.width ?? 80}px`,
                    height: `${cmd.height ?? 50}px`,
                    borderColor: isHighlighted
                      ? "#f59e0b"
                      : isRemediation
                      ? "#f43f5e"
                      : cmd.color || "#3b82f6",
                    backgroundColor: cmd.fill || "#0f172a",
                  }}
                  className={`border-2 rounded-xl flex items-center justify-center font-mono font-bold text-base transition-all duration-300 cursor-pointer shadow-md hover:scale-105 ${
                    isHighlighted ? "ring-4 ring-amber-400/50 shadow-amber-500/20" : ""
                  } ${isRemediation ? "ring-2 ring-rose-500/60 animate-pulse" : ""}`}
                >
                  <span className="text-slate-100">{cmd.label ?? ""}</span>
                </div>
              );
            })}

          {/* Render Text Commands */}
          {activeCommands
            .filter((c): c is TextCommand => c.type === "text")
            .map((cmd) => {
              const isRemediation = cmd.id.includes("misconception") || cmd.id.includes("remediation");
              return (
                <div
                  key={cmd.id}
                  style={{
                    position: "absolute",
                    left: `${cmd.x}px`,
                    top: `${cmd.y}px`,
                    fontSize: `${cmd.size ?? 18}px`,
                    color: isRemediation ? "#f87171" : cmd.color || "#f8fafc",
                  }}
                  className={`font-sans tracking-wide transition-all duration-300 pointer-events-none max-w-2xl leading-relaxed ${
                    isRemediation
                      ? "bg-rose-950/80 px-3 py-1.5 rounded-lg border border-rose-800/60 shadow-lg font-medium"
                      : "font-semibold"
                  }`}
                >
                  {cmd.content}
                </div>
              );
            })}

          {/* Render Equation Commands (KaTeX) */}
          {activeCommands
            .filter((c): c is EquationCommand => c.type === "equation")
            .map((cmd) => (
              <div
                key={cmd.id}
                style={{
                  position: "absolute",
                  left: `${cmd.x}px`,
                  top: `${cmd.y}px`,
                }}
                className="bg-slate-900/90 border border-indigo-500/30 rounded-xl p-3 shadow-xl backdrop-blur transition-all duration-300 max-w-md"
              >
                {cmd.label && (
                  <div className="text-[11px] font-medium text-indigo-300 uppercase tracking-wider mb-1">
                    {cmd.label}
                  </div>
                )}
                <div
                  className="text-sky-300 text-lg font-mono overflow-x-auto"
                  dangerouslySetInnerHTML={{
                    __html: renderLatex(cmd.latex),
                  }}
                />
              </div>
            ))}

          {/* Render Mermaid Diagrams */}
          {activeCommands
            .filter((c): c is MermaidCommand => c.type === "mermaid")
            .map((cmd) => (
              <div
                key={cmd.id}
                style={{
                  position: "absolute",
                  left: `${cmd.x ?? 50}px`,
                  top: `${cmd.y ?? 100}px`,
                }}
                className="bg-slate-900/90 border border-slate-700/80 rounded-2xl p-4 shadow-2xl backdrop-blur transition-all duration-300 max-w-2xl overflow-hidden"
              >
                {cmd.title && (
                  <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-300 border-b border-slate-800 pb-1.5">
                    <svg className="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                    </svg>
                    <span>{cmd.title}</span>
                  </div>
                )}
                {renderedMermaid[cmd.id] ? (
                  <div
                    className="overflow-x-auto text-xs"
                    dangerouslySetInnerHTML={{ __html: renderedMermaid[cmd.id] }}
                  />
                ) : (
                  <pre className="text-[11px] font-mono text-sky-400 bg-slate-950/80 p-2.5 rounded-lg border border-slate-800 overflow-x-auto whitespace-pre-wrap">
                    {cmd.chart}
                  </pre>
                )}
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};
