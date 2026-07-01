export default function AnimatedBackground() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
      <div
        className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full blur-3xl opacity-20"
        style={{
          background: "radial-gradient(circle, #7c3aed, transparent 70%)",
          animation: "blob1 25s ease-in-out infinite",
        }}
      />
      <div
        className="absolute top-1/3 -right-40 w-[500px] h-[500px] rounded-full blur-3xl opacity-15"
        style={{
          background: "radial-gradient(circle, #0891b2, transparent 70%)",
          animation: "blob2 30s ease-in-out infinite",
        }}
      />
      <div
        className="absolute -bottom-40 left-1/3 w-[450px] h-[450px] rounded-full blur-3xl opacity-10"
        style={{
          background: "radial-gradient(circle, #6d28d9, transparent 70%)",
          animation: "blob3 20s ease-in-out infinite",
        }}
      />
    </div>
  );
}
