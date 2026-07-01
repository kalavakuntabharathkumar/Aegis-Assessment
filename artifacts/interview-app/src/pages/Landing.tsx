import { useLocation } from "wouter";
import { Brain, Database, Zap, ArrowRight, Upload, MessageSquare, FileText, BarChart3 } from "lucide-react";
import AnimatedBackground from "@/components/AnimatedBackground";

export default function LandingPage() {
  const [, setLocation] = useLocation();

  return (
    <div className="min-h-screen text-white" style={{ background: "#0A0A0F" }}>
      <AnimatedBackground />

      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 backdrop-blur-xl" style={{ background: "rgba(10,10,15,0.8)" }}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "linear-gradient(135deg, #7c3aed, #0891b2)" }}>
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight">Aegis Assessment</span>
          </div>
          <button
            onClick={() => setLocation("/upload")}
            className="px-5 py-2 rounded-lg text-sm font-semibold transition-all duration-200 hover:scale-105"
            style={{ background: "linear-gradient(135deg, #7c3aed, #0891b2)" }}
          >
            Begin Assessment
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-40 pb-24 px-6 text-center relative">
        <div className="max-w-4xl mx-auto space-y-8" style={{ animation: "fadeUp 0.8s ease-out both" }}>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/10 text-sm text-zinc-400" style={{ background: "rgba(255,255,255,0.04)" }}>
            <div className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
            Powered by RAG Technology
          </div>

          <h1 className="text-5xl md:text-7xl font-bold leading-tight tracking-tight">
            AI Interviews That{" "}
            <span className="gradient-text">Actually Know You</span>
          </h1>

          <p className="text-xl text-zinc-400 max-w-2xl mx-auto leading-relaxed">
            Upload your resume. Get 5 personalized questions grounded in real ML textbooks.
            No generic questions. Ever.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
            <button
              onClick={() => setLocation("/upload")}
              className="group flex items-center gap-2 px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-200 hover:scale-105 hover:shadow-2xl"
              style={{ background: "linear-gradient(135deg, #7c3aed, #0891b2)", boxShadow: "0 0 40px rgba(124,58,237,0.3)" }}
            >
              Start Interview
              <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
            </button>
            <a
              href="#how-it-works"
              className="flex items-center gap-2 px-8 py-4 rounded-xl font-semibold text-lg border border-white/10 text-zinc-300 transition-all duration-200 hover:border-white/20 hover:bg-white/5"
            >
              View How It Works
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 pt-8 max-w-lg mx-auto">
            {[
              { value: "1,214", label: "Knowledge Vectors" },
              { value: "5", label: "ML Textbooks" },
              { value: "100%", label: "Personalized" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="p-4 rounded-xl border border-white/10 transition-all duration-200 hover:scale-105"
                style={{ background: "rgba(255,255,255,0.04)" }}
              >
                <div className="text-2xl font-bold gradient-text">{stat.value}</div>
                <div className="text-xs text-zinc-500 mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Built different.</h2>
            <p className="text-zinc-400 text-lg">Every feature designed to give you a real assessment.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: Brain,
                title: "Resume-Aware Questions",
                desc: "We extract your exact skills and tailor every question to your background — not a random pool.",
                color: "#7c3aed",
              },
              {
                icon: Database,
                title: "RAG Knowledge Base",
                desc: "Questions grounded in Tom Mitchell, Bishop, and Burkov ML textbooks via Pinecone vector search.",
                color: "#0891b2",
              },
              {
                icon: Zap,
                title: "Instant Analysis",
                desc: "Complete session summary with all topics covered delivered immediately after every interview.",
                color: "#059669",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="glass p-8 rounded-2xl transition-all duration-300 hover:scale-105 group"
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center mb-6"
                  style={{ background: `${feature.color}22` }}
                >
                  <feature.icon className="w-6 h-6" style={{ color: feature.color }} />
                </div>
                <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                <p className="text-zinc-400 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">How it works</h2>
            <p className="text-zinc-400 text-lg">Four steps. Zero fluff.</p>
          </div>

          <div className="relative">
            {/* Connecting line */}
            <div className="hidden md:block absolute top-10 left-[12.5%] right-[12.5%] h-px" style={{ background: "linear-gradient(90deg, #7c3aed, #0891b2)" }} />

            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              {[
                { icon: Upload, step: "01", title: "Upload Resume", desc: "Drop your PDF resume" },
                { icon: FileText, step: "02", title: "Select Role", desc: "Choose your target position" },
                { icon: MessageSquare, step: "03", title: "Answer Questions", desc: "5 personalized technical Qs" },
                { icon: BarChart3, step: "04", title: "View Analysis", desc: "Get your full session review" },
              ].map((step, i) => (
                <div key={step.step} className="flex flex-col items-center text-center" style={{ animation: `fadeUp 0.6s ease-out ${i * 0.1}s both` }}>
                  <div
                    className="w-20 h-20 rounded-2xl flex items-center justify-center mb-4 relative z-10 transition-all duration-300 hover:scale-110"
                    style={{ background: "linear-gradient(135deg, #7c3aed22, #0891b222)", border: "1px solid rgba(255,255,255,0.1)" }}
                  >
                    <step.icon className="w-8 h-8 text-violet-400" />
                  </div>
                  <div className="text-xs font-mono text-violet-400 mb-1">{step.step}</div>
                  <h3 className="font-semibold text-lg mb-2">{step.title}</h3>
                  <p className="text-zinc-500 text-sm">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <div
            className="p-12 rounded-3xl border border-white/10"
            style={{ background: "linear-gradient(135deg, rgba(124,58,237,0.15), rgba(8,145,178,0.15))" }}
          >
            <h2 className="text-3xl font-bold mb-4">Ready to get assessed?</h2>
            <p className="text-zinc-400 mb-8">Upload your resume and start a real AI interview in under a minute.</p>
            <button
              onClick={() => setLocation("/upload")}
              className="px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-200 hover:scale-105"
              style={{ background: "linear-gradient(135deg, #7c3aed, #0891b2)", boxShadow: "0 0 40px rgba(124,58,237,0.4)" }}
            >
              Start Your Interview →
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-white/5 text-center text-zinc-600 text-sm">
        Built with FastAPI • Pinecone • Claude AI • React
      </footer>
    </div>
  );
}
