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
  CheckCircle2,
  Search,
  AlertCircle,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

// Helper to format odds (American format)
const formatOdds = (odds: number | undefined | null) => {
  if (odds === undefined || odds === null) return '-';
  return odds > 0 ? `+${odds}` : `${odds}`;
};

// Helper to calculate parlay odds from individual legs
const calculateParlayOdds = (legs: ParlayLeg[]) => {
  if (legs.length === 0) return 0;

  let totalDecimalOdds = 1;
  legs.forEach(leg => {
    const odds = leg.odds || -110;
    // Convert American odds to decimal
    const decimal = odds > 0 ? (odds / 100) + 1 : (100 / Math.abs(odds)) + 1;
    totalDecimalOdds *= decimal;
  });

  // Convert back to American odds
  if (totalDecimalOdds >= 2) {
    return Math.round((totalDecimalOdds - 1) * 100);
  } else {
    return Math.round(-100 / (totalDecimalOdds - 1));
  }
};

// Helper to get stat label
const getStatLabel = (statType: string) => {
  const labels: Record<string, string> = {
    'passing_yards': 'Passing Yards',
    'passing_tds': 'Passing TDs',
    'rushing_yards': 'Rushing Yards',
    'receiving_yards': 'Receiving Yards',
    'receptions': 'Receptions',
    'anytime_tds': 'Anytime TD Scorer',
  };
  return labels[statType] || statType.replace(/_/g, ' ');
};

// Helper to get short stat label
const getShortStatLabel = (statType: string) => {
  const labels: Record<string, string> = {
    'passing_yards': 'Pass Yds',
    'passing_tds': 'Pass TDs',
    'rushing_yards': 'Rush Yds',
    'receiving_yards': 'Rec Yds',
    'receptions': 'Receptions',
    'anytime_tds': 'Anytime TD',
  };
  return labels[statType] || statType;
};

// Position badge component
const PositionBadge = ({ position }: { position: string }) => {
  const colors: Record<string, string> = {
    'QB': 'bg-red-900/30 text-red-300 border-red-700/50',
    'RB': 'bg-green-900/30 text-green-300 border-green-700/50',
    'WR': 'bg-blue-900/30 text-blue-300 border-blue-700/50',
    'TE': 'bg-yellow-900/30 text-yellow-300 border-yellow-700/50',
    'K': 'bg-purple-900/30 text-purple-300 border-purple-700/50',
  };

  const colorClass = colors[position] || 'bg-slate-800 text-slate-400 border-slate-700';

  return (
    <span className={cn('px-1.5 py-0.5 rounded text-[10px] font-bold border', colorClass)}>
      {position}
    </span>
  );
};

const TAB_CATEGORIES = [
  { id: 'popular', label: 'Popular', icon: Trophy },
  { id: 'passing', label: 'Passing', stats: ['passing_yards', 'passing_tds'] },
  { id: 'rushing', label: 'Rushing', stats: ['rushing_yards'] },
  { id: 'receiving', label: 'Receiving', stats: ['receiving_yards', 'receptions'] },
  { id: 'scoring', label: 'TD Scorer', stats: ['anytime_tds'] },
];

