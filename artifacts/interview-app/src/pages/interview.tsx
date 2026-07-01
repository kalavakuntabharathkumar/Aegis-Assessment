import { useState, useEffect, useRef } from "react";
import { useParams, useLocation } from "wouter";
import { useGetSession, useSubmitAnswer, getGetSessionQueryKey } from "@workspace/api-client-react";
import { Loader2, ShieldAlert, User, CheckCircle, ArrowRight, RotateCcw, TrendingUp, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const SKILL_COLORS = [
  { bg: "rgba(124,58,237,0.15)", border: "rgba(124,58,237,0.3)", text: "#a78bfa" },
  { bg: "rgba(8,145,178,0.15)", border: "rgba(8,145,178,0.3)", text: "#22d3ee" },
  { bg: "rgba(5,150,105,0.15)", border: "rgba(5,150,105,0.3)", text: "#34d399" },
  { bg: "rgba(217,119,6,0.15)", border: "rgba(217,119,6,0.3)", text: "#fbbf24" },
];

const LEVEL_BADGE: Record<string, { label: string; bg: string; color: string; border: string }> = {
  beginner:     { label: "Entry Level",  bg: "rgba(5,150,105,0.15)",  color: "#34d399", border: "rgba(5,150,105,0.3)" },
  intermediate: { label: "Mid Level",    bg: "rgba(8,145,178,0.15)",  color: "#22d3ee", border: "rgba(8,145,178,0.3)" },
  advanced:     { label: "Senior Level", bg: "rgba(124,58,237,0.15)", color: "#a78bfa", border: "rgba(124,58,237,0.3)" },
};

const DIFF_BADGE: Record<string, { label: string; bg: string; color: string; border: string }> = {
  beginner:     { label: "Foundational", bg: "rgba(5,150,105,0.15)",  color: "#34d399", border: "rgba(5,150,105,0.3)" },
  intermediate: { label: "Applied",      bg: "rgba(8,145,178,0.15)",  color: "#22d3ee", border: "rgba(8,145,178,0.3)" },
  advanced:     { label: "Expert",       bg: "rgba(124,58,237,0.15)", color: "#a78bfa", border: "rgba(124,58,237,0.3)" },
};

function scoreColor(score: number) {
  if (score <= 4) return { text: "#f87171", ring: "#ef4444", glow: "rgba(239,68,68,0.25)" };
  if (score <= 6) return { text: "#fbbf24", ring: "#f59e0b", glow: "rgba(245,158,11,0.25)" };
  if (score <= 8) return { text: "#a78bfa", ring: "#7c3aed", glow: "rgba(124,58,237,0.25)" };
  return { text: "#34d399", ring: "#059669", glow: "rgba(5,150,105,0.25)" };
}

interface ScoreData {
  score: number | null;
  feedback: string | null;
  strength: string | null;
  improvement: string | null;
  isComplete: boolean;
}

function ScoreRevealCard({
  data,
  onContinue,
  isLastQuestion,
}: {
  data: ScoreData;
  onContinue: () => void;
  isLastQuestion: boolean;
}) {
  const [visible, setVisible] = useState(false);
  useEffect(() => { setTimeout(() => setVisible(true), 30); }, []);

  const { score, feedback, strength, improvement } = data;
  const colors = score ? scoreColor(score) : null;
  const pct = score ? score * 10 : 0;
  const deg = Math.round((pct / 100) * 360);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center pb-0"
      style={{ background: "rgba(10,10,15,0.7)", backdropFilter: "blur(8px)" }}
    >
      <div
        className="w-full max-w-xl rounded-t-3xl border-t border-white/10 p-8 space-y-6"
        style={{
          background: "rgba(18,18,28,0.98)",
          transform: visible ? "translateY(0)" : "translateY(100%)",
          transition: "transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        {score ? (
          <>
            {/* Header */}
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-lg text-white">Your Score</h3>
              <span className="text-xs text-zinc-500 uppercase tracking-wider">AI Evaluation</span>
            </div>

            {/* Score row */}
            <div className="flex items-center gap-6">
              {/* Circular gauge */}
              <div className="relative flex-shrink-0 w-24 h-24">
                <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
                  <circle
                    cx="50" cy="50" r="42" fill="none"
                    stroke={colors?.ring}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${(deg / 360) * 263.9} 263.9`}
                    style={{ filter: `drop-shadow(0 0 6px ${colors?.glow})`, transition: "stroke-dasharray 0.8s ease-out" }}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-black" style={{ color: colors?.text }}>{score}</span>
                  <span className="text-xs text-zinc-500">/10</span>
                </div>
              </div>

              {/* Feedback */}
              <div className="flex-1 space-y-1">
                {feedback && <p className="text-sm text-zinc-300 leading-relaxed">{feedback}</p>}
              </div>
            </div>

            {/* Strength + Improvement */}
            <div className="space-y-3">
              {strength && (
                <div className="flex gap-3 p-3 rounded-xl" style={{ background: "rgba(5,150,105,0.08)", border: "1px solid rgba(5,150,105,0.2)" }}>
                  <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-0.5">Strength</p>
                    <p className="text-sm text-zinc-300">{strength}</p>
                  </div>
                </div>
              )}
              {improvement && (
                <div className="flex gap-3 p-3 rounded-xl" style={{ background: "rgba(217,119,6,0.08)", border: "1px solid rgba(217,119,6,0.2)" }}>
                  <TrendingUp className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-0.5">Improve</p>
                    <p className="text-sm text-zinc-300">{improvement}</p>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex items-center gap-3 py-4">
            <AlertCircle className="w-5 h-5 text-zinc-500" />
            <p className="text-zinc-400 text-sm">Scoring unavailable for this answer.</p>
          </div>
        )}

        {/* Continue button */}
        <button
          onClick={onContinue}
          className="w-full py-3.5 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all hover:scale-[1.02]"
          style={{ background: "linear-gradient(135deg, #7c3aed, #0891b2)", boxShadow: "0 0 20px rgba(124,58,237,0.3)" }}
        >
          {isLastQuestion ? "View Summary →" : <>Next Question <ArrowRight className="w-4 h-4" /></>}
        </button>
      </div>
    </div>
  );
}

export default function InterviewPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  const [, setLocation] = useLocation();
  const { toast } = useToast();

  const [currentAnswer, setCurrentAnswer] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [transitioning, setTransitioning] = useState(false);
  const [scoreData, setScoreData] = useState<ScoreData | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { data: session, isLoading, error, refetch } = useGetSession(sessionId, {
    query: {
      enabled: !!sessionId,
      queryKey: getGetSessionQueryKey(sessionId),
      refetchOnWindowFocus: false,
    },
  });

  const submitAnswer = useSubmitAnswer();

  // Timer
  useEffect(() => {
    const interval = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60).toString().padStart(2, "0");
    const sec = (s % 60).toString().padStart(2, "0");
    return `${m}:${sec}`;
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  }, [currentAnswer]);

  const handleSubmit = () => {
    if (!session || !currentAnswer.trim()) return;
    const questionIndex = session.answers_count;
    if (questionIndex >= session.questions.length) return;
    const currentQuestion = session.questions[questionIndex];

    setTransitioning(true);
    setTimeout(() => {
      submitAnswer.mutate(
        { data: { session_id: sessionId, question_id: currentQuestion.id, answer: currentAnswer } },
        {
          onSuccess: (res) => {
            setCurrentAnswer("");
            setTransitioning(false);
            setScoreData({
              score: res.score ?? null,
              feedback: res.feedback ?? null,
              strength: res.strength ?? null,
              improvement: res.improvement ?? null,
              isComplete: res.is_complete,
            });
          },
          onError: (err) => {
            setTransitioning(false);
            toast({ title: "Failed to submit", description: err.message || "An error occurred", variant: "destructive" });
          },
        }
      );
    }, 300);
  };

  const handleContinue = () => {
    if (!scoreData) return;
    const complete = scoreData.isComplete;
    setScoreData(null);
    if (complete) {
      toast({ title: "Assessment complete! 🎯" });
      setLocation(`/summary/${sessionId}`);
    } else {
      refetch();
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#0A0A0F" }}>
        <div className="flex flex-col items-center gap-4 text-violet-400">
          <Loader2 className="w-10 h-10 animate-spin" />
          <p className="text-lg font-medium text-zinc-400 animate-pulse">Initializing assessment...</p>
        </div>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4" style={{ background: "#0A0A0F" }}>
        <div className="glass p-8 rounded-2xl max-w-md text-center space-y-4">
          <ShieldAlert className="w-12 h-12 text-red-400 mx-auto" />
          <h2 className="text-xl font-semibold text-white">Connection Error</h2>
          <p className="text-zinc-400">Failed to load the assessment session.</p>
          <button onClick={() => setLocation("/")} className="px-6 py-2 rounded-lg text-sm font-medium border border-white/10 text-zinc-300 hover:bg-white/5 transition-colors">
            Return Home
          </button>
        </div>
      </div>
    );
  }

  if (session.status === "completed") {
    setLocation(`/summary/${sessionId}`);
    return null;
  }

  const currentIndex = session.answers_count;
  const currentQuestion = session.questions[currentIndex];
  const isLastQuestion = currentIndex === session.total_questions - 1;
  const level = (session as { experience_level?: string }).experience_level ?? "intermediate";
  const levelBadge = LEVEL_BADGE[level] ?? LEVEL_BADGE.intermediate;
  const diffBadge = DIFF_BADGE[level] ?? DIFF_BADGE.intermediate;

  return (
    <div className="min-h-screen text-white flex flex-col" style={{ background: "#0A0A0F" }}>
      {/* Score reveal card */}
      {scoreData && (
        <ScoreRevealCard data={scoreData} onContinue={handleContinue} isLastQuestion={isLastQuestion} />
      )}

      {/* Top bar */}
      <header className="border-b border-white/5 sticky top-0 z-40 backdrop-blur-xl" style={{ background: "rgba(10,10,15,0.85)" }}>
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-7 h-7 rounded-full bg-violet-500/20 flex items-center justify-center">
              <User className="w-4 h-4 text-violet-400" />
            </div>
            <span className="text-zinc-300 font-medium">{session.candidate_name}</span>
          </div>

          <div className="flex items-center gap-2">
            <span
              className="px-3 py-1 rounded-full text-xs font-semibold"
              style={{ background: "rgba(124,58,237,0.15)", color: "#a78bfa", border: "1px solid rgba(124,58,237,0.3)" }}
            >
              {session.role}
            </span>
            <span
              className="px-3 py-1 rounded-full text-xs font-semibold"
              style={{ background: levelBadge.bg, color: levelBadge.color, border: `1px solid ${levelBadge.border}` }}
            >
              {levelBadge.label}
            </span>
          </div>

          <div className="text-sm font-mono text-zinc-500">
            ⏱ {formatTime(elapsed)}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-3xl w-full mx-auto px-6 py-10 flex flex-col gap-8">
        {/* Progress circles + bar */}
        <div className="space-y-4">
          <div className="flex items-center justify-center gap-3">
            {session.questions.map((_, i) => {
              const done = i < currentIndex;
              const active = i === currentIndex;
              return (
                <div key={i} className="relative flex items-center justify-center">
                  {active && (
                    <div
                      className="absolute w-8 h-8 rounded-full animate-ping"
                      style={{ background: "rgba(124,58,237,0.3)" }}
                    />
                  )}
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center transition-all duration-300"
                    style={{
                      background: done
                        ? "linear-gradient(135deg, #7c3aed, #0891b2)"
                        : active
                        ? "rgba(124,58,237,0.3)"
                        : "rgba(255,255,255,0.06)",
                      border: active ? "2px solid #7c3aed" : done ? "none" : "2px solid rgba(255,255,255,0.1)",
                    }}
                  >
                    {done && <CheckCircle className="w-4 h-4 text-white" />}
                    {active && <div className="w-2 h-2 rounded-full bg-violet-400" />}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="relative h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
            <div
              className="absolute left-0 top-0 h-full rounded-full transition-all duration-700"
              style={{
                width: `${(currentIndex / session.total_questions) * 100}%`,
                background: "linear-gradient(90deg, #7c3aed, #0891b2)",
              }}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-zinc-500">
            <span className="uppercase tracking-wider">Progress</span>
            <span className="text-violet-400 font-medium">Question {currentIndex + 1} of {session.total_questions}</span>
          </div>
        </div>

        {/* Skills strip */}
        {session.questions[currentIndex]?.topic && (
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin">
            {[session.questions[currentIndex].topic, ...(session.questions.slice(0, currentIndex).map(q => q.topic).filter(Boolean))].slice(0, 6).map((skill, i) => {
              const c = SKILL_COLORS[i % SKILL_COLORS.length];
              return (
                <span
                  key={`${skill}-${i}`}
                  className="flex-shrink-0 px-3 py-1 rounded-full text-xs font-medium"
                  style={{ background: c.bg, border: `1px solid ${c.border}`, color: c.text }}
                >
                  {skill}
                </span>
              );
            })}
          </div>
        )}

        {/* Question card */}
        <div
          className="glass rounded-2xl overflow-hidden transition-all duration-300"
          style={{
            opacity: transitioning ? 0 : 1,
            transform: transitioning ? "translateX(-40px)" : "translateX(0)",
            border: "1px solid transparent",
            backgroundImage: "linear-gradient(rgba(255,255,255,0.04), rgba(255,255,255,0.04)), linear-gradient(135deg, rgba(124,58,237,0.4), rgba(8,145,178,0.4))",
            backgroundOrigin: "border-box",
            backgroundClip: "padding-box, border-box",
          }}
        >
          <div className="p-8 space-y-6">
            {/* Header row */}
            <div className="flex items-center justify-between">
              <span
                className="px-3 py-1 rounded-full text-xs font-mono font-semibold"
                style={{ background: "rgba(124,58,237,0.15)", color: "#a78bfa", border: "1px solid rgba(124,58,237,0.25)" }}
              >
                Q{currentIndex + 1}
              </span>
              <div className="flex items-center gap-2">
                {currentQuestion?.topic && (
                  <span
                    className="px-3 py-1 rounded-full text-xs font-medium"
                    style={{ background: "rgba(8,145,178,0.15)", color: "#22d3ee", border: "1px solid rgba(8,145,178,0.25)" }}
                  >
                    {currentQuestion.topic}
                  </span>
                )}
                <span
                  className="px-2.5 py-1 rounded-full text-xs font-medium"
                  style={{ background: diffBadge.bg, color: diffBadge.color, border: `1px solid ${diffBadge.border}` }}
                >
                  {diffBadge.label}
                </span>
              </div>
            </div>

            {/* Question */}
            <p className="text-xl leading-relaxed font-medium text-white">{currentQuestion?.question}</p>

            <p className="text-xs text-zinc-600 flex items-center gap-1.5">
              <span>💡</span> Be specific and explain your reasoning
            </p>
          </div>

          {/* Answer area */}
          <div className="border-t border-white/5 p-6 space-y-4">
            <div className="flex items-center justify-between text-xs text-zinc-500 mb-2">
              <span className="uppercase tracking-wider font-medium">Your Answer</span>
              <span>{currentAnswer.length} chars</span>
            </div>
            <textarea
              ref={textareaRef}
              data-testid="textarea-answer"
              placeholder="Formulate your response here..."
              className="w-full bg-transparent text-zinc-200 placeholder-zinc-600 resize-none outline-none text-base leading-relaxed min-h-[160px]"
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setCurrentAnswer("")}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-zinc-500 hover:text-zinc-300 hover:bg-white/5 transition-all"
          >
            <RotateCcw className="w-4 h-4" />
            Clear
          </button>

          <button
            onClick={handleSubmit}
            disabled={!currentAnswer.trim() || submitAnswer.isPending || transitioning}
            data-testid="button-submit"
            className="group flex items-center gap-2 px-7 py-3 rounded-xl font-semibold text-sm transition-all duration-200 hover:scale-105 disabled:opacity-40 disabled:scale-100 disabled:cursor-not-allowed"
            style={{
              background: "linear-gradient(135deg, #7c3aed, #0891b2)",
              boxShadow: currentAnswer.trim() ? "0 0 25px rgba(124,58,237,0.35)" : "none",
            }}
          >
            {submitAnswer.isPending ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Scoring answer...</>
            ) : isLastQuestion ? (
              <>Complete Interview 🎯</>
            ) : (
              <>Submit Answer <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" /></>
            )}
          </button>
        </div>
      </main>
    </div>
  );
}
