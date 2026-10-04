import { EmptyState } from "@/components/ui/states";

export function AssetChart({ assets }: { assets: Record<string, string | number | null | undefined>[] }) {
  const totals = new Map<string, number>();
  for (const asset of assets) { const type = String(asset.asset_type || "Unspecified"); totals.set(type, (totals.get(type) || 0) + 1); }
  const counts = [...totals].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const maximum = Math.max(1, ...counts.map(([, count]) => count));
  return <section className="panel asset-chart" aria-label="Asset types chart"><h3>Installed Asset Mix</h3><p>Current asset records by device type</p>{counts.length ? <div className="status-chart">{counts.map(([type, count]) => <div className="chart-row" key={type}><strong>{type}</strong><div className="chart-series"><span className="chart-bar visits" style={{ width: `${count / maximum * 100}%` }} /><span>{count}</span></div></div>)}</div> : <EmptyState title="No assets yet" description="Device types will appear when assets are added." />}<table className="sr-only"><caption>Asset counts by device type</caption><thead><tr><th>Device type</th><th>Count</th></tr></thead><tbody>{counts.map(([type, count]) => <tr key={type}><th>{type}</th><td>{count}</td></tr>)}</tbody></table></section>;
}
