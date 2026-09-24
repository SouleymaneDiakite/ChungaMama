/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12222E",
        "ink-soft": "#4D6270",
        "blue-deep": "#164863",
        "blue-mid": "#2C7A9E",
        "blue-pale": "#E6F1F6",
        "blue-black": "#0B1826",
        paper: "#FBF8F2",
        gold: "#C98A2E",
        line: "#DCE6EA",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        body: ["IBM Plex Sans", "sans-serif"],
      },
    },
  },
  plugins: [],
};
