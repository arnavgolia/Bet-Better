'use client';

import { useQuery } from '@tanstack/react-query';
import { gamesApi } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calendar, MapPin, TrendingUp, TrendingDown } from 'lucide-react';
import Link from 'next/link';

export default function Dashboard() {
  const { data: games, isLoading, error } = useQuery({
    queryKey: ['games', { upcoming: true }],
    queryFn: () => gamesApi.list({ upcoming: true }),
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading games...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Games</CardTitle>
            <CardDescription>
              {error instanceof Error ? error.message : 'Failed to fetch games'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Make sure the backend is running at http://localhost:8000
            </p>
            <Button onClick={() => window.location.reload()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold tracking-tight">SmartParlay</h1>
          <p className="text-muted-foreground mt-1">
            AI-Powered Same-Game Parlay Analytics
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold mb-2">Upcoming Games</h2>
          <p className="text-muted-foreground">
            Select a game to build an optimized parlay
          </p>
        </div>

        {games && games.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <p className="text-center text-muted-foreground">
                No upcoming games available. Check back later!
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {games?.map((game) => (
              <Card key={game.id} className="hover:border-primary/50 transition-colors">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg mb-1">
                        {game.away_team.name} @ {game.home_team.name}
                      </CardTitle>
                      <CardDescription className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        {new Date(game.commence_time).toLocaleDateString('en-US', {
                          weekday: 'short',
                          month: 'short',
                          day: 'numeric',
                          hour: 'numeric',
                          minute: '2-digit',
                        })}
                      </CardDescription>
                    </div>
                    <Badge variant={game.status === 'scheduled' ? 'default' : 'secondary'}>
                      {game.status}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Venue Info */}
                  {game.venue && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <MapPin className="w-4 h-4" />
                      {game.venue.name}
                      {game.venue.city && `, ${game.venue.city}`}
                    </div>
                  )}

                  {/* Betting Lines */}
                  <div className="grid grid-cols-2 gap-4">
                    {game.spread !== null && (
                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground font-medium">SPREAD</div>
                        <div className="flex items-center gap-1">
                          {game.spread > 0 ? (
                            <TrendingUp className="w-4 h-4 text-positive" />
                          ) : (
                            <TrendingDown className="w-4 h-4 text-negative" />
                          )}
                          <span className="font-semibold">
                            {game.spread > 0 ? '+' : ''}
                            {game.spread}
                          </span>
                        </div>
                      </div>
                    )}

                    {game.total !== null && (
                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground font-medium">TOTAL</div>
                        <div className="font-semibold">O/U {game.total}</div>
                      </div>
                    )}
                  </div>

                  {/* Weather Info */}
                  {(game.temperature_f || game.wind_mph) && (
                    <div className="text-xs text-muted-foreground">
                      {game.temperature_f && `${game.temperature_f}°F`}
                      {game.wind_mph && ` • Wind: ${game.wind_mph} mph`}
                      {game.precipitation_prob && ` • Precip: ${(game.precipitation_prob * 100).toFixed(0)}%`}
                    </div>
                  )}

                  {/* CTA Button */}
                  <Link href={`/parlay/${game.id}`} className="block">
                    <Button className="w-full" variant="default">
                      Build Parlay
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
