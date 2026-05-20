import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./content/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "deep-space": {
          900: "#050914",
          800: "#0A0F1E",
          700: "#0F1A2E",
          600: "#152540",
        },
        gold: {
          300: "#F0E0A0",
          400: "#E8CC80",
          500: "#D4AF37",
          600: "#B8960F",
          700: "#8C7200",
        },
        crystal: {
          100: "rgba(255, 255, 255, 0.05)",
          200: "rgba(255, 255, 255, 0.08)",
          300: "rgba(255, 255, 255, 0.12)",
          400: "rgba(255, 255, 255, 0.2)",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
      backdropBlur: {
        glass: "20px",
        "glass-heavy": "40px",
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        glow: "glow 2s ease-in-out infinite alternate",
        "slide-up": "slideUp 0.6s ease-out",
        "fade-in": "fadeIn 0.8s ease-out",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-14px)" },
        },
        glow: {
          "0%": { boxShadow: "0 0 20px rgba(212, 175, 55, 0.3)" },
          "100%": { boxShadow: "0 0 40px rgba(212, 175, 55, 0.55)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(30px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
