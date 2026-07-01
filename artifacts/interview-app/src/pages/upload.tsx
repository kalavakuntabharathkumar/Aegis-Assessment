import { useState, useCallback, useEffect } from "react";
import { useLocation } from "wouter";
import { useStartSession } from "@workspace/api-client-react";
import { Bot, Server, UploadCloud, FileText, Check, X, Lightbulb, Loader2, BarChart2, Layers, GitBranch } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import AnimatedBackground from "@/components/AnimatedBackground";

const LOADING_STEPS = [
  "Parsing resume PDF...",
  "Extracting skills & experience...",
  "Querying knowledge base...",
  "Generating questions...",
  "Preparing your interview...",
];

const STEP_DELAYS = [0, 2000, 5000, 9000, 12000];

const LEVEL_BADGE: Record<string, { label: string; bg: string; color: string; border: string; emoji: string }> = {
  beginner:     { label: "Entry Level Detected",  bg: "rgba(5,150,105,0.15)",  color: "#34d399", border: "rgba(5,150,105,0.4)",  emoji: "🌱" },
  intermediate: { label: "Mid Level Detected",    bg: "rgba(8,145,178,0.15)",  color: "#22d3ee", border: "rgba(8,145,178,0.4)",  emoji: "🚀" },
  advanced:     { label: "Senior Level Detected", bg: "rgba(124,58,237,0.15)", color: "#a78bfa", border: "rgba(124,58,237,0.4)", emoji: "⚡" },
};

