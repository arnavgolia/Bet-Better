'use client';

import { useQuery } from '@tanstack/react-query';
import { gamesApi } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar, MapPin, TrendingUp, TrendingDown, Sparkles, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

export default function Dashboard() {
  const { data: games, isLoading, error } = useQuery({
    queryKey: ['games', { upcoming: true }],
    queryFn: () => gamesApi.list({ upcoming: true }),
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-500 mx-auto mb-6"></div>
          <p className="text-lg text-slate-400 font-medium">Loading games...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <Card className="max-w-md bg-slate-900 border-slate-800">
          <CardContent className="pt-6">
            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white text-center mb-2">Error Loading Games</h2>
            <p className="text-slate-400 text-center mb-6">
              {error instanceof Error ? error.message : 'Failed to fetch games'}
            </p>
            <div className="text-sm text-slate-500 text-center mb-4">
              Make sure the backend is running at <span className="font-mono text-blue-400">http://localhost:8000</span>
            </div>
            <Button
              onClick={() => window.location.reload()}
              className="w-full bg-blue-600 hover:bg-blue-500"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className="bg-gradient-to-b from-slate-900 to-slate-950 border-b border-slate-800">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-lg shadow-blue-600/30">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-4xl font-bold tracking-tight">SmartParlay</h1>
                <p className="text-slate-400 text-sm mt-0.5">AI-Powered Same-Game Parlay Analytics</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold mb-2">Upcoming Games</h2>
          <p className="text-slate-400">
            Select a game to build an AI-optimized parlay
          </p>
        </div>

        {games && games.length === 0 ? (
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="pt-16 pb-16 text-center">
              <div className="w-20 h-20 rounded-full bg-slate-800 mx-auto flex items-center justify-center mb-4">
                <Calendar className="w-10 h-10 text-slate-600" />
              </div>
              <p className="text-xl font-semibold text-white mb-2">
                No upcoming games
              </p>
              <p className="text-slate-400">
                Check back later for new games!
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {games?.map((game) => (
              <Card
                key={game.id}
                className="bg-slate-900 border-slate-800 hover:border-blue-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-blue-600/10 group overflow-hidden"
              >
                <CardContent className="p-0">
                  {/* Game Header */}
                  <div className="p-6 pb-4 relative">
                    {/* Status Badge */}
                    <div className="absolute top-4 right-4">
                      <span className={cn(
                        "px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide",
                        game.status === 'scheduled'
                          ? "bg-blue-950/50 text-blue-400 border border-blue-900/50"
                          : "bg-slate-800 text-slate-400"
                      )}>
                        {game.status}
                      </span>
                    </div>

                    {/* Teams */}
                    <div className="mb-4 pr-20">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center text-sm font-bold shadow-md">
                          {game.away_team.abbreviation.slice(0, 2)}
                        </div>
                        <div>
                          <div className="font-bold text-lg text-white">{game.away_team.name}</div>
                          <div className="text-xs text-slate-500">Away</div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-sm font-bold shadow-lg shadow-blue-600/20">
                          {game.home_team.abbreviation.slice(0, 2)}
                        </div>
                        <div>
                          <div className="font-bold text-lg text-white">{game.home_team.name}</div>
                          <div className="text-xs text-slate-500">Home</div>
                        </div>
                      </div>
                    </div>

                    {/* Date/Time */}
                    <div className="flex items-center gap-2 text-sm text-slate-400 mb-3">
                      <Calendar className="w-4 h-4" />
                      {new Date(game.commence_time).toLocaleDateString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                      })}
                    </div>

                    {/* Venue */}
                    {game.venue && (
                      <div className="flex items-center gap-2 text-sm text-slate-500">
                        <MapPin className="w-4 h-4" />
                        <span>{game.venue.name}</span>
                        {game.venue.city && <span className="text-slate-600">• {game.venue.city}</span>}
                      </div>
                    )}
                  </div>

                  {/* Betting Lines */}
                  {(game.spread !== null || game.total !== null) && (
                    <div className="px-6 pb-4">
                      <div className="grid grid-cols-2 gap-4 bg-slate-950/50 rounded-lg p-4 border border-slate-800">
                        {game.spread !== null && (
                          <div>
                            <div className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">
                              Spread
                            </div>
                            <div className="flex items-center gap-1.5">
                              {game.spread > 0 ? (
                                <TrendingUp className="w-4 h-4 text-green-500" />
                              ) : (
                                <TrendingDown className="w-4 h-4 text-red-500" />
                              )}
                              <span className="font-bold text-lg text-white">
                                {game.spread > 0 ? '+' : ''}{game.spread}
                              </span>
                            </div>
                          </div>
                        )}

                        {game.total !== null && (
                          <div>
                            <div className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">
                              Total
                            </div>
                            <div className="font-bold text-lg text-white">
                              O/U {game.total}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Weather Info */}
                  {(game.temperature_f || game.wind_mph) && (
                    <div className="px-6 pb-4">
                      <div className="text-xs text-slate-500 flex items-center gap-3">
                        {game.temperature_f && (
                          <span className="flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                            {game.temperature_f}°F
                          </span>
                        )}
                        {game.wind_mph && (
                          <span className="flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-600"></span>
                            Wind: {game.wind_mph} mph
                          </span>
                        )}
                        {game.precipitation_prob && (
                          <span className="flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                            {(game.precipitation_prob * 100).toFixed(0)}% precip
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* CTA Button */}
                  <div className="p-6 pt-4">
                    <Link href={`/parlay/${game.id}`} className="block">
                      <Button className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-bold py-6 shadow-lg shadow-blue-600/20 group-hover:shadow-blue-600/30 transition-all">
                        <Sparkles className="w-5 h-5 mr-2" />
                        Build Smart Parlay
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
