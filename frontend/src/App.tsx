import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";

const HomePage = lazy(() => import("./pages/HomePage"));
const WeatherPage = lazy(() => import("./pages/WeatherPage"));
const EnvironmentPage = lazy(() => import("./pages/EnvironmentPage"));
const HealthcarePage = lazy(() => import("./pages/HealthcarePage"));
const TransportPage = lazy(() => import("./pages/TransportPage"));
const TravelTimesPage = lazy(() => import("./pages/TravelTimesPage"));
const CamerasPage = lazy(() => import("./pages/CamerasPage"));
const CrowdingPage = lazy(() => import("./pages/CrowdingPage"));
const BusesPage = lazy(() => import("./pages/BusesPage"));
const NearbyPage = lazy(() => import("./pages/NearbyPage"));

function RouteLoading() {
  return (
    <div className="state-card route-loading" role="status">
      <span className="spinner" aria-hidden="true" />
      <strong>Opening dashboard view…</strong>
    </div>
  );
}

function NotFoundPage() {
  return (
    <section className="not-found">
      <p className="eyebrow">404</p>
      <h1>Page not found</h1>
      <p>The requested dashboard view does not exist.</p>
      <a className="button-link" href="/">Return to overview</a>
    </section>
  );
}

/** Renders the lazy-loaded application routes inside the shared layout. */
export function AppRoutes() {
  return (
    <Suspense fallback={<RouteLoading />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="weather/realtime" element={<WeatherPage />} />
          <Route path="environment" element={<EnvironmentPage />} />
          <Route path="healthcare" element={<HealthcarePage />} />
          <Route path="transport" element={<TransportPage />} />
          <Route path="transport/travel-times" element={<TravelTimesPage />} />
          <Route path="transport/cameras" element={<CamerasPage />} />
          <Route path="transit/crowding" element={<CrowdingPage />} />
          <Route path="transit/buses" element={<BusesPage />} />
          <Route path="nearby" element={<NearbyPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
