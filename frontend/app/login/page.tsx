"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
    Eye,
    EyeOff,
    LockKeyhole,
    LogIn,
    Mail,
    Sparkles,
} from "lucide-react";
import { LogoMark } from "@/components/brand/logo-mark";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { getToken, saveToken, saveUser } from "@/lib/session";
import { getDemoCredentials, loginMock } from "@/lib/mock-auth";
import { useToast } from "@/components/ui/toast-provider";

export default function LoginPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const redirectTo = searchParams.get("redirect") || "/";
    const { showToast } = useToast();

    const [correo, setCorreo] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);

    const [errors, setErrors] = useState<{
        correo?: string;
        password?: string;
    }>({});

    useEffect(() => {
        const token = getToken();
        if (token) {
            router.replace(redirectTo);
        }
    }, [redirectTo, router]);

    function fillDemoAccount() {
        const demo = getDemoCredentials();
        setCorreo(demo.correo);
        setPassword(demo.password);

        showToast({
            type: "info",
            title: "Cuenta demo cargada",
            description: "Ya puedes ingresar con las credenciales locales.",
        });
    }

    async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();

        const newErrors: {
            correo?: string;
            password?: string;
        } = {};

        if (!correo.trim()) {
            newErrors.correo = "El correo es obligatorio";
        }

        if (!password.trim()) {
            newErrors.password = "La contraseña es obligatoria";
        }

        setErrors(newErrors);

        if (Object.keys(newErrors).length > 0) {
            showToast({
                type: "error",
                title: "Campos incompletos",
                description: "Completa el correo y la contraseña.",
            });
            return;
        }

        try {
            setLoading(true);

            const session = await loginMock(correo, password);

            saveToken(session.token);
            saveUser(session.user);

            showToast({
                type: "success",
                title: "Sesión iniciada",
                description: "Ingresando al panel principal.",
            });

            router.replace(redirectTo);
        } catch (error) {
            showToast({
                type: "error",
                title: "No se pudo iniciar sesión",
                description:
                    error instanceof Error
                        ? error.message
                        : "Credenciales incorrectas",
            });
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="flex min-h-screen items-center justify-center px-4 py-8">
            <div className="fixed right-3 top-3 z-50 sm:right-4 sm:top-4">
                <ThemeToggle className="h-9 w-9 rounded-xl opacity-90 sm:h-11 sm:w-11 sm:rounded-2xl sm:opacity-100" />
            </div>

            <div className="grid w-full max-w-5xl overflow-hidden rounded-[36px] border border-white/20 bg-white/65 shadow-[0_30px_80px_rgba(0,0,0,0.12)] backdrop-blur-xl dark:border-white/10 dark:bg-neutral-900/65 lg:grid-cols-[1.05fr_0.95fr]">
                <div className="hidden flex-col justify-between bg-[linear-gradient(180deg,rgba(246,177,26,0.22),rgba(246,177,26,0.06))] p-8 lg:flex">
                    <LogoMark />

                    <div className="max-w-md">
                        <span className="inline-flex items-center gap-2 rounded-full bg-white/60 px-3 py-1 text-xs font-semibold text-[var(--primary-strong)] dark:bg-white/5">
                            <Sparkles className="h-3.5 w-3.5" />
                            Acceso local de prueba
                        </span>

                        <h2 className="mt-4 text-4xl font-semibold tracking-tight">
                            Bienvenido a PIO AI
                        </h2>

                        <p className="mt-4 text-sm leading-7 text-[var(--muted-strong)]">
                            Este login funciona sin backend. Usa la cuenta demo local para
                            probar todo el frontend.
                        </p>
                    </div>
                </div>

                <div className="p-6 sm:p-8 lg:p-10">
                    <div className="mb-8 lg:hidden">
                        <LogoMark />
                    </div>

                    <div>
                        <p className="text-sm font-medium text-[var(--muted)]">
                            Inicio de sesión
                        </p>
                        <h1 className="mt-2 text-3xl font-semibold tracking-tight">
                            Accede a tu cuenta
                        </h1>
                        <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                            Introduce tu correo y contraseña o usa la cuenta demo.
                        </p>
                    </div>

                    <div className="mt-6 rounded-[24px] border border-white/20 bg-white/60 p-4 shadow-sm dark:border-white/10 dark:bg-white/5">
                        <p className="text-sm font-semibold text-[var(--foreground)]">
                            Cuenta demo local
                        </p>
                        <p className="mt-2 text-sm text-[var(--muted)]">
                            Correo: <span className="font-medium">admin@pioai.com</span>
                        </p>
                        <p className="text-sm text-[var(--muted)]">
                            Contraseña: <span className="font-medium">123456</span>
                        </p>

                        <button
                            type="button"
                            onClick={fillDemoAccount}
                            className="secondary-button mt-4 rounded-2xl px-4 py-2 text-sm font-medium transition duration-300 hover:-translate-y-0.5"
                        >
                            Usar cuenta demo
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="mt-8 space-y-5">
                        <div>
                            <label className="mb-2 block text-sm font-medium">Correo</label>
                            <div className="flex items-center gap-3 rounded-2xl border border-black/10 bg-white/80 px-4 py-3 dark:border-white/10 dark:bg-black/20">
                                <Mail className="h-4 w-4 text-[var(--muted)]" />
                                <input
                                    type="email"
                                    value={correo}
                                    onChange={(e) => setCorreo(e.target.value)}
                                    placeholder="correo@ejemplo.com"
                                    className="w-full bg-transparent text-sm outline-none placeholder:text-black/35 dark:placeholder:text-white/35"
                                />
                            </div>
                            {errors.correo ? (
                                <p className="mt-2 text-sm text-red-500">{errors.correo}</p>
                            ) : null}
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-medium">
                                Contraseña
                            </label>
                            <div className="flex items-center gap-3 rounded-2xl border border-black/10 bg-white/80 px-4 py-3 dark:border-white/10 dark:bg-black/20">
                                <LockKeyhole className="h-4 w-4 text-[var(--muted)]" />
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="********"
                                    className="w-full bg-transparent text-sm outline-none placeholder:text-black/35 dark:placeholder:text-white/35"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword((prev) => !prev)}
                                    className="text-[var(--muted)]"
                                >
                                    {showPassword ? (
                                        <EyeOff className="h-4 w-4" />
                                    ) : (
                                        <Eye className="h-4 w-4" />
                                    )}
                                </button>
                            </div>
                            {errors.password ? (
                                <p className="mt-2 text-sm text-red-500">{errors.password}</p>
                            ) : null}
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="primary-button inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 disabled:opacity-70"
                        >
                            <LogIn className="h-4 w-4" />
                            {loading ? "Ingresando..." : "Iniciar sesión"}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}