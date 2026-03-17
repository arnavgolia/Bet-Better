'use client';

import { useState, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { gamesApi, playersApi, parlayApi } from '@/lib/api';
import type { ParlayLeg, PlayerMarginal, PropType } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  ArrowLeft,
  Calendar,
  MapPin,
  X,
  Sparkles,
  Trophy,
  CheckCircle2
} from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

// Helper to format odds (American format)
const formatOdds = (odds: number | undefined | null) => {
  if (odds === undefined || odds === null) return '-';
  return odds > 0 ? `+${odds}` : `${odds}`;
};

// Helper to get stat label
const getStatLabel = (statType: string) => {
  switch (statType) {
    case 'passing_yards': return 'Pass Yds';
    case 'passing_tds': return 'Pass TDs';
    case 'rushing_yards': return 'Rush Yds';
    case 'receiving_yards': return 'Rec Yds';
    case 'receptions': return 'Receptions';
    case 'anytime_tds': return 'Anytime TD';
    default: return statType.replace('_', ' ');
  }
};

const TAB_CATEGORIES = [
  { id: 'all', label: 'Popular' },
  { id: 'passing', label: 'Passing', stats: ['passing_yards', 'passing_tds'] },
  { id: 'rushing', label: 'Rushing', stats: ['rushing_yards'] },
  { id: 'receiving', label: 'Receiving', stats: ['receiving_yards', 'receptions'] },
  { id: 'scoring', label: 'TD Scorer', stats: ['anytime_tds'] },
];

