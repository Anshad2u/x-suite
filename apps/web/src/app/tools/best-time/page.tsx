'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { IconClock, IconSearch } from '@tabler/icons-react';
import { analyzeProfile, type AnalysisResult } from '@/lib/api';
import { getHourHistogram, getDayHistogram, type HourSlot, type DaySlot } from '@/lib/analytics';

const DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function BestTimePage() {
  const [username, setUsername] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<AnalysisResult | null>(null);

  const run = async () => {
    if (!username.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeProfile(username.trim());
      setResult(data);
    } catch (e: any) {
      setError(e?.message || 'Failed to analyze profile');
    } finally {
      setLoading(false);
    }
  };

  const hours: HourSlot[] = result ? getHourHistogram(result.tweets) : [];
  const days: DaySlot[] = result ? getDayHistogram(result.tweets) : [];
  const maxAvg = Math.max(...hours.map((h) => h.avgScore), 1);
  const maxDay = Math.max(...days.map((d) => d.avgScore), 1);

  return (
    <div className='container mx-auto max-w-7xl py-8'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold mb-2'>Best Time to Post</h1>
        <p className='text-muted-foreground'>
          Heatmap of engagement score by posting hour and day, from real scraped tweets.
        </p>
      </div>

      <div className='flex gap-2 mb-6'>
        <Input
          placeholder='Enter username'
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && run()}
          className='max-w-md'
        />
        <Button onClick={run} disabled={loading || !username.trim()}>
          <IconSearch className='w-4 h-4 mr-2' />
          {loading ? 'Analyzing…' : 'Analyze Times'}
        </Button>
      </div>

      {loading && <Skeleton className='h-64 w-full' />}

      {error && (
        <Card className='mb-6 border-destructive'>
          <CardContent className='pt-6 text-sm text-destructive'>{error}</CardContent>
        </Card>
      )}

      {!loading && hours.length > 0 && (
        <div className='space-y-6'>
          <Card>
            <CardHeader>
              <CardTitle className='flex items-center gap-2'>
                <IconClock className='w-5 h-5 text-primary' />
                Score by hour — @{result?.username}
              </CardTitle>
              <CardDescription>Darker = higher average engagement score</CardDescription>
            </CardHeader>
            <CardContent>
              <div className='flex items-end gap-1 h-40'>
                {hours.map((h) => (
                  <div key={h.hour} className='flex-1 flex flex-col items-center justify-end h-full group relative'>
                    <div
                      className='w-full rounded-t bg-primary'
                      style={{ height: `${Math.max((h.avgScore / maxAvg) * 100, 2)}%`, opacity: 0.35 + (h.avgScore / maxAvg) * 0.65 }}
                    />
                    <span className='text-[9px] text-muted-foreground mt-1'>
                      {h.hour % 3 === 0 ? h.label : ''}
                    </span>
                    <div className='absolute bottom-full mb-1 hidden group-hover:block bg-popover border rounded px-2 py-1 text-xs whitespace-nowrap z-10'>
                      {h.label}: {h.tweets} tweets, avg {Math.round(h.avgScore).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Score by day of week</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='space-y-2'>
                {DAY_ORDER.map((dayName) => {
                  const d = days.find((x) => x.day === dayName);
                  if (!d) return null;
                  return (
                    <div key={dayName} className='flex items-center gap-3'>
                      <span className='w-24 text-sm text-muted-foreground'>{dayName}</span>
                      <div className='flex-1 h-6 bg-muted rounded overflow-hidden'>
                        <div
                          className='h-full bg-primary rounded'
                          style={{ width: `${Math.max((d.avgScore / maxDay) * 100, 1)}%`, opacity: 0.4 + (d.avgScore / maxDay) * 0.6 }}
                        />
                      </div>
                      <span className='w-40 text-xs text-muted-foreground text-right'>
                        {d.tweets} tweets · avg {Math.round(d.avgScore).toLocaleString()}
                      </span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {!loading && !error && hours.length === 0 && (
        <Card>
          <CardContent className='py-10 text-center text-sm text-muted-foreground'>
            Enter a username to see when their audience engages most.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
