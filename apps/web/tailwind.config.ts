import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Warm beige/brown palette mirrored from cdss-training
        bg: {
          DEFAULT: "#FDFBF9", // page background
          surface: "#F4F3F1", // sidebar / card backgrounds
          muted: "#ede5e0",   // hover / subdued
        },
        brand: {
          50: "#FAF7F5",
          100: "#F4F3F1",
          200: "#ede5e0",
          300: "#D7CCC8",
          400: "#B79A8E",
          500: "#A1887F", // primary accent
          600: "#6f5a52", // darker accent
          700: "#5b483f",
        },
        ink: {
          DEFAULT: "#4a4441",
          soft: "#6b5f5b",
          muted: "#8a827e",
        },
        danger: {
          DEFAULT: "#9f403d",
          soft: "rgba(159,64,61,0.07)",
        },
      },
      fontFamily: {
        sans: ["Manrope", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 16px 48px -16px rgba(161,136,127,0.18)",
        cta: "0 24px 64px -16px rgba(161,136,127,0.15)",
      },
    },
  },
  plugins: [],
} satisfies Config;
