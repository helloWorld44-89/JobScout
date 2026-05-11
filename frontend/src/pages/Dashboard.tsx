import { LayoutDashboard } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';

const statCards = [
  { label: 'Total Jobs', value: '—' },
  { label: 'High Score Jobs', value: '—' },
  { label: 'Applied', value: '—' },
  { label: 'Docs Generated', value: '—' },
];

export function Dashboard() {
  return (
    <div className="flex h-full">
      {/* Main content */}
      <div className="flex-1 space-y-6 p-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <LayoutDashboard className="h-5 w-5 text-emerald-400" />
            <h1 className="text-xl font-semibold">Dashboard</h1>
          </div>
          <Button size="sm">Scrape Now</Button>
        </div>

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {statCards.map(({ label, value }) => (
            <Card key={label} className="border-zinc-800 bg-zinc-900">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-zinc-400">{label}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <p className="text-sm text-zinc-500">Last scrape: never</p>
      </div>

      {/* Notifications panel */}
      <aside className="w-80 border-l border-zinc-800 bg-zinc-900/50">
        <div className="flex h-14 items-center px-6">
          <h2 className="font-semibold text-zinc-300">High Score Jobs</h2>
        </div>
        <Separator />
        <div className="p-6">
          <p className="text-sm text-zinc-500">
            No high-score jobs yet. Run a scrape to get started.
          </p>
        </div>
      </aside>
    </div>
  );
}
