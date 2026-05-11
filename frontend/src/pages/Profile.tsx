import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { AxiosError } from 'axios';
import { Loader2, Upload, User } from 'lucide-react';

import { apiClient } from '@/lib/api';
import { TagInput } from '@/components/TagInput';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';

interface ScoringCriteria {
  keywords: string[];
  exclude_keywords: string[];
  location: string;
  remote_preference: boolean;
  score_threshold: number;
}

interface ProfileData {
  id?: number;
  resume_text: string;
  notification_email: string;
  skills: string[];
  scoring_criteria: ScoringCriteria;
}

interface ParsedResume {
  resume_text: string;
  skills: string[];
  keywords: string[];
}

const DEFAULT_SCORING: ScoringCriteria = {
  keywords: [],
  exclude_keywords: [],
  location: '',
  remote_preference: false,
  score_threshold: 70,
};

const EMPTY_FORM: ProfileData = {
  resume_text: '',
  notification_email: '',
  skills: [],
  scoring_criteria: { ...DEFAULT_SCORING },
};

async function fetchProfile(): Promise<ProfileData | null> {
  try {
    const res = await apiClient.get<ProfileData>('/profile/');
    return res.data;
  } catch (e) {
    if ((e as AxiosError).response?.status === 404) return null;
    throw e;
  }
}

export function Profile() {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [form, setForm] = useState<ProfileData>(EMPTY_FORM);

  const { data: existingProfile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: fetchProfile,
    retry: false,
  });

  useEffect(() => {
    if (existingProfile) {
      setForm({
        ...existingProfile,
        scoring_criteria: { ...DEFAULT_SCORING, ...existingProfile.scoring_criteria },
      });
    }
  }, [existingProfile]);

  const parseMutation = useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData();
      body.append('file', file);
      const res = await apiClient.post<ParsedResume>('/profile/parse-resume', body);
      return res.data;
    },
    onSuccess: (data) => {
      setForm((prev) => ({
        ...prev,
        resume_text: data.resume_text,
        skills: data.skills,
        scoring_criteria: { ...prev.scoring_criteria, keywords: data.keywords },
      }));
      setSelectedFile(null);
      if (fileRef.current) fileRef.current.value = '';
    },
  });

  const saveMutation = useMutation({
    mutationFn: async (data: ProfileData) => {
      if (existingProfile) {
        const res = await apiClient.patch<ProfileData>('/profile/', data);
        return res.data;
      }
      const res = await apiClient.post<ProfileData>('/profile/', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
  });

  function setScoring<K extends keyof ScoringCriteria>(key: K, val: ScoringCriteria[K]) {
    setForm((prev) => ({
      ...prev,
      scoring_criteria: { ...prev.scoring_criteria, [key]: val },
    }));
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-emerald-400" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl space-y-6 p-8">
      <div className="flex items-center gap-2">
        <User className="h-5 w-5 text-emerald-400" />
        <h1 className="text-xl font-semibold">Profile</h1>
      </div>

      {/* Resume Upload */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Upload Resume</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-zinc-500">
            Upload a PDF, DOCX, or TXT file — AI will extract your skills and suggest scoring
            keywords.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
            />
            <Button variant="outline" size="sm" onClick={() => fileRef.current?.click()}>
              <Upload className="h-4 w-4" />
              Choose file
            </Button>
            {selectedFile && (
              <span className="max-w-[200px] truncate text-sm text-zinc-400">
                {selectedFile.name}
              </span>
            )}
            {selectedFile && (
              <Button
                size="sm"
                onClick={() => parseMutation.mutate(selectedFile)}
                disabled={parseMutation.isPending}
              >
                {parseMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Parsing…
                  </>
                ) : (
                  'Parse with AI'
                )}
              </Button>
            )}
          </div>
          {parseMutation.isError && (
            <p className="text-xs text-red-400">
              Parse failed — ensure your AI provider is configured in .env.
            </p>
          )}
          {parseMutation.isSuccess && (
            <p className="text-xs text-emerald-400">
              Parsed — review the extracted data below before saving.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Resume Text */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Resume Text</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={form.resume_text}
            onChange={(e) => setForm((prev) => ({ ...prev, resume_text: e.target.value }))}
            placeholder="Paste your resume here, or upload a file above to auto-populate…"
            className="min-h-[240px] font-mono text-xs leading-relaxed"
          />
        </CardContent>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Skills</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-xs text-zinc-500">
            Technical skills from your resume. These inform AI-generated documents.
          </p>
          <TagInput
            tags={form.skills}
            onChange={(tags) => setForm((prev) => ({ ...prev, skills: tags }))}
            placeholder="Add a skill…"
          />
        </CardContent>
      </Card>

      {/* Job Scoring */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Job Scoring</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <Label className="text-xs text-zinc-400">Include keywords</Label>
            <TagInput
              tags={form.scoring_criteria.keywords}
              onChange={(tags) => setScoring('keywords', tags)}
              placeholder="python, fastapi, senior engineer…"
            />
            <p className="text-xs text-zinc-600">Jobs matching these keywords score higher (up to 60 pts).</p>
          </div>

          <Separator />

          <div className="space-y-2">
            <Label className="text-xs text-zinc-400">Exclude keywords</Label>
            <TagInput
              tags={form.scoring_criteria.exclude_keywords}
              onChange={(tags) => setScoring('exclude_keywords', tags)}
              placeholder="unpaid, intern, 10+ years…"
            />
            <p className="text-xs text-zinc-600">Jobs matching any of these are scored zero.</p>
          </div>

          <Separator />

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="location" className="text-xs text-zinc-400">
                Preferred location
              </Label>
              <Input
                id="location"
                value={form.scoring_criteria.location}
                onChange={(e) => setScoring('location', e.target.value)}
                placeholder="San Francisco, CA"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="threshold" className="text-xs text-zinc-400">
                Score threshold (0–100)
              </Label>
              <Input
                id="threshold"
                type="number"
                min={0}
                max={100}
                value={form.scoring_criteria.score_threshold}
                onChange={(e) => setScoring('score_threshold', Number(e.target.value))}
              />
              <p className="text-xs text-zinc-600">
                Jobs at or above this score trigger document generation.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Switch
              id="remote"
              checked={form.scoring_criteria.remote_preference}
              onCheckedChange={(v) => setScoring('remote_preference', v)}
            />
            <Label htmlFor="remote" className="cursor-pointer text-sm">
              Prefer remote jobs
            </Label>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Notifications</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Label htmlFor="email" className="text-xs text-zinc-400">
            Notification email
          </Label>
          <Input
            id="email"
            type="email"
            value={form.notification_email}
            onChange={(e) => setForm((prev) => ({ ...prev, notification_email: e.target.value }))}
            placeholder="you@example.com"
          />
        </CardContent>
      </Card>

      {/* Save */}
      <div className="flex items-center gap-3 pb-8">
        <Button onClick={() => saveMutation.mutate(form)} disabled={saveMutation.isPending}>
          {saveMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving…
            </>
          ) : (
            'Save profile'
          )}
        </Button>
        {saveMutation.isSuccess && <span className="text-sm text-emerald-400">Saved.</span>}
        {saveMutation.isError && <span className="text-sm text-red-400">Save failed.</span>}
      </div>
    </div>
  );
}
