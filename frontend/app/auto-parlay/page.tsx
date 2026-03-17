"use client";

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sparkles, Loader2, TrendingUp, TrendingDown, Trophy, AlertCircle } from 'lucide-react';

interface PropLeg {
  player_name: string | null;
  stat_type: string;
  line: number | null;
  direction: string;
  odds: number;
  confidence: number;
  primary_reason: string;
  supporting_factors: string[];
}

interface Parlay {
  parlay_id: string;
  legs: PropLeg[];
  num_legs: number;
  overall_score: number;
  expected_value: number;
  win_probability: number;
  parlay_odds: number;
  correlation: number;
  confidence: number;
  risk_profile: string;
  summary: string;
  reasoning: string;
}

interface AlternativeParlay {
  type: string;
  description: string;
  parlay: Parlay;
}

interface AutoParlayResponse {
  primary_parlay: Parlay;
  alternatives: AlternativeParlay[];
  intent: any;
  build_time_ms: number;
  candidates_considered: number;
}

export default function AutoParlayPage() {
  const [userInput, setUserInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AutoParlayResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAlternatives, setShowAlternatives] = useState(false);

  const quickPresets = [
    { label: '🛡️ Safe Money', text: 'Build me a safe 5-leg parlay' },
    { label: '⚖️ Balanced', text: 'Build me a balanced 5-leg parlay' },
    { label: '🚀 High Risk', text: 'Build me a high-risk aggressive parlay' },
    { label: '🎰 YOLO', text: 'Build me a degen lottery ticket parlay' },
  ];

  const buildParlay = async () => {
    if (!userInput.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/auto-parlay/build', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: userInput })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || 'Failed to build parlay');
      }

      const data: AutoParlayResponse = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const formatOdds = (odds: number) => {
    return odds > 0 ? `+${odds}` : `${odds}`;
  };

  const formatStatType = (statType: string) => {
    return statType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            <Sparkles className="inline-block w-8 h-8 mr-2 text-blue-500" />
            AI Parlay Builder
          </h1>
          <p className="text-slate-400">
            Describe your ideal parlay in plain English. I'll build it for you.
          </p>
        </div>

        {/* Input Section */}
        <Card className="bg-slate-900 border-slate-800 mb-6">
          <CardContent className="pt-6">
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Examples:
• Build me a 5-leg parlay for the Super Bowl
• Give me a super safe money parlay
• Make me a high-risk, high-reward NFL parlay
• Build a cross-sport parlay (NFL + NBA)"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-4 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-32 resize-none"
            />

            <div className="flex gap-2 mt-4 flex-wrap">
              {quickPresets.map((preset, idx) => (
                <button
                  key={idx}
                  onClick={() => setUserInput(preset.text)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors"
                >
                  {preset.label}
                </button>
              ))}
            </div>

            <Button
              onClick={buildParlay}
              disabled={loading || !userInput.trim()}
              className="w-full mt-4 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-bold py-6 text-lg shadow-lg shadow-blue-600/20"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Building Your Parlay...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Build My Parlay
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Card className="bg-red-950/30 border-red-900 mb-6">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-red-300 mb-1">Error Building Parlay</h3>
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {result && (
          <>
            {/* Primary Parlay */}
            <Card className="bg-slate-900 border-slate-800 mb-6">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Trophy className="w-6 h-6 text-yellow-500" />
                    Optimized {result.primary_parlay.num_legs}-Leg Parlay
                  </span>
                  <span className="text-2xl font-bold text-blue-400">
                    {formatOdds(result.primary_parlay.parlay_odds)}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {/* Stats Row */}
                <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-slate-950/50 rounded-lg">
                  <div>
                    <div className="text-xs text-slate-500 mb-1">Win Probability</div>
                    <div className="text-xl font-bold text-white">
                      {(result.primary_parlay.win_probability * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 mb-1">Expected Value</div>
                    <div className={`text-xl font-bold ${result.primary_parlay.expected_value >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ${result.primary_parlay.expected_value.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 mb-1">Confidence</div>
                    <div className="text-xl font-bold text-white">
                      {(result.primary_parlay.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>

                {/* Reasoning */}
                <div className="mb-6 p-4 bg-blue-950/30 border border-blue-900/50 rounded-lg">
                  <p className="text-blue-100 leading-relaxed">{result.primary_parlay.reasoning}</p>
                </div>

                {/* Legs */}
                <div className="space-y-3">
                  {result.primary_parlay.legs.map((leg, idx) => (
                    <Card key={idx} className="bg-slate-950 border-slate-800">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs font-bold text-slate-500">LEG {idx + 1}</span>
                              <span className="text-sm font-semibold text-white">
                                {leg.player_name || 'Team'}
                              </span>
                            </div>
                            <div className="text-lg font-bold text-blue-400">
                              {leg.direction.toUpperCase()} {leg.line} {formatStatType(leg.stat_type)}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-white">{formatOdds(leg.odds)}</div>
                            <div className="text-xs text-slate-500">{(leg.confidence * 100).toFixed(0)}% confidence</div>
                          </div>
                        </div>

                        <div className="mt-3 p-3 bg-slate-900 rounded-lg">
                          <div className="text-xs font-semibold text-slate-400 mb-1">WHY THIS PICK:</div>
                          <div className="text-sm text-slate-300 mb-2">{leg.primary_reason}</div>
                          <ul className="space-y-1">
                            {leg.supporting_factors.map((factor, i) => (
                              <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                                <span className="text-blue-500">•</span>
                                {factor}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Build Stats */}
                <div className="mt-6 pt-4 border-t border-slate-800 text-xs text-slate-500 flex justify-between">
                  <span>Built in {result.build_time_ms}ms</span>
                  <span>{result.candidates_considered} props analyzed</span>
                </div>
              </CardContent>
            </Card>

            {/* Alternatives */}
            {result.alternatives.length > 0 && (
              <div>
                <button
                  onClick={() => setShowAlternatives(!showAlternatives)}
                  className="w-full mb-4 p-4 bg-slate-900 border border-slate-800 rounded-lg text-left hover:bg-slate-850 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">
                      View Alternative Versions ({result.alternatives.length})
                    </span>
                    <TrendingDown className={`w-5 h-5 transition-transform ${showAlternatives ? 'rotate-180' : ''}`} />
                  </div>
                </button>

                {showAlternatives && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {result.alternatives.map((alt, idx) => (
                      <Card key={idx} className="bg-slate-900 border-slate-800">
                        <CardHeader>
                          <CardTitle className="text-sm">
                            {alt.type === 'safer' && '🛡️ Safer Version'}
                            {alt.type === 'riskier' && '🚀 Riskier Version'}
                            {alt.type === 'same_game' && '🎮 Same Game'}
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold text-blue-400 mb-2">
                            {formatOdds(alt.parlay.parlay_odds)}
                          </div>
                          <div className="text-sm text-slate-400 mb-4">{alt.description}</div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div>
                              <div className="text-slate-500">Win Prob</div>
                              <div className="font-semibold text-white">
                                {(alt.parlay.win_probability * 100).toFixed(1)}%
                              </div>
                            </div>
                            <div>
                              <div className="text-slate-500">EV</div>
                              <div className={`font-semibold ${alt.parlay.expected_value >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                ${alt.parlay.expected_value.toFixed(2)}
                              </div>
                            </div>
                          </div>
                          <Button className="w-full mt-4 bg-slate-800 hover:bg-slate-700 text-white text-sm">
                            View Details
                          </Button>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
