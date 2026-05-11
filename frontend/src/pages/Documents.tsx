import { FileText } from 'lucide-react';

export function Documents() {
  return (
    <div className="space-y-6 p-8">
      <div className="flex items-center gap-2">
        <FileText className="h-5 w-5 text-emerald-400" />
        <h1 className="text-xl font-semibold">Documents</h1>
      </div>
      <p className="text-sm text-zinc-500">
        AI-generated resumes and cover letters will appear here.
      </p>
    </div>
  );
}
