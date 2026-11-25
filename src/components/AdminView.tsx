import { useEffect, useState } from 'react';
import { cloud } from '../cloud';

interface Props {isAdmin: boolean; signedIn: boolean;}
type Metrics = {counts: Record<string, number>; totalOriginalBytes: number; bytesSaved: number; failureRate: number; averageLatencyMs: number};

export function AdminView({isAdmin, signedIn}: Props) {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    if (!isAdmin) return;
    const load = () => cloud.metrics().then(setMetrics).catch(err => setError(err.message));
    load();
    const timer = window.setInterval(load, 10000);
    return () => window.clearInterval(timer);
  }, [isAdmin]);
  if (!signedIn || !isAdmin) return <div className="mx-auto max-w-xl p-8 text-center bg-white/70 rounded-2xl border border-neutral-300"><h2 className="text-xl font-semibold">Admin dashboard</h2><p className="text-sm text-neutral-600 mt-2">{signedIn ? 'Your account does not have admin access.' : 'Sign in with an admin account to see pipeline metrics.'}</p></div>;
  const total = Object.values(metrics?.counts || {}).reduce((a, b) => a + b, 0);
  const values = [['Total files', total], ['Completed', metrics?.counts.completed || 0], ['Processing', (metrics?.counts.processing || 0) + (metrics?.counts.pending || 0)], ['Failed', metrics?.counts.failed || 0], ['Failure rate', `${metrics?.failureRate || 0}%`], ['Average latency', `${((metrics?.averageLatencyMs || 0) / 1000).toFixed(1)} s`], ['Storage saved', `${((metrics?.bytesSaved || 0) / 1024 / 1024).toFixed(2)} MB`]];
  return <div className="mx-auto w-full max-w-5xl px-4 py-8"><h2 className="text-2xl font-bold">Pipeline overview</h2><p className="text-sm text-neutral-600 mt-1">Live totals from DynamoDB, refreshed every 10 seconds.</p>{error && <p role="alert" className="mt-4 text-red-700">{error}</p>}<div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">{values.map(([label, value]) => <div key={label} className="p-5 bg-white/85 rounded-2xl border border-neutral-300 shadow-sm"><p className="text-xs text-neutral-500">{label}</p><p className="text-2xl font-bold mt-2">{value}</p></div>)}</div><p className="mt-6 text-xs text-neutral-600">Metrics cover records currently retained in the CloudLens table.</p></div>;
}