export default function UploadPage() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [role, setRole] = useState<string>("");
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [detectedLevel, setDetectedLevel] = useState<string | null>(null);
  const [pendingRedirect, setPendingRedirect] = useState<string | null>(null);

  const startSession = useStartSession();

  useEffect(() => {
    if (!isLoading) {
      setCompletedSteps([]);
      return;
    }
    const timers = STEP_DELAYS.map((delay, i) =>
      setTimeout(() => setCompletedSteps((prev) => [...prev, i]), delay)
    );
    return () => timers.forEach(clearTimeout);
  }, [isLoading]);

  // When level is detected and we have a pending redirect, wait briefly then go
  useEffect(() => {
    if (detectedLevel && pendingRedirect) {
      const t = setTimeout(() => {
        setIsLoading(false);
        setLocation(pendingRedirect);
      }, 1500);
      return () => clearTimeout(t);
    }
  }, [detectedLevel, pendingRedirect, setLocation]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f?.type === "application/pdf") setFile(f);
    else toast({ title: "Invalid file type", description: "Please upload a PDF file.", variant: "destructive" });
  }, [toast]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f?.type === "application/pdf") setFile(f);
    else if (f) toast({ title: "Invalid file type", description: "Please upload a PDF file.", variant: "destructive" });
  };

  const handleStart = () => {
    if (!file || !role) {
      toast({ title: "Missing fields", description: "Please provide both a resume and select a role.", variant: "destructive" });
      return;
    }
    setIsLoading(true);
    setDetectedLevel(null);
    setPendingRedirect(null);

    startSession.mutate(
      { data: { role, resume: file } },
      {
        onSuccess: (data) => {
          const level = (data as { experience_level?: string }).experience_level ?? "intermediate";
          setDetectedLevel(level);
          setPendingRedirect(`/interview/${data.session_id}`);
        },
        onError: (err) => {
          setIsLoading(false);
          toast({ title: "Error starting session", description: err.message || "An unknown error occurred.", variant: "destructive" });
        },
      }
    );
  };

  const canSubmit = !!file && !!role && !isLoading;
  const badge = detectedLevel ? LEVEL_BADGE[detectedLevel] ?? LEVEL_BADGE.intermediate : null;

  return (
    <div className="min-h-screen text-white" style={{ background: "#0A0A0F" }}>
      <AnimatedBackground />

      {/* Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: "rgba(10,10,15,0.92)", backdropFilter: "blur(12px)" }}>
          <div
            className="p-10 rounded-3xl border border-white/10 max-w-sm w-full mx-6 text-center space-y-8"
            style={{ background: "rgba(255,255,255,0.04)" }}
          >
            {/* Spinning ring */}
            <div className="flex items-center justify-center">
              <div className="relative w-20 h-20">
                <div className="absolute inset-0 rounded-full border-4 border-white/10" />
                <div
                  className="absolute inset-0 rounded-full border-4 border-transparent animate-spin"
                  style={{ borderTopColor: "#7c3aed", borderRightColor: "#0891b2" }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Loader2 className="w-7 h-7 text-violet-400 animate-spin" />
                </div>
              </div>
            </div>

            <div className="space-y-3 text-left">
              {LOADING_STEPS.map((step, i) => (
                <div
                  key={step}
                  className="flex items-center gap-3 transition-all duration-500"
                  style={{ opacity: completedSteps.includes(i) ? 1 : 0.3 }}
                >
                  <div
                    className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300"
                    style={{
                      background: completedSteps.includes(i) ? "linear-gradient(135deg, #7c3aed, #0891b2)" : "rgba(255,255,255,0.1)",
                    }}
                  >
                    {completedSteps.includes(i) && <Check className="w-3 h-3 text-white" />}
                  </div>
                  <span className={`text-sm ${completedSteps.includes(i) ? "text-white" : "text-zinc-500"}`}>
                    {step}
                  </span>
                </div>
              ))}
            </div>

            {/* Experience level badge — appears when session is ready */}
            {badge && (
              <div
                className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border"
                style={{
                  background: badge.bg,
                  borderColor: badge.border,
                  animation: "fadeUp 0.4s ease-out both",
                }}
              >
                <span className="text-base">{badge.emoji}</span>
                <span className="text-sm font-semibold" style={{ color: badge.color }}>{badge.label}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Navbar */}
      <nav className="border-b border-white/5 backdrop-blur-xl sticky top-0 z-40" style={{ background: "rgba(10,10,15,0.8)" }}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <button onClick={() => setLocation("/")} className="font-bold text-lg tracking-tight hover:text-violet-400 transition-colors">
            Aegis Assessment
          </button>
          <span className="text-sm text-zinc-500">New Session</span>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="mb-12 text-center" style={{ animation: "fadeUp 0.6s ease-out both" }}>
          <h1 className="text-4xl font-bold mb-3">Configure Your Session</h1>
          <p className="text-zinc-400 text-lg">Set up your personalized AI interview in under a minute.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Left — Info panel */}
          <div className="space-y-8" style={{ animation: "fadeUp 0.6s ease-out 0.1s both" }}>
            <div className="glass p-8 rounded-2xl space-y-6">
              <h2 className="text-xl font-semibold">What happens next?</h2>
              <div className="space-y-5">
                {[
                  "Your resume is parsed for skills and technologies",
                  "Experience level is auto-detected from your background",
                  "We query 1,214 ML knowledge vectors in Pinecone",
                  "Claude AI generates questions across 3 rounds: Aptitude, Technical, HR",
                  "Your answers are scored and stored for final analysis",
                ].map((step, i) => (
                  <div key={step} className="flex gap-4">
                    <div
                      className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold"
                      style={{ background: "linear-gradient(135deg, #7c3aed, #0891b2)" }}
                    >
                      {i + 1}
                    </div>
                    <p className="text-zinc-300 leading-relaxed pt-0.5">{step}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass p-6 rounded-2xl flex gap-4 border border-yellow-500/20" style={{ background: "rgba(234,179,8,0.05)" }}>
              <Lightbulb className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-zinc-400 leading-relaxed">
                <span className="text-yellow-400 font-semibold">Pro tip:</span> Resumes with clear skills sections get more targeted, relevant questions.
              </p>
            </div>
          </div>

          {/* Right — Form */}
          <div className="space-y-6" style={{ animation: "fadeUp 0.6s ease-out 0.2s both" }}>
            {/* Role selector */}
            <div>
              <label className="text-sm font-medium text-zinc-400 mb-3 block uppercase tracking-wider">Target Role</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { value: "AI/ML Engineer",       icon: Bot,       desc: "Neural networks, ML algorithms, model deployment" },
                  { value: "Backend Engineer",      icon: Server,    desc: "APIs, databases, system design, architecture" },
                  { value: "Data Scientist",        icon: BarChart2, desc: "Statistical analysis, modeling, data pipelines" },
                  { value: "Full-Stack Engineer",   icon: Layers,    desc: "Frontend, backend, databases, end-to-end systems" },
                  { value: "DevOps Engineer",       icon: GitBranch, desc: "CI/CD, infrastructure, cloud, reliability" },
                ].map(({ value, icon: Icon, desc }) => (
                  <button
                    key={value}
                    onClick={() => setRole(value)}
                    className="p-5 rounded-xl border text-left transition-all duration-200 hover:scale-[1.02]"
                    style={{
                      background: role === value ? "rgba(124,58,237,0.1)" : "rgba(255,255,255,0.03)",
                      borderColor: role === value ? "#7c3aed" : "rgba(255,255,255,0.08)",
                      boxShadow: role === value ? "0 0 20px rgba(124,58,237,0.2)" : "none",
                    }}
                  >
                    <Icon className="w-6 h-6 mb-3" style={{ color: role === value ? "#a78bfa" : "#71717a" }} />
                    <div className="font-semibold text-sm mb-1">{value}</div>
                    <div className="text-xs text-zinc-500 leading-relaxed">{desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* File upload */}
            <div>
              <label className="text-sm font-medium text-zinc-400 mb-3 block uppercase tracking-wider">Resume (PDF)</label>
              {file ? (
                <div
                  className="flex items-center gap-4 p-5 rounded-xl border border-green-500/30"
                  style={{ background: "rgba(5,150,105,0.08)" }}
                >
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: "rgba(239,68,68,0.15)" }}>
                    <FileText className="w-5 h-5 text-red-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{file.name}</p>
                    <p className="text-xs text-zinc-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                      <Check className="w-3.5 h-3.5 text-white" />
                    </div>
                    <button
                      onClick={() => setFile(null)}
                      className="w-6 h-6 rounded-full flex items-center justify-center text-zinc-500 hover:text-white hover:bg-white/10 transition-colors"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ) : (
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className="relative flex flex-col items-center justify-center h-44 rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer group"
                  style={{
                    borderColor: isDragging ? "#7c3aed" : "rgba(255,255,255,0.1)",
                    background: isDragging ? "rgba(124,58,237,0.08)" : "rgba(255,255,255,0.02)",
                  }}
                >
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    data-testid="input-resume"
                  />
                  <div style={{ animation: "bounce 2s ease-in-out infinite" }}>
                    <UploadCloud className="w-10 h-10 text-zinc-600 group-hover:text-violet-400 transition-colors mb-3" />
                  </div>
                  <p className="text-sm font-medium text-zinc-400 group-hover:text-white transition-colors">
                    Drag and drop your PDF here
                  </p>
                  <p className="text-xs text-zinc-600 mt-1">or click to browse</p>
                </div>
              )}
            </div>

            {/* Submit */}
            <button
              onClick={handleStart}
              disabled={!canSubmit}
              data-testid="button-start"
              className="w-full py-4 rounded-xl font-semibold text-base transition-all duration-200"
              style={{
                background: canSubmit
                  ? "linear-gradient(135deg, #7c3aed, #0891b2)"
                  : "rgba(255,255,255,0.05)",
                color: canSubmit ? "white" : "#52525b",
                cursor: canSubmit ? "pointer" : "not-allowed",
              }}
              onMouseEnter={(e) => canSubmit && ((e.target as HTMLElement).style.transform = "scale(1.01)")}
              onMouseLeave={(e) => ((e.target as HTMLElement).style.transform = "scale(1)")}
            >
              Analyze Resume & Generate Questions
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
