import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import { AppSidebar } from "./components/navigation/AppSidebar";

import { OverviewPage } from "./pages/OverviewPage";
import { BrandProfilePage } from "./pages/BrandProfilePage";
import { SocialMonitoringPage } from "./pages/SocialMonitoringPage";
import { AppMonitoringPage } from "./pages/AppMonitoringPage";
import { LookalikeDetectionPage } from "./pages/LookalikeDetectionPage";
import { ThreatsPage } from "./pages/ThreatsPage";
import { ThreatDetailPage } from "./pages/ThreatDetailPage";

import CheckName from "./CheckName";
import { SourceStatusNotice } from "./SourceStatus";

import "./styles.css";
import "./check.css";

function SocialPage() {
  return (
    <>
      <SourceStatusNotice kind="SOCIAL" />
      <SocialMonitoringPage />
    </>
  );
}

function AppsPage() {
  return (
    <>
      <SourceStatusNotice kind="APP" />
      <AppMonitoringPage />
    </>
  );
}

function App() {
  return (
    <div className="aegis-shell">
      <AppSidebar />

      <main className="aegis-content">
        <Routes>
          <Route path="/" element={<OverviewPage />} />

          <Route
            path="/profile"
            element={<BrandProfilePage />}
          />

          <Route
            path="/social"
            element={<SocialPage />}
          />

          <Route
            path="/apps"
            element={<AppsPage />}
          />

          <Route
            path="/lookalikes"
            element={<LookalikeDetectionPage />}
          />

          <Route
            path="/check"
            element={<CheckName />}
          />

          <Route
            path="/threats"
            element={<ThreatsPage />}
          />

          <Route
            path="/threats/:id"
            element={<ThreatDetailPage />}
          />

          <Route
            path="*"
            element={<OverviewPage />}
          />
        </Routes>
      </main>
    </div>
  );
}

const rootElement = document.getElementById("root");

if (rootElement) {
  createRoot(rootElement).render(
    <React.StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </React.StrictMode>,
  );
}