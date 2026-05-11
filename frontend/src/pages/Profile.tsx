import { User } from 'lucide-react';

export function Profile() {
  return (
    <div className="space-y-6 p-8">
      <div className="flex items-center gap-2">
        <User className="h-5 w-5 text-emerald-400" />
        <h1 className="text-xl font-semibold">Profile</h1>
      </div>
      <p className="text-sm text-zinc-500">
        Configure your resume, skills, and scoring criteria here.
      </p>
    </div>
  );
}
