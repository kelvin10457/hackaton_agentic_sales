import Link from "next/link";
import { ArrowRight, GraduationCap, LayoutDashboard, ShieldCheck } from "lucide-react";

import { LogoMark, LogoWordmark } from "@/components/shared/logo";

const SUPERFICIES = [
  {
    href: "/chat",
    icono: GraduationCap,
    titulo: "Chat del prospecto",
    chip: "Público · sin registro",
    descripcion:
      "Aprende con contenido citado, haz el quiz de perfil de riesgo y recibe tu ruta de 3 pasos.",
  },
  {
    href: "/consola",
    icono: LayoutDashboard,
    titulo: "Consola del ejecutivo",
    chip: "Carlos Peña · Ejecutivo",
    descripcion:
      "Pipeline priorizado, score explicable y aprobación humana de cada comunicación.",
  },
];

export default function HomePage() {
  return (
    <main className="relative flex min-h-dvh flex-col items-center justify-center overflow-hidden bg-futuro-base px-6 py-14 text-white">
      {/* Resplandores de marca (decorativos) */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -left-32 -top-32 size-96 rounded-full bg-futuro-sky/20 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-40 -right-32 size-96 rounded-full bg-futuro-ia/15 blur-3xl"
      />

      <div className="relative flex w-full max-w-2xl flex-col items-center text-center">
        <div className="flex items-center gap-3">
          <LogoMark claro className="size-10 text-base" />
          <LogoWordmark invertido />
        </div>

        <h1 className="mt-8 text-balance text-3xl font-extrabold leading-tight tracking-tight sm:text-4xl">
          Educación financiera con un agente que sabe frenar
        </h1>
        <p className="mt-4 max-w-xl text-pretty text-sm leading-relaxed text-white/70 sm:text-base">
          Capta, califica y educa prospectos 24/7 — y ninguna comunicación sale sin la
          aprobación de un humano, con traza auditable de cada decisión.
        </p>

        <p className="mt-6 flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-4 py-1.5 text-xs font-medium text-white/80">
          <ShieldCheck className="size-3.5 text-futuro-sky" aria-hidden="true" />
          No es un chatbot con un CRM detrás: es un agente con frenos
        </p>

        <div className="mt-10 grid w-full gap-4 sm:grid-cols-2">
          {SUPERFICIES.map(({ href, icono: Icono, titulo, chip, descripcion }) => (
            <Link
              key={href}
              href={href}
              className="group flex flex-col rounded-2xl border border-white/10 bg-white/5 p-6 text-left transition-all duration-150 hover:border-futuro-sky/50 hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-futuro-sky"
            >
              <div className="flex items-center justify-between">
                <span className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-b from-futuro-sky to-futuro-accent/60 shadow-md">
                  <Icono className="size-5 text-white" aria-hidden="true" />
                </span>
                <ArrowRight
                  className="size-4 text-white/40 transition-transform duration-150 group-hover:translate-x-1 group-hover:text-futuro-sky"
                  aria-hidden="true"
                />
              </div>
              <h2 className="mt-4 text-base font-bold">{titulo}</h2>
              <p className="mt-1.5 flex-1 text-[13px] leading-relaxed text-white/65">
                {descripcion}
              </p>
              <span className="mt-4 w-fit rounded-full border border-white/15 bg-white/5 px-2.5 py-1 text-[11px] font-semibold text-white/70">
                {chip}
              </span>
            </Link>
          ))}
        </div>

        <p className="mt-12 text-[11px] text-white/40">
          Demo · Agentic Scale — Ecuador Tech Week 2026 · ESPOL
        </p>
      </div>
    </main>
  );
}
