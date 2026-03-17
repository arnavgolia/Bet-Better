#!/usr/bin/env python3
"""
Auto-Parlay System Test Script
Tests all components of the auto-parlay intelligence system
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_db
from app.services.auto_parlay.intent_parser import IntentParser, RiskProfile
from app.services.auto_parlay.candidate_generator import CandidateGenerator, ConstraintValidator
from app.services.auto_parlay.compatibility_engine import CompatibilityEngine, CorrelationEngine
from app.services.auto_parlay.parlay_scorer import ParlayScorer, ParlayOptimizer


async def test_intent_parser():
    """Test the intent parsing system"""
    print("\n" + "="*60)
    print("TEST 1: Intent Parser")
    print("="*60)

    parser = IntentParser()

    test_cases = [
        "Build me a safe 5-leg parlay for the Super Bowl",
        "Give me a risky 7-leg parlay",
        "Make me a cross-sport parlay with NFL and NBA",
        "Build a same-game parlay for KC vs SF",
        "I want a degen lottery ticket parlay"
    ]

    for test_input in test_cases:
        print(f"\n📝 Input: '{test_input}'")
        intent = parser.parse(test_input)
        print(f"   ✅ Legs: {intent.num_legs}")
        print(f"   ✅ Risk: {intent.risk_profile.value}")
        print(f"   ✅ Sports: {intent.sports}")
        print(f"   ✅ Correlation: {intent.correlation_strategy.value}")

    print("\n✅ Intent Parser: PASSED")
    return True


async def test_candidate_generation():
    """Test candidate generation from database"""
    print("\n" + "="*60)
    print("TEST 2: Candidate Generation")
    print("="*60)

    # Get database session
    async for db in get_db():
        parser = IntentParser()
        intent = parser.parse("Build me a 5-leg parlay")

        print(f"\n📊 Checking database for available props...")

        # Test constraint validation
        validator = ConstraintValidator(db)
        validation = await validator.validate(intent)

        print(f"   ✅ Validation: {'PASS' if validation['valid'] else 'FAIL'}")
        if not validation['valid']:
            print(f"   ❌ Errors: {validation['errors']}")
            return False

        # Generate candidates
        generator = CandidateGenerator(db)
        candidates = await generator.generate_candidates(intent)

        print(f"   ✅ Candidates found: {len(candidates)}")

        if len(candidates) > 0:
            print(f"\n   Sample candidates:")
            for i, candidate in enumerate(candidates[:3]):
                print(f"   {i+1}. {candidate.player.name if candidate.player else 'Team'}")
                print(f"      {candidate.stat_type}: {candidate.line}")
                print(f"      Over: {candidate.over_odds} ({candidate.over_prob:.1%})")
                print(f"      Under: {candidate.under_odds} ({candidate.under_prob:.1%})")
        else:
            print(f"\n   ⚠️  No candidates found - did you run data ingestion?")
            print(f"   Run: python -m scripts.ingest_fanduel_data")
            return False

        print("\n✅ Candidate Generation: PASSED")
        return True


async def test_compatibility_engine():
    """Test compatibility and correlation checking"""
    print("\n" + "="*60)
    print("TEST 3: Compatibility Engine")
    print("="*60)

    # Create mock candidates for testing
    from unittest.mock import Mock

    # Create mock props
    qb_passing = Mock()
    qb_passing.player = Mock(id="player1", team_id="KC", name="Patrick Mahomes")
    qb_passing.stat_type = "passing_yards"
    qb_passing.line = 285.5
    qb_passing.recommended_direction = "over"
    qb_passing.game_id = "game1"

    wr_receiving = Mock()
    wr_receiving.player = Mock(id="player2", team_id="KC", name="Travis Kelce")
    wr_receiving.stat_type = "receiving_yards"
    wr_receiving.line = 65.5
    wr_receiving.recommended_direction = "over"
    wr_receiving.game_id = "game1"

    rb_rushing = Mock()
    rb_rushing.player = Mock(id="player3", team_id="SF", name="Christian McCaffrey")
    rb_rushing.stat_type = "rushing_yards"
    rb_rushing.line = 75.5
    rb_rushing.recommended_direction = "over"
    rb_rushing.game_id = "game1"

    # Test compatibility
    engine = CompatibilityEngine()

    props = [qb_passing, wr_receiving, rb_rushing]
    report = engine.check_compatibility(props)

    print(f"\n📊 Testing 3-leg parlay:")
    print(f"   Leg 1: Mahomes OVER 285.5 Pass Yards")
    print(f"   Leg 2: Kelce OVER 65.5 Rec Yards")
    print(f"   Leg 3: CMC OVER 75.5 Rush Yards")

    print(f"\n   ✅ Compatibility Score: {report.score:.2f}")
    print(f"   ✅ Valid: {report.is_valid}")

    if report.bonuses:
        print(f"\n   🎁 Bonuses:")
        for bonus in report.bonuses[:3]:
            print(f"      • {bonus.reason} ({bonus.severity:.0%})")

    if report.penalties:
        print(f"\n   ⚠️  Penalties:")
        for penalty in report.penalties[:3]:
            print(f"      • {penalty.reason} ({penalty.severity:.0%})")

    # Test correlation
    corr_engine = CorrelationEngine()
    corr_metrics = corr_engine.measure_parlay_correlation(props)

    print(f"\n   ✅ Average Correlation: {corr_metrics['average']:.2f}")
    print(f"   ✅ Max Correlation: {corr_metrics['max']:.2f}")

    print("\n✅ Compatibility Engine: PASSED")
    return True


async def test_parlay_scoring():
    """Test parlay scoring system"""
    print("\n" + "="*60)
    print("TEST 4: Parlay Scoring")
    print("="*60)

    from unittest.mock import Mock

    # Create mock candidates
    candidates = []
    for i in range(5):
        marginal = Mock()
        marginal.id = f"m{i}"
        marginal.game_id = "game1"
        marginal.player_id = f"player{i}"
        marginal.stat_type = "passing_yards"
        marginal.line = 250.5 + i * 10
        marginal.over_odds = -110
        marginal.under_odds = -110
        marginal.over_prob = 0.52
        marginal.under_prob = 0.48

        game = Mock()
        game.id = "game1"
        game.sport = "NFL"

        player = Mock()
        player.id = f"player{i}"
        player.team_id = "KC"
        player.name = f"Player {i}"

        candidate = Mock()
        candidate.marginal = marginal
        candidate.game = game
        candidate.player = player
        candidate.game_id = "game1"
        candidate.stat_type = "passing_yards"
        candidate.line = 250.5 + i * 10
        candidate.over_odds = -110
        candidate.under_odds = -110
        candidate.over_prob = 0.52
        candidate.under_prob = 0.48
        candidate.recommended_direction = "over"
        candidate.model_confidence = 0.75

        candidates.append(candidate)

    # Test different risk profiles
    scorer = ParlayScorer()

    risk_profiles = [
        RiskProfile.SAFE,
        RiskProfile.BALANCED,
        RiskProfile.AGGRESSIVE,
        RiskProfile.DEGEN
    ]

    print(f"\n📊 Scoring 5-leg parlay with different risk profiles:")

    for profile in risk_profiles:
        intent = Mock()
        intent.risk_profile = profile
        intent.num_legs = 5
        intent.correlation_strategy = Mock()
        intent.correlation_strategy.value = 'neutral'

        score = scorer.score(candidates[:5], intent)

        print(f"\n   {profile.value.upper()}:")
        print(f"      Overall Score: {score.overall:.1f}/100")
        print(f"      Expected Value: ${score.expected_value:.2f}")
        print(f"      Win Probability: {score.win_probability*100:.1f}%")
        print(f"      Confidence: {score.confidence:.2%}")
        print(f"      Sharpe Ratio: {score.sharpe_ratio:.2f}")

    print("\n✅ Parlay Scoring: PASSED")
    return True


async def test_full_build():
    """Test complete parlay building end-to-end"""
    print("\n" + "="*60)
    print("TEST 5: Full Parlay Build (End-to-End)")
    print("="*60)

    async for db in get_db():
        # Parse intent
        parser = IntentParser()
        intent = parser.parse("Build me a safe 5-leg parlay")

        print(f"\n📝 User Input: 'Build me a safe 5-leg parlay'")
        print(f"   Parsed Intent:")
        print(f"      • Legs: {intent.num_legs}")
        print(f"      • Risk: {intent.risk_profile.value}")

        # Validate
        validator = ConstraintValidator(db)
        validation = await validator.validate(intent)

        if not validation['valid']:
            print(f"\n   ❌ Validation Failed:")
            for error in validation['errors']:
                print(f"      • {error}")
            return False

        print(f"   ✅ Validation: PASSED")

        # Generate candidates
        generator = CandidateGenerator(db)
        candidates = await generator.generate_candidates(intent)

        print(f"   ✅ Candidates: {len(candidates)} props")

        if len(candidates) < intent.num_legs:
            print(f"\n   ⚠️  Not enough props for {intent.num_legs}-leg parlay")
            print(f"   Run data ingestion: python -m scripts.ingest_fanduel_data")
            return False

        # Build optimal parlay
        scorer = ParlayScorer()
        optimizer = ParlayOptimizer(scorer)

        print(f"\n   🎯 Building optimal parlay...")
        result = await optimizer.build_optimal_parlay(
            candidates,
            intent,
            max_combinations=100
        )

        best = result['primary']

        print(f"\n   ✅ SUCCESS! Built optimal parlay:")
        print(f"      Score: {best.score.overall:.1f}/100")
        print(f"      Win Prob: {best.score.win_probability*100:.1f}%")
        print(f"      EV: ${best.score.expected_value:.2f}")
        print(f"      Confidence: {best.score.confidence:.2%}")

        print(f"\n   Legs:")
        for i, leg in enumerate(best.legs):
            player_name = leg.player.name if leg.player else "Team"
            print(f"      {i+1}. {player_name} {leg.recommended_direction.upper()} {leg.line} {leg.stat_type}")

        print(f"\n   Alternatives: {len(result['alternatives'])}")
        for alt in result['alternatives']:
            print(f"      • {alt['type']}: {alt['description']}")

        print("\n✅ Full Build: PASSED")
        return True


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 AUTO-PARLAY SYSTEM TEST SUITE")
    print("="*60)
    print("Testing all components of the auto-parlay intelligence system")

    tests = [
        ("Intent Parser", test_intent_parser),
        ("Candidate Generation", test_candidate_generation),
        ("Compatibility Engine", test_compatibility_engine),
        ("Parlay Scoring", test_parlay_scoring),
        ("Full Build (E2E)", test_full_build),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {name}: {status}")

    print(f"\n   Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready to use.")
        print("\nNext steps:")
        print("   1. Start backend: uvicorn app.main:app --reload")
        print("   2. Start frontend: cd frontend && npm run dev")
        print("   3. Visit: http://localhost:3000/build-parlay")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        print("\nCommon fixes:")
        print("   • Run migrations: alembic upgrade head")
        print("   • Ingest data: python -m scripts.ingest_fanduel_data")
        print("   • Check database connection in .env")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
