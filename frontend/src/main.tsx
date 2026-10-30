import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "leaflet/dist/leaflet.css";
import "./styles.css";
import App from "./App";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      gcTime: 10 * 60_000,
    },
  },
});

const root = document.getElementById("root");
if (!root) throw new Error("Application root element was not found.");

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
);
