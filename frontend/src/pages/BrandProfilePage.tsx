import React, { useCallback, useEffect, useState } from "react";
import {
  api,
  Brand,
  BrandAsset,
  OfficialApp,
  OfficialSocial,
} from "../api";
import { LoadingState } from "../components/common/LoadingState";
import { BrandSwitcher } from "../components/navigation/BrandSwitcher";
import { Badge } from "../components/common/Badge";
import { PlatformIcon } from "../components/monitoring/PlatformIcon";
import { ShieldCheck, CheckCircle2, Globe, ExternalLink, Lock } from "lucide-react";

export const BrandProfilePage: React.FC = () => {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [brandId, setBrandId] = useState("");
  const [profile, setProfile] = useState<Brand | null>(null);
  const [social, setSocial] = useState<OfficialSocial[]>([]);
  const [apps, setApps] = useState<OfficialApp[]>([]);
  const [assets, setAssets] = useState<BrandAsset[]>([]);
  const [error, setError] = useState("");

  const loadBrandProfile = useCallback((id: string) => {
    setError("");
    setProfile(null);
    Promise.all([
      api.brand(id),
      api.brandSocial(id),
      api.brandApps(id),
      api.brandAssets(id),
    ])
      .then(([b, s, a, as]) => {
        setProfile(b);
        setSocial(s);
        setApps(a);
        setAssets(as);
      })
      .catch(() =>
        setError(
          "Unable to load protected brand identity baseline from backend."
        )
      );
  }, []);

  useEffect(() => {
    api
      .brands()
      .then((res) => {
        setBrands(res);
        const initial = res.find((b) => b.name.toLowerCase() === "nike") ?? res[0];
        if (initial) {
          setBrandId(initial.id);
          loadBrandProfile(initial.id);
        }
      })
      .catch(() => setError("Unable to load protected brands."));
  }, [loadBrandProfile]);

  const handleBrandChange = (id: string) => {
    setBrandId(id);
    loadBrandProfile(id);
  };

  if (error) {
    return <LoadingState error={error} onRetry={() => loadBrandProfile(brandId)} />;
  }

  if (!profile) {
    return <LoadingState message="Loading protected brand baseline identity dossier..." />;
  }

  return (
    <div className="space-y-6">
      {/* Switcher Bar */}
      <div className="flex items-center justify-between pb-4 border-b border-[var(--border-subtle)]">
        <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)] uppercase font-semibold">
          PROTECTED IDENTITY DOSSIER
        </span>
        <BrandSwitcher
          brands={brands}
          selectedId={brandId}
          onSelect={handleBrandChange}
        />
      </div>

      {/* Hero Dossier Certificate Header */}
      <div className="p-8 bg-[var(--bg-elevated)] border border-[var(--color-legitimate-border)] rounded-md relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Lock size={14} className="text-[var(--color-legitimate)]" />
              <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--color-legitimate)] uppercase font-semibold">
                ANCHORED IDENTITY BASELINE
              </span>
            </div>
            <h1 className="font-serif text-4xl md:text-5xl font-normal text-[var(--text-primary)]">
              {profile.name}
            </h1>
            <p className="text-xs font-mono text-[var(--text-muted)] max-w-2xl mt-2">
              {profile.description ||
                "Authoritative reference records used to protect this brand's official presence across global digital channels."}
            </p>
          </div>

          <Badge value="LEGITIMATE BASELINE" />
        </div>
      </div>

      {/* Two-Column Grid: Domains & Social Presence */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Official Domain & Logo Assets */}
        <div className="aegis-card">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-2">
              <Globe size={16} className="text-[var(--color-legitimate)]" />
              <span className="font-mono text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
                PRIMARY DOMAIN & ASSET BASELINE
              </span>
            </div>
            <span className="font-mono text-[10px] text-[var(--color-legitimate)]">VERIFIED</span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="p-3 bg-[var(--bg-elevated)] rounded border border-[var(--border-subtle)]">
              <span className="text-[10px] text-[var(--text-muted)] uppercase block">OFFICIAL REGISTERED DOMAIN</span>
              <p className="font-serif text-lg font-normal text-[var(--color-legitimate)] mt-0.5">
                {profile.official_domain || "Not recorded"}
              </p>
            </div>

            {assets.length > 0 ? (
              assets.map((ast) => (
                <div
                  key={ast.id}
                  className="p-3 bg-[var(--bg-elevated)] rounded border border-[var(--border-subtle)]"
                >
                  <span className="text-[10px] text-[var(--text-muted)] uppercase block">
                    {ast.asset_type.replaceAll("_", " ")}
                  </span>
                  <p className="text-[var(--text-primary)] mt-0.5">
                    {ast.label || ast.value}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-xs text-[var(--text-muted)]">No additional brand assets recorded.</p>
            )}
          </div>
        </div>

        {/* Official Social Accounts */}
        <div className="aegis-card">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-[var(--color-legitimate)]" />
              <span className="font-mono text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
                ANCHORED SOCIAL PRESENCE
              </span>
            </div>
            <span className="font-mono text-[10px] text-[var(--color-legitimate)]">{social.length} ACCOUNTS</span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            {social.length > 0 ? (
              social.map((acc) => (
                <div
                  key={acc.id}
                  className="p-3 bg-[var(--bg-elevated)] rounded border border-[var(--border-subtle)] flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <PlatformIcon platform={acc.platform} />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-[var(--text-primary)]">
                          {acc.display_name || acc.handle}
                        </span>
                        {acc.verified && (
                          <CheckCircle2 size={12} className="text-[var(--color-legitimate)]" />
                        )}
                      </div>
                      <span className="text-[11px] text-[var(--text-muted)]">
                        {acc.platform} · @{acc.handle}
                      </span>
                    </div>
                  </div>

                  <a
                    href={acc.profile_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  >
                    <ExternalLink size={14} />
                  </a>
                </div>
              ))
            ) : (
              <p className="text-xs text-[var(--text-muted)]">No official social accounts recorded.</p>
            )}
          </div>
        </div>
      </div>

      {/* Official Mobile Applications Baseline */}
      <div className="aegis-card">
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-2">
            <ShieldCheck size={16} className="text-[var(--color-legitimate)]" />
            <span className="font-mono text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
              AUTHORIZED APPLICATION DEVELOPER BASELINE
            </span>
          </div>
          <span className="font-mono text-[10px] text-[var(--color-legitimate)]">AUTHORITATIVE</span>
        </div>

        {apps.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {apps.map((app) => (
              <div
                key={app.id}
                className="p-4 bg-[var(--bg-elevated)] rounded border border-[var(--border-subtle)] font-mono text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-serif text-lg font-normal text-[var(--text-primary)]">
                    {app.app_name}
                  </span>
                  <Badge value="LEGITIMATE" />
                </div>
                <div>
                  <span className="text-[10px] text-[var(--text-muted)] uppercase block">
                    AUTHORIZED PUBLISHER / DEVELOPER
                  </span>
                  <p className="text-[var(--color-legitimate)] font-semibold mt-0.5">
                    {app.developer_name}
                  </p>
                </div>
                <div>
                  <span className="text-[10px] text-[var(--text-muted)] uppercase block">
                    PACKAGE IDENTIFIER
                  </span>
                  <p className="text-[var(--text-secondary)] mt-0.5">{app.package_identifier}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs font-mono text-[var(--text-muted)]">
            No official applications recorded for this protected brand.
          </p>
        )}
      </div>
    </div>
  );
};

