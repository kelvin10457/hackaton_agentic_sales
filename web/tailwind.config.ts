import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "var(--font-sans)",
          "Inter",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
      },
      colors: {
        // Tokens semánticos (shadcn) — definidos como variables HSL en globals.css
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        // Paleta de marca Futuro (hex oficiales del brandbook)
        futuro: {
          base: "#031B4E", // azul oscuro principal
          corp: "#003E6B", // azul corporativo profundo
          sky: "#4BA3E3", // celeste del isotipo (inicio del degradado)
          accent: "#0084FF", // azul brillante / CTA
          ia: "#5A17F5", // violeta — reservado para "razonamiento del agente"
          magenta: "#D900C7", // magenta — uso puntual de marca
          bg: "#F4F5F6", // gris claro de fondo
        },
        // Colores de banda — MISMOS HEX en chat y consola (regla de consistencia #1)
        banda: {
          caliente: "#EF4444",
          tibio: "#F59E0B",
          frio: "#3B82F6",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.96)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "toast-in": {
          from: { opacity: "0", transform: "translateY(10px) scale(0.98)" },
          to: { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        "slide-in-right": {
          from: { opacity: "0", transform: "translateX(24px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
      },
      animation: {
        // Transiciones cortas (~150–200 ms): se graban bien en vídeo
        "fade-up": "fade-up 0.2s ease-out both",
        "fade-in": "fade-in 0.15s ease-out both",
        "scale-in": "scale-in 0.15s ease-out both",
        "toast-in": "toast-in 0.2s ease-out both",
        "slide-in-right": "slide-in-right 0.2s ease-out both",
      },
    },
  },
  plugins: [],
};
export default config;
