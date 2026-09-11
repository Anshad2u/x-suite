import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { IconArrowRight, IconCalendar, IconClock, IconChartBar, IconUsers, IconSearch, IconTarget, IconTrendingUp, IconDownload, IconFolder, IconAddressBook, IconActivity } from '@tabler/icons-react';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 dark:from-slate-900 dark:via-slate-950 dark:to-slate-900">
      <div className="container mx-auto px-4 py-20">
        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            X Growth Hub
          </h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
            Reverse-engineer Twitter/X growth strategies. Analyze any profile, score tweets,
            find winning patterns, and clone successful tactics for your own account.
          </p>
          <div className="bg-muted/30 rounded-xl p-6 max-w-2xl mx-auto mt-4">
            <p className="text-sm text-muted-foreground">
              👆 <strong>Get started</strong> by entering any X username above — no API keys needed!
            </p>
          </div>
        </div>

        {/* Beginner Step-by-Step Guide */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="p-6 bg-card rounded-lg border">
            <IconTarget className="w-8 h-8 mb-4 text-primary" />
            <h3 className="text-bold text-lg mb-2">Step 1: Audit Your Account</h3>
            <p className="text-muted-foreground">
              Enter your X username to analyze your tweet performance, engagement scores,
              and content patterns. Get personalized recommendations.
            </p>
          </div>
          <div className="p-6 bg-card rounded-lg border">
            <IconSearch className="w-8 h-8 mb-4 text-primary" />
            <h3 className="text-bold text-lg mb-2">Step 2: Analyze Competitors</h3>
            <p className="text-muted-foreground">
              Compare any public X account against yours. See their best-performing tweets,
              content types, and engagement strategies you can emulate.
            </p>
          </div>
          <div className="p-6 bg-card rounded-lg border">
            <IconTrendingUp className="w-8 h-8 mb-4 text-primary" />
            <h3 className="text-bold text-lg mb-2">Step 3: Clone Winning Patterns</h3>
            <p className="text-muted-foreground">
              Discover which tweet formats (questions, threads, hot takes) drive the most
              engagement. Generate a data-driven content calendar to post more of what works.
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-12">
          <Link href="/analyze">
            <Button size="lg" className="w-full h-24 flex-col gap-2">
              <IconSearch className="w-6 h-6" />
              Analyze Profile
            </Button>
          </Link>
          <Link href="/compare">
            <Button size="lg" variant="outline" className="w-full h-24 flex-col gap-2">
              <IconUsers className="w-6 h-6" />
              Compare Accounts
            </Button>
          </Link>
          <Link href="/my-account">
            <Button size="lg" variant="outline" className="w-full h-24 flex-col gap-2">
              <IconTarget className="w-6 h-6" />
              My Account Audit
            </Button>
          </Link>
          <Link href="/tools/calendar">
            <Button size="lg" variant="outline" className="w-full h-24 flex-col gap-2">
              <IconCalendar className="w-6 h-6" />
              Content Calendar
            </Button>
          </Link>
          <Link href="/tools/best-time">
            <Button size="lg" variant="outline" className="w-full h-24 flex-col gap-2">
              <IconClock className="w-6 h-6" />
              Best Time to Post
            </Button>
          </Link>
          <Link href="/tools/patterns">
            <Button size="lg" variant="outline" className="w-full h-24 flex-col gap-2">
              <IconTrendingUp className="w-6 h-6" />
              Pattern Recognition
            </Button>
          </Link>
          <Link href="/scrape">
            <Button size="lg" variant="outline" className="w-full h-24 flex-col gap-2">
              <IconDownload className="w-6 h-6" />
              Scrape Data
            </Button>
          </Link>
          <Link href="/groups">
            <Button size="lg" variant="outline" className="w-full h-24 flex-col gap-2">
              <IconFolder className="w-6 h-6" />
              Groups
            </Button>
          </Link>
          <Link href="/followers">
            <Button size="lg" variant="outline" className="w-full h-24 flex-col gap-2">
              <IconAddressBook className="w-6 h-6" />
              All Followers
            </Button>
          </Link>
          <Link href="/activity">
            <Button size="lg" variant="outline" className="w-full h-24 flex-col gap-2">
              <IconActivity className="w-6 h-6" />
              Activity
            </Button>
          </Link>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-16">
          <div className="p-6 bg-card rounded-lg border">
            <IconChartBar className="w-8 h-8 mb-4 text-primary" />
            <h3 className="text-xl font-semibold mb-2">Tweet Engagement Scoring</h3>
            <p className="text-muted-foreground">
              Score = (Replies×20) + (Reposts×2) + (Likes×0.5) + (Bookmarks×80).
              See exactly which of your tweets drive the most engagement.
            </p>
          </div>
          <div className="p-6 bg-card rounded-lg border">
            <IconSearch className="w-8 h-8 mb-4 text-primary" />
            <h3 className="text-xl font-semibold mb-2">Competitor Analysis</h3>
            <p className="text-muted-foreground">
              Analyze any X profile — see their best performing tweets, content patterns,
              and engagement strategies. Clone what works.
            </p>
          </div>
          <div className="p-6 bg-card rounded-lg border">
            <IconTrendingUp className="w-8 h-8 mb-4 text-primary" />
            <h3 className="text-xl font-semibold mb-2">Pattern Recognition</h3>
            <p className="text-muted-foreground">
              Identify which tweet types (questions, announcements, threads) perform
              best. Generate a content calendar based on winning patterns.
            </p>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <Link href="/analyze">
            <Button size="lg" className="gap-2">
              Start Analyzing <IconArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
