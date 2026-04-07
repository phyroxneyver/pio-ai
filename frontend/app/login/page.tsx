"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (localStorage.getItem("token")) {
      router.push("/dashboard");
    }
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Por favor completa todos los campos.");
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/login`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        }
      );

      if (!res.ok) {
        setError("Correo o contraseña incorrectos.");
        return;
      }

      const data = await res.json();
      localStorage.setItem("token", data.token);
      localStorage.setItem("user",JSON.stringify(data.user))
      document.cookie= `token=${data.token}; path=/`;
      router.push("/");
      setError("Error de conexión. Intenta de nuevo.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen relative flex items-center justify-center bg-[#0a0a0a] px-4 overflow-hidden antialiased">
      {/* Subtle Glows */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-zinc-800/20 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        <div className="bg-[#141414] border border-zinc-800/50 rounded-3xl shadow-2xl p-10 backdrop-blur-sm">
          
          {/* Logo Section - Matching screenshot style */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-white rounded-[2rem] mb-6 shadow-xl relative overflow-hidden group">
              {/* Egg shell effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-white to-zinc-100"></div>
              {/* Yolk */}
              <div className="w-8 h-10 bg-[#fbb100] rounded-full z-10 shadow-sm transition-transform group-hover:scale-110"></div>
            </div>
            <div className="space-y-1">
                <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-[0.3em]">Sistema Avícola</span>
                <h1 className="text-3xl font-black text-white tracking-tight">PIO AI</h1>
            </div>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-2">
              <label className="block text-xs font-bold text-zinc-400 uppercase tracking-widest pl-1">
                Correo electrónico
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="adrian@pioai.local"
                className="w-full bg-[#0d0d0d] border border-zinc-800 focus:border-amber-500/50 rounded-2xl px-5 py-4 text-white placeholder-zinc-600 focus:outline-none focus:ring-4 focus:ring-amber-500/5 transition-all shadow-inner"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center px-1">
                <label className="block text-xs font-bold text-zinc-400 uppercase tracking-widest">
                  Contraseña
                </label>
                <button type="button" className="text-[10px] text-amber-500 font-bold hover:underline uppercase tracking-tighter">
                  ¿Olvidaste tu clave?
                </button>
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#0d0d0d] border border-zinc-800 focus:border-amber-500/50 rounded-2xl px-5 py-4 text-white focus:outline-none focus:ring-4 focus:ring-amber-500/5 transition-all shadow-inner"
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border-l-4 border-red-500 p-3 rounded-r-xl transition-all">
                <p className="text-red-400 text-xs font-bold flex items-center">
                  <span className="mr-2 text-base"></span> {error}
                </p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="group w-full bg-[#fbb100] hover:bg-[#ffc124] text-black rounded-2xl py-4 text-sm font-black shadow-[0_10px_20px_rgba(251,177,0,0.2)] disabled:opacity-50 transition-all transform active:scale-[0.98] flex items-center justify-center gap-3 relative overflow-hidden"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin"></div>
              ) : (
                <>
                  <span className="uppercase tracking-[0.2em]">Ingresar al Sistema</span>
                  <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                </>
              )}
            </button>
          </form>

          <footer className="mt-10 pt-6 border-t border-zinc-800/50 text-center">
            <p className="text-zinc-600 text-[10px] font-medium tracking-[0.1em] uppercase">
              &copy; {new Date().getFullYear()} PIO AI &bull; Seguridad & Control
            </p>
          </footer>
        </div>
      </div>
    </main>
  );
}
