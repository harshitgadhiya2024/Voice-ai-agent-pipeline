import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./store/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      keyframes: {
        pulseSoft: {
          "0%, 100%": { opacity: "0.5" },
          "50%": { opacity: "1" },
        },
        // Expanding ripple ring used while the mic is actively listening.
        micRipple: {
          "0%": { transform: "scale(1)", opacity: "0.55" },
          "80%": { transform: "scale(1.85)", opacity: "0" },
          "100%": { transform: "scale(1.85)", opacity: "0" },
        },
        // Breathing glow halo behind the mic.
        micGlow: {
          "0%, 100%": {
            transform: "scale(1)",
            opacity: "0.55",
            filter: "blur(18px)",
          },
          "50%": {
            transform: "scale(1.08)",
            opacity: "0.85",
            filter: "blur(24px)",
          },
        },
        // Mic icon micro-pulse synced to the breath.
        micPulse: {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.06)" },
        },
        // Soft fade-out used when the listening state ends.
        micFadeOut: {
          "0%": { opacity: "1" },
          "100%": { opacity: "0" },
        },
      },
      animation: {
        "pulse-soft": "pulseSoft 1.5s ease-in-out infinite",
        "mic-ripple": "micRipple 1.8s cubic-bezier(0.22,1,0.36,1) infinite",
        "mic-ripple-delay-1":
          "micRipple 1.8s cubic-bezier(0.22,1,0.36,1) -0.6s infinite",
        "mic-ripple-delay-2":
          "micRipple 1.8s cubic-bezier(0.22,1,0.36,1) -1.2s infinite",
        "mic-glow": "micGlow 2.4s ease-in-out infinite",
        "mic-pulse": "micPulse 1.2s ease-in-out infinite",
        "mic-fade-out": "micFadeOut 0.35s ease-out forwards",
      },
    },
  },
  plugins: [],
};

export default config;
