import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#155e75" },
    success: { main: "#15803d" },
    background: { default: "#f3f6f2" }
  },
  shape: { borderRadius: 8 }
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </StrictMode>
);
