import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import AiPage from "./AiPage";
import "./dynamic-fas.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <AiPage />
  </StrictMode>,
);
