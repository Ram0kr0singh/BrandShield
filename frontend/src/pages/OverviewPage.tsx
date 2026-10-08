import React, { useCallback, useEffect, useState } from "react";
import { api, Brand, Overview } from "../api";
import { LoadingState } from "../components/common/LoadingState";
import { BrandSwitcher } from "../components/navigation/BrandSwitcher";
import { DigitalPerimeterBriefing } from "../components/overview/DigitalPerimeterBriefing";
import { PerimeterVisualization } from "../components/overview/PerimeterVisualization";
import { SourceSplit } from "../components/overview/SourceSplit";
import { IntelligenceLedger } from "../components/overview/IntelligenceLedger";
import { ThreatSummary } from "../components/overview/ThreatSummary";

export const OverviewPage: React.FC = () => {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [brandId, setBrandId] = useState("");
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  const [scanning, setScanning] = useState(false);

  const loadData = useCallback(async (id: string) => {
    setError("");
    setData(null);
    try {
      const res = await api.overview(id);
      setData(res);
    } catch {
      setError("Unable to load digital perimeter overview data from API.");
    }
  }, []);

  useEffect(() => {
    api
      .brands()
      .then((res) => {
        setBrands(res);
        const initial = res.find((b) => b.name.toLowerCase() === "nike") ?? res[0];
        if (initial) {
          setBrandId(initial.id);
          loadData(initial.id);
        }
      })
      .catch(() => setError("Unable to load protected brand targets."));
  }, [loadData]);

  const handleBrandChange = (id: string) => {
    setBrandId(id);
    loadData(id);
  };

  const handleScan = async () => {
    if (!brandId) return;
    setScanning(true);
    try {
      await api.scan(brandId);
      await loadData(brandId);
    } catch {
      setError("Perimeter scan execution failed.");
    } finally {
      setScanning(false);
    }
  };

  if (error) {
    return <LoadingState error={error} onRetry={() => loadData(brandId)} />;
  }

  if (!data) {
    return <LoadingState message="Initializing digital perimeter briefing..." />;
  }

  const { recent_threats } = data;

  return (
    <div className="space-y-4">
      {/* Brand Selector Header Bar */}
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-[var(--border-subtle)]">
        <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)] uppercase font-semibold">
          DIGITAL PERIMETER BRIEFING
        </span>
        <BrandSwitcher
          brands={brands}
          selectedId={brandId}
          onSelect={handleBrandChange}
          disabled={scanning}
        />
      </div>

      {/* 1. Briefing Executive Header & Large Threat Number */}
      <DigitalPerimeterBriefing
        overview={data}
        onScan={handleScan}
        scanning={scanning}
      />

      {/* 2. THE PERIMETER Signature Hero Visualization */}
      <PerimeterVisualization
        brandName={data.brand.name}
        threats={recent_threats}
      />

      {/* 3. Restrained Source Channel Split */}
      <SourceSplit overview={data} />

      {/* 4. Intelligence Ledger */}
      <IntelligenceLedger threats={recent_threats} />

      {/* 5. Demoted / Secondary Analytics (Charts below) */}
      <div className="pt-8 border-t border-[var(--border-subtle)]">
        <div className="mb-4">
          <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)] uppercase font-semibold">
            TELEMETRY DISTRIBUTION ANALYTICS
          </span>
        </div>
        <ThreatSummary overview={data} />
      </div>
    </div>
  );
};

