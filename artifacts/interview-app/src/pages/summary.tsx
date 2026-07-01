import { useState, useEffect } from "react";
import { useParams, useLocation } from "wouter";
import { useGetSummary, getGetSummaryQueryKey } from "@workspace/api-client-react";
import { Loader2, ShieldAlert, Download, RefreshCw, Trophy, Hash, BookOpen, Pen, Star } from "lucide-react";

const SKILL_COLORS = [
  { bg: "rgba(124,58,237,0.15)", border: "rgba(124,58,237,0.3)", text: "#a78bfa" },
  { bg: "rgba(8,145,178,0.15)", border: "rgba(8,145,178,0.3)", text: "#22d3ee" },
  { bg: "rgba(5,150,105,0.15)", border: "rgba(5,150,105,0.3)", text: "#34d399" },
  { bg: "rgba(217,119,6,0.15)", border: "rgba(217,119,6,0.3)", text: "#fbbf24" },
  { bg: "rgba(236,72,153,0.15)", border: "rgba(236,72,153,0.3)", text: "#f472b6" },
];

function AnimatedCheckmark() {
  const [visible, setVisible] = useState(false);
  useEffect(() => { setTimeout(() => setVisible(true), 100); }, []);
  return (
    <svg width="80" height="80" viewBox="0 0 80 80" fill="none" className="mx-auto">
      <circle
        cx="40" cy="40" r="36"
        stroke="url(#cg)" strokeWidth="3" fill="none"
        strokeDasharray="226" strokeDashoffset={visible ? 0 : 226}
        style={{ transition: "stroke-dashoffset 1s ease-out" }}
      />
      <polyline
        points="24,40 36,52 56,28"
        stroke="url(#cg)" strokeWidth="3.5" fill="none"
        strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray="60" strokeDashoffset={visible ? 0 : 60}
        style={{ transition: "stroke-dashoffset 0.6s ease-out 0.8s" }}
      />
      <defs>
        <linearGradient id="cg" x1="0" y1="0" x2="80" y2="80" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7c3aed" />
          <stop offset="1" stopColor="#0891b2" />
        </linearGradient>
      </defs>
    </svg>
  );
}

function avgScoreGradient(avg: number) {
  if (avg > 7) return { from: "#059669", to: "#34d399", text: "#34d399", rating: "Excellent Performance" };
  if (avg >= 5) return { from: "#d97706", to: "#fbbf24", text: "#fbbf24", rating: "Good Performance" };
  return { from: "#dc2626", to: "#f87171", text: "#f87171", rating: "Needs Improvement" };
}