export default function ParlayBuilder() {
  const params = useParams();
  const gameId = params.gameId as string;

  const [selectedLegs, setSelectedLegs] = useState<ParlayLeg[]>([]);
  const [activeTab, setActiveTab] = useState('all');

  // Fetch Game Details
  const { data: games } = useQuery({
    queryKey: ['games'],
    queryFn: () => gamesApi.list(),
  });
  const game = games?.find((g: any) => g.id === gameId);

  // Fetch Player Props (Marginals)
  const { data: marginals, isLoading, error } = useQuery({
    queryKey: ['game-props', gameId],
    queryFn: () => playersApi.getMarginals(gameId),
    enabled: !!gameId,
  });

  // Filter props based on active tab
  const filteredMarginals = useMemo(() => {
    if (!marginals) return [];
    if (activeTab === 'all') return marginals;

    const category = TAB_CATEGORIES.find(c => c.id === activeTab);
    if (!category || !('stats' in category)) return marginals;

    return marginals.filter(m => category.stats.includes(m.stat_type));
  }, [marginals, activeTab]);

  const addLeg = (leg: ParlayLeg) => {
    // Check if leg already exists (toggle behavior)
    if (selectedLegs.some((l) => l.player_id === leg.player_id && l.stat === leg.stat && l.direction === leg.direction)) {
      removeLeg(leg.player_id!, leg.stat!);
      return;
    }
    // Remove conflicting leg (same player same stat different direction)
    const newLegs = selectedLegs.filter(
      (l) => !(l.player_id === leg.player_id && l.stat === leg.stat)
    );
    setSelectedLegs([...newLegs, leg]);
  };

  const removeLeg = (playerId: string, stat: string) => {
    setSelectedLegs(selectedLegs.filter(
      (l) => !(l.player_id === playerId && l.stat === stat)
    ));
  };

  // Analysis Mutation
  const { mutate: analyzeParlay, isPending: isAnalyzing, data: analysisResult } = useMutation({
    mutationFn: (request: any) => parlayApi.generate(request),
    onError: (err) => {
      console.error("Analysis failed", err);
      alert("Analysis failed. Please try again.");
    }
  });

  const handleAnalyze = () => {
    if (!game) return;

    if (selectedLegs.length < 2) {
      alert("Please select at least 2 outcomes to analyze a parlay.");
      return;
    }

    // Construct request
    const request = {
      game_id: gameId,
      legs: selectedLegs.map(leg => ({
        type: leg.type,
        player_id: leg.player_id,
        stat: leg.stat,
        line: leg.line,
        direction: leg.direction,
        odds: leg.odds
      })),
      context: {
        weather: {
          wind_mph: game.wind_mph || 0,
          temp_f: game.temperature_f || 70,
          precip_prob: game.precipitation_prob || 0
        }
      },
      sportsbook: 'fanduel'
    };

    analyzeParlay(request);
  };

  if (!game) return <div className="p-8 text-center text-white">Loading game details...</div>;

  return (
    <div className="min-h-screen bg-slate-950 text-white pb-20">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <Link
            href="/"
            className="inline-flex items-center text-sm text-slate-400 hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Games
          </Link>

          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white mb-2">
                {game.away_team.name} @ {game.home_team.name}
              </h1>
              <div className="flex items-center gap-4 text-sm text-slate-400">
                <span className="flex items-center">
                  <Calendar className="w-4 h-4 mr-1" />
                  {new Date(game.commence_time).toLocaleDateString(undefined, {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
                <span className="flex items-center">
                  <MapPin className="w-4 h-4 mr-1" />
                  {game.venue?.name || 'TBD'}
                </span>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex overflow-x-auto gap-2 mt-6 pb-2 no-scrollbar">
            {TAB_CATEGORIES.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all",
                  activeTab === tab.id
                    ? "bg-white text-slate-950"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Props Selection Area */}
          <div className="lg:col-span-2 space-y-6">
            {!filteredMarginals || filteredMarginals.length === 0 ? (
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="pt-6 text-center text-slate-400">
                  <p>{isLoading ? "Loading props..." : "No props available for this category."}</p>
                  {error && <p className="text-red-500 mt-2">Error loading props: {(error as Error).message}</p>}

                  {/* Enhanced Debug Info */}
                  {!isLoading && (
                    <div className="mt-4 text-xs text-slate-500 text-left bg-slate-950 p-2 rounded border border-slate-800 font-mono">
                      <p className="font-bold text-slate-400 mb-1">Debug Info:</p>
                      <div>Game ID: {gameId}</div>
                      <div>Marginals Loaded: {marginals ? marginals.length : 'null'} ({activeTab} filtered: {filteredMarginals ? filteredMarginals.length : 0})</div>

                      {marginals && marginals.length > 0 && (
                        <div className="mt-2">
                          <p className="font-semibold text-slate-400">Available Stat Types:</p>
                          <div className="grid grid-cols-2 gap-1 mt-1">
                            {Array.from(new Set(marginals.map(m => m.stat_type))).map(st => (
                              <div key={st}>{st}</div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-6">
                {/* Organize by Team. 
                    NOTE: Using game.away_team and game.home_team from the game object.
                    Team ID must match what is in the marginal.player.team_id.
                */}
                {[game.away_team, game.home_team].map((team: any) => {
                  const teamProps = filteredMarginals.filter(m => m.player?.team_id === team.id);
                  if (teamProps.length === 0) return null;

                  return (
                    <div key={team.id} className="space-y-3">
                      <div className="flex items-center gap-2 px-1">
                        {/* Placeholder Logo */}
                        <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400">
                          {team.abbreviation[0]}
                        </div>
                        <h3 className="font-semibold text-lg">{team.name}</h3>
                      </div>

                      <div className="bg-slate-900 rounded-xl overflow-hidden border border-slate-800">
                        {/* Header Row */}
                        <div className="grid grid-cols-12 gap-4 px-4 py-3 bg-slate-900/50 border-b border-slate-800 text-xs font-medium text-slate-500 uppercase tracking-wider">
                          <div className="col-span-6">Player</div>
                          <div className="col-span-3 text-center">Over</div>
                          <div className="col-span-3 text-center">Under</div>
                        </div>

                        <div className="divide-y divide-slate-800">
                          {teamProps.map((marginal) => (
                            <PlayerPropRow
                              key={marginal.id}
                              marginal={marginal}
                              selectedLegs={selectedLegs}
                              onToggle={addLeg}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Parlay Slip Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-24">
              <Card className="bg-slate-900 border-slate-800 shadow-xl">
                <CardHeader className="border-b border-slate-800 pb-4">
                  <CardTitle className="flex items-center gap-2 text-white">
                    <Sparkles className="w-5 h-5 text-blue-400" />
                    Your Parlay
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-6">
                  {selectedLegs.length === 0 ? (
                    <div className="text-center text-slate-500 py-8">
                      <div className="w-16 h-16 rounded-full bg-slate-800 mx-auto flex items-center justify-center mb-4">
                        <Trophy className="w-8 h-8 text-slate-600" />
                      </div>
                      <p>Select outcome to add to your betslip</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {selectedLegs.map((leg, idx) => (
                        <div key={`${leg.player_id}-${leg.stat}`} className="bg-slate-950 p-3 rounded-lg border border-slate-800 relative group">
                          <button
                            onClick={() => removeLeg(leg.player_id!, leg.stat!)}
                            className="absolute top-2 right-2 text-slate-500 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <X className="w-4 h-4" />
                          </button>
                          <div className="font-medium text-sm text-white">{leg.player_name}</div>
                          <div className="text-sm text-slate-400">
                            {getStatLabel(leg.stat!)} <span className="text-blue-400 font-medium uppercase">{leg.direction} {leg.line}</span>
                          </div>
                          {leg.odds && (
                            <div className="text-xs text-slate-500 mt-1">Odds: {formatOdds(leg.odds)}</div>
                          )}
                        </div>
                      ))}

                      <Button
                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-6 mt-4 disabled:opacity-50"
                        onClick={handleAnalyze}
                        disabled={isAnalyzing}
                      >
                        {isAnalyzing ? (
                          <span className="flex items-center gap-2">
                            <Sparkles className="w-4 h-4 animate-spin" /> Analyzing...
                          </span>
                        ) : "Analyze Parlay"}
                      </Button>

                      {analysisResult && (
                        <div className="mt-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 text-center mb-3">
                            <div className="text-emerald-400 text-sm font-medium flex items-center justify-center gap-2">
                              <CheckCircle2 className="w-4 h-4" />
                              {analysisResult.recommended ? "Recommended" : "Analysis Complete"}
                            </div>
                          </div>

                          <dl className="grid grid-cols-2 gap-4 text-xs">
                            <div className="bg-slate-900 p-2 rounded">
                              <dt className="text-slate-500 mb-1">EV</dt>
                              <dd className={cn("text-lg font-bold", analysisResult.ev_pct > 0 ? "text-emerald-400" : "text-white")}>
                                {analysisResult.ev_pct > 0 ? '+' : ''}{analysisResult.ev_pct.toFixed(2)}%
                              </dd>
                            </div>
                            <div className="bg-slate-900 p-2 rounded">
                              <dt className="text-slate-500 mb-1">True Prob</dt>
                              <dd className="text-lg font-bold text-white">
                                {(analysisResult.true_probability * 100).toFixed(1)}%
                              </dd>
                            </div>
                          </dl>
                          {analysisResult.explanation && (
                            <div className="mt-3 text-xs text-slate-400 bg-slate-900 p-2 rounded">
                              <p className="font-medium text-white mb-1">Insight:</p>
                              {analysisResult.explanation.regime_reasoning}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// Redesigned Player Prop Row Component (FanDuel Style)
function PlayerPropRow({
  marginal,
  selectedLegs,
  onToggle,
}: {
  marginal: PlayerMarginal;
  selectedLegs: ParlayLeg[];
  onToggle: (leg: ParlayLeg) => void;
}) {
  if (!marginal.player) return null;

  const playerName = marginal.player.name || marginal.player.full_name;
  const statLabel = getStatLabel(marginal.stat_type);
  const line = marginal.line;

  const isOverSelected = selectedLegs.some(
    l => l.player_id === marginal.player!.id && l.stat === marginal.stat_type && l.direction === 'over'
  );

  const isUnderSelected = selectedLegs.some(
    l => l.player_id === marginal.player!.id && l.stat === marginal.stat_type && l.direction === 'under'
  );

  const showUnder = marginal.under_odds !== null && marginal.under_odds !== undefined;

  return (
    <div className="grid grid-cols-12 gap-4 px-4 py-4 items-center hover:bg-slate-800/50 transition-colors">

      {/* Player Section */}
      <div className="col-span-6 flex flex-col justify-center">
        <div className="font-semibold text-sm text-white">{playerName}</div>
        <div className="text-xs text-slate-500">{statLabel}</div>
      </div>

      {/* Over Button */}
      <div className={cn("col-span-3", !showUnder && "col-span-6")}>
        <button
          onClick={() => onToggle({
            type: 'player_prop',
            player_id: marginal.player!.id,
            player_name: playerName,
            stat: marginal.stat_type as PropType,
            direction: 'over',
            line: line,
            odds: marginal.over_odds || -110,
          })}
          className={cn(
            "w-full py-2 px-1 rounded-md border text-center transition-all duration-200",
            isOverSelected
              ? "bg-blue-600 border-blue-500 text-white shadow-[0_0_10px_rgba(37,99,235,0.5)]"
              : "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-600"
          )}
        >
          <div className="flex flex-col items-center leading-tight">
            <span className="text-xs font-bold">{showUnder ? 'O' : 'Yes'} {line}</span>
            <span className="text-[10px] opacity-80">{formatOdds(marginal.over_odds)}</span>
          </div>
        </button>
      </div>

      {/* Under Button (Optional for TD scorers) */}
      {showUnder ? (
        <div className="col-span-3">
          <button
            onClick={() => onToggle({
              type: 'player_prop',
              player_id: marginal.player!.id,
              player_name: playerName,
              stat: marginal.stat_type as PropType,
              direction: 'under',
              line: line,
              odds: marginal.under_odds || -110,
            })}
            className={cn(
              "w-full py-2 px-1 rounded-md border text-center transition-all duration-200",
              isUnderSelected
                ? "bg-blue-600 border-blue-500 text-white shadow-[0_0_10px_rgba(37,99,235,0.5)]"
                : "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-600"
            )}
          >
            <div className="flex flex-col items-center leading-tight">
              <span className="text-xs font-bold">U {line}</span>
              <span className="text-[10px] opacity-80">{formatOdds(marginal.under_odds)}</span>
            </div>
          </button>
        </div>
      ) : (
        <div className="col-span-0 hidden"></div>
      )}

    </div>
  );
}
