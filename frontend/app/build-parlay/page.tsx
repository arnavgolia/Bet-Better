"use client";

import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sparkles, LayoutGrid } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

// Import the AI builder component
import AutoParlayBuilder from '@/components/AutoParlayBuilder';

export default function BuildParlayPage() {
  const [mode, setMode] = useState<'ai' | 'manual'>('ai');
  const router = useRouter();

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header with mode toggle */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Build Your Parlay</h1>
              <p className="text-sm text-slate-400 mt-1">
                Choose how you want to build your winning parlay
              </p>
            </div>

            {/* Mode Toggle */}
            <div className="flex gap-2 bg-slate-950 p-1 rounded-lg">
              <button
                onClick={() => setMode('ai')}
                className={`px-6 py-2.5 rounded-md font-semibold text-sm transition-all ${
                  mode === 'ai'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Sparkles className="w-4 h-4 inline-block mr-2" />
                AI Builder
              </button>
              <button
                onClick={() => setMode('manual')}
                className={`px-6 py-2.5 rounded-md font-semibold text-sm transition-all ${
                  mode === 'manual'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <LayoutGrid className="w-4 h-4 inline-block mr-2" />
                Sportsbook
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {mode === 'ai' ? (
          <AutoParlayBuilder />
        ) : (
          <ManualBuilder />
        )}
      </div>
    </div>
  );
}

// Manual builder component (shows games to select)
function ManualBuilder() {
  const router = useRouter();

  // For now, fetch games from the API
  const [games, setGames] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch games on mount
  useState(() => {
    fetch('/api/v1/games/upcoming')
      .then(res => res.json())
      .then(data => {
        setGames(data.games || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching games:', err);
        setLoading(false);
      });
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-slate-400">Loading games...</div>
      </div>
    );
  }

  if (games.length === 0) {
    return (
      <Card className="bg-slate-900 border-slate-800">
        <CardContent className="py-20 text-center">
          <LayoutGrid className="w-16 h-16 text-slate-700 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Games Available</h3>
          <p className="text-slate-400 mb-6">
            Check back soon for upcoming games
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold text-white mb-2">Select a Game</h2>
        <p className="text-slate-400">Choose a game to start building your parlay</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {games.map((game) => (
          <Link key={game.id} href={`/parlay/${game.id}`}>
            <Card className="bg-slate-900 border-slate-800 hover:border-blue-500/50 transition-all cursor-pointer hover:shadow-xl hover:shadow-blue-600/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                    {game.sport}
                  </span>
                  <span className="text-xs text-slate-500">
                    {new Date(game.commence_time).toLocaleDateString()}
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center text-sm font-bold shadow-md">
                      {game.away_team?.abbreviation || 'A'}
                    </div>
                    <div>
                      <div className="font-bold text-white">{game.away_team?.name || 'Away Team'}</div>
                      <div className="text-xs text-slate-500">Away</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center text-sm font-bold shadow-md">
                      {game.home_team?.abbreviation || 'H'}
                    </div>
                    <div>
                      <div className="font-bold text-white">{game.home_team?.name || 'Home Team'}</div>
                      <div className="text-xs text-slate-500">Home</div>
                    </div>
                  </div>
                </div>

                {game.spread !== null && (
                  <div className="mt-4 pt-4 border-t border-slate-800">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Spread: {game.spread > 0 ? '+' : ''}{game.spread}</span>
                      {game.total && <span className="text-slate-500">O/U: {game.total}</span>}
                    </div>
                  </div>
                )}

                <Button className="w-full mt-4 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-semibold">
                  <Sparkles className="w-4 h-4 mr-2" />
                  Build Parlay
                </Button>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