export default function ParlayBuilder() {
  const params = useParams();
  const gameId = params.gameId as string;

  const [selectedLegs, setSelectedLegs] = useState<ParlayLeg[]>([]);
  const [activeTab, setActiveTab] = useState('popular');
  const [searchQuery, setSearchQuery] = useState('');

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

  // Filter and search props
  const filteredMarginals = useMemo(() => {
    if (!marginals) return [];

    let filtered = marginals;

    // Tab filtering
    if (activeTab !== 'popular') {
      const category = TAB_CATEGORIES.find(c => c.id === activeTab);
      if (category && 'stats' in category && category.stats) {
        filtered = filtered.filter(m => category.stats.includes(m.stat_type));
      }
    }

    // Search filtering
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(m =>
        m.player?.name?.toLowerCase().includes(query) ||
        m.player?.position?.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [marginals, activeTab, searchQuery]);

  const addLeg = (leg: ParlayLeg) => {
    // Check if exact same leg exists (toggle off)
    const exactMatch = selectedLegs.find(
      l => l.player_id === leg.player_id && l.stat === leg.stat && l.direction === leg.direction
    );

    if (exactMatch) {
      setSelectedLegs(selectedLegs.filter(l => l !== exactMatch));
      return;
    }

    // Remove conflicting leg (same player, same stat, different direction)
    const withoutConflict = selectedLegs.filter(
      l => !(l.player_id === leg.player_id && l.stat === leg.stat)
    );

    setSelectedLegs([...withoutConflict, leg]);
  };

  const removeLeg = (leg: ParlayLeg) => {
    setSelectedLegs(selectedLegs.filter(l => l !== leg));
  };

  const clearBetslip = () => {
    setSelectedLegs([]);
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

  if (!game) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center text-slate-400">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Loading game details...</p>
        </div>
      </div>
    );
  }

  const parlayOdds = calculateParlayOdds(selectedLegs);

  return (
    <div className="min-h-screen bg-slate-950 text-white pb-32">
      {/* Sticky Header */}
      <div className="bg-slate-900 border-b border-slate-800 sticky top-0 z-20 shadow-xl">
        <div className="container mx-auto px-4 py-4">
          {/* Back Button */}
          <Link
            href="/"
            className="inline-flex items-center text-sm text-slate-400 hover:text-white mb-4 transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 mr-1 group-hover:-translate-x-1 transition-transform" />
            Back to Games
          </Link>

          {/* Game Header */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
            <div>
              <h1 className="text-2xl font-bold text-white mb-2">
                {game.away_team.name} @ {game.home_team.name}
              </h1>
              <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400">
                <span className="flex items-center">
                  <Calendar className="w-4 h-4 mr-1.5" />
                  {new Date(game.commence_time).toLocaleDateString(undefined, {
                    weekday: 'long',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
                {game.venue && (
                  <span className="flex items-center">
                    <MapPin className="w-4 h-4 mr-1.5" />
                    {game.venue.name}
                  </span>
                )}
              </div>
            </div>

            {/* Quick Game Stats */}
            <div className="flex gap-4 text-sm">
              {game.spread !== null && (
                <div className="text-center">
                  <div className="text-slate-500 text-xs mb-1">Spread</div>
                  <div className="font-semibold">{game.spread > 0 ? '+' : ''}{game.spread}</div>
                </div>
              )}
              {game.total !== null && (
                <div className="text-center">
                  <div className="text-slate-500 text-xs mb-1">Total</div>
                  <div className="font-semibold">O/U {game.total}</div>
                </div>
              )}
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex overflow-x-auto gap-2 pb-2 no-scrollbar">
            {TAB_CATEGORIES.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "px-5 py-2.5 rounded-lg text-sm font-semibold whitespace-nowrap transition-all duration-200 flex items-center gap-2",
                  activeTab === tab.id
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-600/30"
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
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Props Selection Area */}
          <div className="lg:col-span-2 space-y-6">

            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
              <input
                type="text"
                placeholder="Search players..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-11 pr-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Props List */}
            {isLoading ? (
              <div className="text-center py-16">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-slate-400">Loading player props...</p>
              </div>
            ) : error ? (
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="pt-6 text-center">
                  <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                  <p className="text-red-400 font-semibold mb-2">Error Loading Props</p>
                  <p className="text-slate-400 text-sm">{(error as Error).message}</p>
                </CardContent>
              </Card>
            ) : filteredMarginals.length === 0 ? (
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="pt-6 text-center py-16">
                  <Trophy className="w-16 h-16 text-slate-700 mx-auto mb-4" />
                  {searchQuery ? (
                    <>
                      <p className="text-slate-300 font-semibold mb-2">No players found</p>
                      <p className="text-slate-500 text-sm">Try a different search term</p>
                    </>
                  ) : (
                    <>
                      <p className="text-slate-300 font-semibold mb-2">
                        {activeTab === 'scoring' ? 'No TD Scorer props available' : 'No props available'}
                      </p>
                      <p className="text-slate-500 text-sm">
                        {activeTab === 'scoring'
                          ? 'Touchdown scorer props may not be available for this game yet'
                          : 'Try selecting a different category'
                        }
                      </p>

                      {/* Debug info for TD Scorer */}
                      {activeTab === 'scoring' && marginals && marginals.length > 0 && (
                        <div className="mt-6 text-xs text-slate-600 text-left bg-slate-950/50 p-4 rounded border border-slate-800 font-mono max-w-md mx-auto">
                          <p className="font-bold text-slate-500 mb-2">Debug Info:</p>
                          <div className="space-y-1">
                            <div>Total props loaded: {marginals.length}</div>
                            <div>Available stat types:</div>
                            <div className="pl-2 text-slate-500">
                              {Array.from(new Set(marginals.map(m => m.stat_type))).join(', ')}
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-8">
                {/* Group by Team */}
                {[game.away_team, game.home_team].map((team: any) => {
                  const teamProps = filteredMarginals.filter(m => m.player?.team_id === team.id);
                  if (teamProps.length === 0) return null;

                  return (
                    <div key={team.id} className="space-y-4">
                      {/* Team Header */}
                      <div className="flex items-center gap-3 px-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-sm font-bold shadow-lg">
                          {team.abbreviation.slice(0, 2)}
                        </div>
                        <h3 className="font-bold text-xl">{team.name}</h3>
                        <span className="text-slate-500 text-sm">({teamProps.length})</span>
                      </div>

                      {/* Player Props */}
                      <div className="space-y-3">
                        {teamProps.map((marginal) => (
                          <ImprovedPropCard
                            key={marginal.id}
                            marginal={marginal}
                            selectedLegs={selectedLegs}
                            onToggle={addLeg}
                          />
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Enhanced Betslip Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-24">
              <Card className="bg-slate-900 border-slate-800 shadow-2xl">
                <CardHeader className="border-b border-slate-800 pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-white">
                      <Sparkles className="w-5 h-5 text-blue-400" />
                      Betslip ({selectedLegs.length})
                    </CardTitle>
                    {selectedLegs.length > 0 && (
                      <button
                        onClick={clearBetslip}
                        className="text-xs text-slate-500 hover:text-white transition-colors"
                      >
                        Clear All
                      </button>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="pt-6">
                  {selectedLegs.length === 0 ? (
                    <div className="text-center text-slate-500 py-12">
                      <div className="w-20 h-20 rounded-full bg-slate-800 mx-auto flex items-center justify-center mb-4">
                        <Trophy className="w-10 h-10 text-slate-600" />
                      </div>
                      <p className="font-medium mb-1">Your betslip is empty</p>
                      <p className="text-sm">Tap on props to add them</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {/* Parlay Odds Summary */}
                      <div className="bg-blue-950/30 border border-blue-900/50 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-blue-300">Parlay Odds</span>
                          <span className="text-2xl font-bold text-white">{formatOdds(parlayOdds)}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs text-slate-400">
                          <span>$10 Bet</span>
                          <span className="text-green-400 font-semibold">
                            Win ${parlayOdds > 0 ? (10 * (parlayOdds / 100) + 10).toFixed(2) : (10 * (100 / Math.abs(parlayOdds)) + 10).toFixed(2)}
                          </span>
                        </div>
                      </div>

                      {/* Selected Legs */}
                      <div className="space-y-2 max-h-[300px] overflow-y-auto">
                        {selectedLegs.map((leg, idx) => (
                          <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800 relative group hover:border-slate-700 transition-colors">
                            <button
                              onClick={() => removeLeg(leg)}
                              className="absolute top-2 right-2 text-slate-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                            >
                              <X className="w-4 h-4" />
                            </button>

                            <div className="pr-6">
                              <div className="font-semibold text-sm text-white mb-1">{leg.player_name}</div>
                              <div className="flex items-center gap-2 text-xs">
                                <span className="text-slate-400">{getShortStatLabel(leg.stat!)}</span>
                                <span className={cn(
                                  "font-bold px-1.5 py-0.5 rounded",
                                  leg.direction === 'over' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                                )}>
                                  {leg.direction?.toUpperCase()} {leg.line}
                                </span>
                                <span className="text-slate-500">{formatOdds(leg.odds)}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Analyze Button */}
                      <Button
                        className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-bold py-6 mt-4 disabled:opacity-50 shadow-lg shadow-blue-600/30 transition-all"
                        onClick={handleAnalyze}
                        disabled={isAnalyzing || selectedLegs.length < 2}
                      >
                        {isAnalyzing ? (
                          <span className="flex items-center gap-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            Analyzing...
                          </span>
                        ) : (
                          <span className="flex items-center gap-2">
                            <Sparkles className="w-5 h-5" />
                            Analyze Parlay
                          </span>
                        )}
                      </Button>

                      {/* Analysis Results */}
                      {analysisResult && (
                        <div className="mt-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                          {/* Recommendation Badge */}
                          <div className={cn(
                            "rounded-xl p-4 text-center mb-4 border-2",
                            analysisResult.recommended
                              ? "bg-emerald-950/50 border-emerald-500/50"
                              : "bg-slate-800/50 border-slate-600/50"
                          )}>
                            <div className="flex items-center justify-center gap-2 mb-2">
                              {analysisResult.recommended ? (
                                <>
                                  <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                                  <span className="text-emerald-400 font-bold text-lg">Recommended</span>
                                </>
                              ) : (
                                <>
                                  <AlertCircle className="w-6 h-6 text-yellow-400" />
                                  <span className="text-yellow-400 font-bold text-lg">Not Recommended</span>
                                </>
                              )}
                            </div>
                          </div>

                          {/* Key Metrics Grid */}
                          <div className="grid grid-cols-2 gap-3 mb-4">
                            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                              <div className="text-xs text-slate-500 mb-1">Expected Value</div>
                              <div className={cn(
                                "text-2xl font-bold",
                                analysisResult.ev_pct > 0 ? "text-emerald-400" : "text-red-400"
                              )}>
                                {analysisResult.ev_pct > 0 ? '+' : ''}{analysisResult.ev_pct.toFixed(1)}%
                              </div>
                            </div>

                            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                              <div className="text-xs text-slate-500 mb-1">True Probability</div>
                              <div className="text-2xl font-bold text-white">
                                {(analysisResult.true_probability * 100).toFixed(1)}%
                              </div>
                            </div>

                            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                              <div className="text-xs text-slate-500 mb-1">Fair Odds</div>
                              <div className="text-lg font-bold text-blue-400">
                                {analysisResult.fair_odds}
                              </div>
                            </div>

                            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                              <div className="text-xs text-slate-500 mb-1">Correlation</div>
                              <div className="text-lg font-bold text-purple-400">
                                {analysisResult.correlation_multiplier.toFixed(2)}x
                              </div>
                            </div>
                          </div>

                          {/* Explanation */}
                          {analysisResult.explanation && (
                            <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
                              <div className="flex items-start gap-2 mb-2">
                                <Sparkles className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                                <div>
                                  <p className="font-semibold text-sm text-white mb-1">AI Insight</p>
                                  <p className="text-xs text-slate-400 leading-relaxed">
                                    {analysisResult.explanation.regime_reasoning}
                                  </p>
                                </div>
                              </div>
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

// Improved Prop Card Component (FanDuel Style)
function ImprovedPropCard({
  marginal,
  selectedLegs,
  onToggle,
}: {
  marginal: PlayerMarginal;
  selectedLegs: ParlayLeg[];
  onToggle: (leg: ParlayLeg) => void;
}) {
  if (!marginal.player) return null;

  const playerName = marginal.player.name || '';
  const position = marginal.player.position || '';
  const statLabel = getShortStatLabel(marginal.stat_type);
  const line = marginal.line;

  const isOverSelected = selectedLegs.some(
    l => l.player_id === marginal.player!.id && l.stat === marginal.stat_type && l.direction === 'over'
  );

  const isUnderSelected = selectedLegs.some(
    l => l.player_id === marginal.player!.id && l.stat === marginal.stat_type && l.direction === 'under'
  );

  const hasUnder = marginal.under_odds !== null && marginal.under_odds !== undefined;
  const isTDScorer = marginal.stat_type === 'anytime_tds';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 hover:border-slate-700 transition-all">
      <div className="flex items-center justify-between mb-3">
        {/* Player Info */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center text-sm font-bold text-white shadow-md">
            {playerName.split(' ').map(n => n[0]).join('').slice(0, 2)}
          </div>
          <div>
            <div className="font-semibold text-white">{playerName}</div>
            <div className="flex items-center gap-2 mt-0.5">
              <PositionBadge position={position} />
              <span className="text-xs text-slate-500">{statLabel}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Prop Buttons */}
      <div className="grid grid-cols-2 gap-3">
        {/* Over / Yes Button */}
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
            "relative py-4 px-4 rounded-xl border-2 text-center transition-all duration-200 group",
            isOverSelected
              ? "bg-blue-600 border-blue-500 shadow-lg shadow-blue-600/30 scale-105"
              : "bg-slate-950 border-slate-700 hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-600/10"
          )}
        >
          <div className="flex flex-col items-center gap-1">
            {isOverSelected && (
              <div className="absolute top-1 right-1">
                <CheckCircle2 className="w-4 h-4 text-white" />
              </div>
            )}
            <div className={cn(
              "text-xs font-semibold uppercase tracking-wide mb-1",
              isOverSelected ? "text-blue-100" : "text-slate-400 group-hover:text-blue-400"
            )}>
              {isTDScorer ? 'Yes' : 'Over'}
            </div>
            <div className={cn(
              "text-xl font-bold",
              isOverSelected ? "text-white" : "text-white"
            )}>
              {line}
            </div>
            <div className={cn(
              "text-xs font-medium",
              isOverSelected ? "text-blue-100" : "text-slate-500"
            )}>
              {formatOdds(marginal.over_odds)}
            </div>
          </div>
        </button>

        {/* Under / No Button (if applicable) */}
        {hasUnder ? (
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
              "relative py-4 px-4 rounded-xl border-2 text-center transition-all duration-200 group",
              isUnderSelected
                ? "bg-blue-600 border-blue-500 shadow-lg shadow-blue-600/30 scale-105"
                : "bg-slate-950 border-slate-700 hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-600/10"
            )}
          >
            <div className="flex flex-col items-center gap-1">
              {isUnderSelected && (
                <div className="absolute top-1 right-1">
                  <CheckCircle2 className="w-4 h-4 text-white" />
                </div>
              )}
              <div className={cn(
                "text-xs font-semibold uppercase tracking-wide mb-1",
                isUnderSelected ? "text-blue-100" : "text-slate-400 group-hover:text-blue-400"
              )}>
                Under
              </div>
              <div className={cn(
                "text-xl font-bold",
                isUnderSelected ? "text-white" : "text-white"
              )}>
                {line}
              </div>
              <div className={cn(
                "text-xs font-medium",
                isUnderSelected ? "text-blue-100" : "text-slate-500"
              )}>
                {formatOdds(marginal.under_odds)}
              </div>
            </div>
          </button>
        ) : (
          // Placeholder for single-sided props
          <div className="flex items-center justify-center text-slate-600 text-xs">
            {isTDScorer ? 'TD Scorer' : 'No Under'}
          </div>
        )}
      </div>
    </div>
  );
}
