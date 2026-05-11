import { Briefcase } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function Jobs() {
  return (
    <div className="space-y-6 p-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Briefcase className="h-5 w-5 text-emerald-400" />
          <h1 className="text-xl font-semibold">Jobs</h1>
        </div>
        <Button size="sm">Scrape Now</Button>
      </div>
      <p className="text-sm text-zinc-500">
        Job listings will appear here. Use the filters to narrow results.
      </p>
    </div>
  );
}
