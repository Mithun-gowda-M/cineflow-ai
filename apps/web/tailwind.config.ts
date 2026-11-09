import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        cine: {
          black: "#0B0D13",
          surface: "#11141E",
          card: "#161B27",
          panel: "#1C2232",
          hover: "#242B3F",
          border: "rgba(229, 184, 105, 0.15)",
          borderBright: "rgba(229, 184, 105, 0.4)",
          gold: {
            300: "#FBE49D",
            400: "#F5D485",
            500: "#E5B869",
            600: "#D4A24E",
            700: "#A17426",
          },
          cyan: {
            300: "#7DD3FC",
            400: "#38BDF8",
            500: "#0EA5E9",
          },
          purple: {
            400: "#C084FC",
            500: "#A855F7",
          },
        },
      },
      backgroundImage: {
        "gold-gradient": "linear-gradient(135deg, #FBE49D 0%, #E5B869 50%, #B38634 100%)",
        "gold-glow": "radial-gradient(ellipse at center, rgba(229, 184, 105, 0.15) 0%, rgba(11, 13, 19, 0) 70%)",
        "cyan-glow": "radial-gradient(ellipse at center, rgba(56, 189, 248, 0.12) 0%, rgba(11, 13, 19, 0) 70%)",
      },
      boxShadow: {
        "gold-sm": "0 0 15px rgba(229, 184, 105, 0.2)",
        "gold-lg": "0 0 35px rgba(229, 184, 105, 0.35)",
        "cyan-sm": "0 0 15px rgba(56, 189, 248, 0.25)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        display: ["var(--font-cinematic)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
