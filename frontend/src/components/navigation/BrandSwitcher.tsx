import React from "react";
import { Brand } from "../../api";

interface BrandSwitcherProps {
  brands: Brand[];
  selectedId: string;
  onSelect: (id: string) => void;
  disabled?: boolean;
}

export const BrandSwitcher: React.FC<BrandSwitcherProps> = ({
  brands,
  selectedId,
  onSelect,
  disabled = false,
}) => {
  return (
    <div className="flex items-center gap-2">
      <label className="font-mono text-xs text-[var(--text-muted)] uppercase tracking-wider">
        Protected Brand:
      </label>
      <select
        value={selectedId}
        onChange={(e) => onSelect(e.target.value)}
        disabled={disabled}
        className="font-mono font-medium text-xs px-3 py-1.5 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-md text-[var(--text-primary)] cursor-pointer"
      >
        {brands.map((b) => (
          <option key={b.id} value={b.id}>
            {b.name}
          </option>
        ))}
      </select>
    </div>
  );
};