export default function SummaryPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  const [, setLocation] = useLocation();
  const [openIndex, setOpenIndex] = useState<number | null>(0);
  const [downloading, setDownloading] = useState(false);

  const { data: summary, isLoading, error } = useGetSummary(sessionId, {
    query: { enabled: !!sessionId, queryKey: getGetSummaryQueryKey(sessionId) },
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#0A0A0F" }}>
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-10 h-10 animate-spin text-violet-400" />
          <p className="text-zinc-400 animate-pulse">Compiling assessment dossier...</p>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4" style={{ background: "#0A0A0F" }}>
        <div className="glass p-8 rounded-2xl max-w-md text-center space-y-4">
          <ShieldAlert className="w-12 h-12 text-red-400 mx-auto" />
          <h2 className="text-xl font-semibold text-white">Retrieval Error</h2>
          <p className="text-zinc-400">Failed to retrieve session summary.</p>
          <button onClick={() => setLocation("/")} className="px-6 py-2 rounded-lg text-sm font-medium border border-white/10 text-zinc-300 hover:bg-white/5 transition-colors">
            Return Home
          </button>
        </div>
      </div>
    );
  }

  const scores = summary.qa_pairs.map(qa => (qa as { score?: number | null }).score).filter((s): s is number => s != null);
  const avgScore = scores.length > 0 ? Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10 : null;
  const scoreStyle = avgScore != null ? avgScoreGradient(avgScore) : null;

  const avgWords = Math.round(
    summary.qa_pairs.reduce((sum, qa) => sum + (qa.answer?.split(/\s+/).filter(Boolean).length ?? 0), 0) /
    Math.max(summary.qa_pairs.length, 1)
  );

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const res = await fetch(`/api/report/${sessionId}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `aegis_report_${sessionId.slice(0, 8)}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      // Silently fail — user sees no change
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="min-h-screen text-white pb-20" style={{ background: "#0A0A0F" }}>
      {/* Gradient top accent */}
      <div className="h-1 w-full" style={{ background: "linear-gradient(90deg, #7c3aed, #0891b2)" }} />

      <div className="max-w-4xl mx-auto px-6 py-16 space-y-12">
        {/* Hero section */}
        <div className="text-center space-y-6" style={{ animation: "fadeUp 0.6s ease-out both" }}>
          <AnimatedCheckmark />
          <h1 className="text-4xl font-bold">Interview Complete!</h1>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <span
              className="px-4 py-1.5 rounded-full text-sm font-medium"
              style={{ background: "rgba(124,58,237,0.15)", color: "#a78bfa", border: "1px solid rgba(124,58,237,0.3)" }}
            >
              {summary.candidate_name}
            </span>
            <span
              className="px-4 py-1.5 rounded-full text-sm font-medium"
              style={{ background: "rgba(8,145,178,0.15)", color: "#22d3ee", border: "1px solid rgba(8,145,178,0.3)" }}
            >
              {summary.role}
            </span>
            <span className="text-xs text-zinc-600">{new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</span>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4" style={{ animation: "fadeUp 0.6s ease-out 0.1s both" }}>
          {[
            { icon: Trophy, label: "Questions", value: `${summary.qa_pairs.length}/5`, gradient: "from-violet-600 to-violet-400" },
            { icon: BookOpen, label: "Topics Covered", value: summary.topics_covered?.length ?? 0, gradient: "from-cyan-600 to-cyan-400" },
            { icon: Pen, label: "Avg Words", value: avgWords, gradient: "from-emerald-600 to-emerald-400" },
            { icon: Star, label: "Avg Score", value: avgScore != null ? `${avgScore}/10` : "—", gradient: scoreStyle ? `from-[${scoreStyle.from}] to-[${scoreStyle.to}]` : "from-zinc-600 to-zinc-400" },
          ].map(({ icon: Icon, label, value }, i) => {
            const isScore = label === "Avg Score";
            const cardBg = isScore && scoreStyle
              ? `linear-gradient(135deg, ${scoreStyle.from}20, ${scoreStyle.to}10)`
              : "rgba(255,255,255,0.03)";
            const cardBorder = isScore && scoreStyle
              ? `1px solid ${scoreStyle.from}40`
              : "1px solid rgba(255,255,255,0.06)";
            return (
              <div
                key={label}
                className="p-5 rounded-2xl text-center space-y-2 hover:scale-105 transition-transform duration-200"
                style={{ background: cardBg, border: cardBorder }}
              >
                <div
                  className="w-8 h-8 rounded-lg mx-auto flex items-center justify-center"
                  style={{
                    background: isScore && scoreStyle
                      ? `linear-gradient(135deg, ${scoreStyle.from}, ${scoreStyle.to})`
                      : ["linear-gradient(135deg,#7c3aed,#a78bfa)", "linear-gradient(135deg,#0891b2,#22d3ee)", "linear-gradient(135deg,#059669,#34d399)"][i] ?? "linear-gradient(135deg,#7c3aed,#0891b2)",
                  }}
                >
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <div
                  className="text-2xl font-bold"
                  style={{ color: isScore && scoreStyle ? scoreStyle.text : undefined }}
                >
                  {isScore && scoreStyle ? value : <span className="gradient-text">{value}</span>}
                </div>
                <div className="text-xs text-zinc-500 uppercase tracking-wider">{label}</div>
                {isScore && scoreStyle && (
                  <div className="text-xs font-medium" style={{ color: scoreStyle.text }}>{scoreStyle.rating}</div>
                )}
              </div>
            );
          })}
        </div>

        {/* Skills + Topics grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6" style={{ animation: "fadeUp 0.6s ease-out 0.2s both" }}>
          {summary.extracted_skills?.length > 0 && (
            <div className="glass p-6 rounded-2xl space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">Skills Assessed</h2>
              <div className="flex flex-wrap gap-2">
                {summary.extracted_skills.map((skill, i) => {
                  const c = SKILL_COLORS[i % SKILL_COLORS.length];
                  return (
                    <span key={skill} className="px-3 py-1 rounded-full text-xs font-medium" style={{ background: c.bg, border: `1px solid ${c.border}`, color: c.text }}>
                      {skill}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
          {summary.topics_covered?.length > 0 && (
            <div className="glass p-6 rounded-2xl space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">Topics Covered</h2>
              <div className="flex flex-wrap gap-2">
                {summary.topics_covered.map((topic, i) => {
                  const c = SKILL_COLORS[(i + 2) % SKILL_COLORS.length];
                  return (
                    <span key={topic} className="px-3 py-1 rounded-full text-xs font-medium" style={{ background: c.bg, border: `1px solid ${c.border}`, color: c.text }}>
                      {topic}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Per-round breakdown */}
        {(() => {
          const breakdown = (summary as any).round_breakdown as Record<string, { total: number; answered: number; avg_score: number | null }> | undefined;
          if (!breakdown || Object.keys(breakdown).length === 0) return null;

          const ROUND_META: Record<string, { label: string; color: string; border: string; bg: string }> = {
            aptitude:  { label: "Aptitude Round",  color: "#fbbf24", border: "rgba(217,119,6,0.3)",  bg: "rgba(217,119,6,0.07)"  },
            technical: { label: "Technical Round", color: "#22d3ee", border: "rgba(8,145,178,0.3)",  bg: "rgba(8,145,178,0.07)"  },
            hr:        { label: "HR Round",        color: "#a78bfa", border: "rgba(124,58,237,0.3)", bg: "rgba(124,58,237,0.07)" },
          };
          const ORDER = ["aptitude", "technical", "hr"];
          const rounds = ORDER.filter(r => breakdown[r]);

          return (
            <div className="space-y-4" style={{ animation: "fadeUp 0.6s ease-out 0.25s both" }}>
              <h2 className="text-2xl font-bold">Round Breakdown</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {rounds.map((round) => {
                  const meta = ROUND_META[round] ?? ROUND_META.technical;
                  const data = breakdown[round];
                  const pct = data.total > 0 ? Math.round((data.answered / data.total) * 100) : 0;
                  return (
                    <div
                      key={round}
                      className="p-5 rounded-2xl space-y-3"
                      style={{ background: meta.bg, border: `1px solid ${meta.border}` }}
                    >
                      <p className="text-xs font-bold uppercase tracking-wider" style={{ color: meta.color }}>{meta.label}</p>
                      <div className="flex items-end justify-between">
                        <div>
                          <p className="text-2xl font-black text-white">{data.answered}<span className="text-sm text-zinc-500 font-normal">/{data.total}</span></p>
                          <p className="text-xs text-zinc-500 mt-0.5">answered</p>
                        </div>
                        {data.avg_score != null && (
                          <div className="text-right">
                            <p className="text-2xl font-black" style={{ color: meta.color }}>{data.avg_score}<span className="text-sm font-normal text-zinc-500">/10</span></p>
                            <p className="text-xs text-zinc-500 mt-0.5">avg score</p>
                          </div>
                        )}
                      </div>
                      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                        <div
                          className="h-full rounded-full transition-all duration-700"
                          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${meta.color}99, ${meta.color})` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })()}

        {/* Q&A Review */}
        <div className="space-y-4" style={{ animation: "fadeUp 0.6s ease-out 0.3s both" }}>
          <h2 className="text-2xl font-bold">Session Review</h2>
          <div className="space-y-3">
            {summary.qa_pairs.map((qa, index) => {
              const wordCount = qa.answer?.split(/\s+/).filter(Boolean).length ?? 0;
              const isOpen = openIndex === index;
              const qaScore = (qa as { score?: number | null }).score;
              const qaFeedback = (qa as { feedback?: string | null }).feedback;
              const qaStrength = (qa as { strength?: string | null }).strength;
              const qaImprovement = (qa as { improvement?: string | null }).improvement;

              let scoreColor = "#a78bfa";
              if (qaScore != null) {
                if (qaScore <= 4) scoreColor = "#f87171";
                else if (qaScore <= 6) scoreColor = "#fbbf24";
                else if (qaScore <= 8) scoreColor = "#a78bfa";
                else scoreColor = "#34d399";
              }

              return (
                <div
                  key={index}
                  className="rounded-2xl border border-white/8 overflow-hidden transition-all duration-200"
                  style={{
                    background: "rgba(255,255,255,0.03)",
                    borderLeft: "3px solid",
                    borderLeftColor: isOpen ? "#7c3aed" : "rgba(124,58,237,0.3)",
                  }}
                >
                  <button
                    className="w-full p-6 text-left"
                    onClick={() => setOpenIndex(isOpen ? null : index)}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-2 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="px-2 py-0.5 rounded text-xs font-mono font-bold" style={{ background: "rgba(124,58,237,0.2)", color: "#a78bfa" }}>
                            Q{index + 1}
                          </span>
                          {qa.topic && (
                            <span className="px-2 py-0.5 rounded text-xs font-medium" style={{ background: "rgba(8,145,178,0.15)", color: "#22d3ee" }}>
                              {qa.topic}
                            </span>
                          )}
                          <span className="text-xs text-zinc-600">{wordCount} words</span>
                        </div>
                        <p className="font-semibold text-white leading-snug">{qa.question}</p>
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0">
                        {qaScore != null && (
                          <span className="text-lg font-black" style={{ color: scoreColor }}>{qaScore}<span className="text-xs text-zinc-600 font-normal">/10</span></span>
                        )}
                        <div className={`text-zinc-500 transition-transform duration-200 mt-1 ${isOpen ? "rotate-180" : ""}`}>
                          <Hash className="w-4 h-4" />
                        </div>
                      </div>
                    </div>
                  </button>

                  {isOpen && (
                    <div className="px-6 pb-6 border-t border-white/5 pt-4 space-y-4">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: "#22d3ee" }}>Your Answer</p>
                        <p className="text-zinc-300 leading-relaxed whitespace-pre-wrap">
                          {qa.answer || <span className="italic text-zinc-600">No response provided.</span>}
                        </p>
                      </div>

                      {qaFeedback && (
                        <div className="space-y-2 pt-2 border-t border-white/5">
                          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">AI Feedback</p>
                          <p className="text-sm text-zinc-400 leading-relaxed">{qaFeedback}</p>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
                            {qaStrength && (
                              <div className="p-3 rounded-lg" style={{ background: "rgba(5,150,105,0.08)", border: "1px solid rgba(5,150,105,0.2)" }}>
                                <p className="text-xs font-semibold text-emerald-400 mb-1">✓ Strength</p>
                                <p className="text-xs text-zinc-400">{qaStrength}</p>
                              </div>
                            )}
                            {qaImprovement && (
                              <div className="p-3 rounded-lg" style={{ background: "rgba(217,119,6,0.08)", border: "1px solid rgba(217,119,6,0.2)" }}>
                                <p className="text-xs font-semibold text-amber-400 mb-1">↑ Improve</p>
                                <p className="text-xs text-zinc-400">{qaImprovement}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 pt-4" style={{ animation: "fadeUp 0.6s ease-out 0.4s both" }}>
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm border border-white/10 text-zinc-300 hover:bg-white/5 hover:border-white/20 transition-all flex-1 disabled:opacity-60"
          >
            {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            {downloading ? "Generating report..." : "Download Report"}
          </button>
          <button
            onClick={() => setLocation("/")}
            data-testid="button-new-interview"
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-200 hover:scale-105 flex-1"
            style={{ background: "linear-gradient(135deg, #7c3aed, #0891b2)" }}
          >
            <RefreshCw className="w-4 h-4" />
            Start New Interview
          </button>
        </div>
      </div>
    </div>
  );
}
