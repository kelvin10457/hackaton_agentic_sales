import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        futuro: {
          base: '#031B4E',
          corp: '#003E6B',
          bg: '#F4F5F6',
          accent: '#0084FF',
          alert: '#D900C7',
        },
      },
    },
  },
  plugins: [],
};
export default config;