# SmartParlay UI Improvement Plan
**Date:** February 1, 2026
**Objective:** Match FanDuel's UI/UX and fix TD Scorer tab issue

---

## 🔍 Issues Identified

### Issue #1: TD Scorer Tab Shows No Data
**Current State:**
- Tab filters for `stat_type === 'anytime_tds'`
- Debug shows: "28 marginals loaded (scoring filtered: 0)"
- Available stat types: receiving_yards, rushing_yards, passing_tds, passing_yards
- **NO** anytime_tds in the data

**Root Cause:**
- Either TD props weren't ingested for this game
- OR they're stored with a different stat_type name in the database

**Solution:**
1. Check actual database stat_type values for TD props
2. Update frontend filter to match actual backend naming
3. Ensure ingestion script is creating TD props correctly

### Issue #2: UI Doesn't Match FanDuel

**Current Issues:**
- Prop cards are too compact
- Player info lacks detail (no position badges, team colors)
- Odds display is small and hard to read
- No search/filter functionality
- Header could be cleaner
- Betslip needs better visual hierarchy

**FanDuel Design Patterns:**
- Large, tappable prop buttons with clear odds
- Player headshots (we can use placeholders)
- Team-colored accents
- Position badges (QB, RB, WR, TE)
- Search bar for quick player lookup
- "Popular" props featured first
- Cleaner spacing and typography
- Better mobile touch targets

---

## 📋 Implementation Plan

### Phase 1: Fix TD Scorer Data Issue ✅

**Step 1:** Query database to check actual TD prop stat_types
```bash
# Check what stat types exist for TD scorers
docker-compose exec backend python -c "
from app.models.database import PlayerMarginal
from app.api.dependencies.database import async_session_maker
import asyncio

async def check():
    async with async_session_maker() as db:
        from sqlalchemy import select, distinct
        result = await db.execute(select(distinct(PlayerMarginal.stat_type)))
        types = result.scalars().all()
        print('All stat types:', types)

        # Check for touchdown-related
        td_result = await db.execute(
            select(PlayerMarginal).where(PlayerMarginal.stat_type.contains('td'))
        )
        td_props = td_result.scalars().all()
        print(f'TD Props found: {len(td_props)}')
        for prop in td_props[:5]:
            print(f'  - {prop.stat_type}')

asyncio.run(check())
"
```

**Step 2:** Update frontend TAB_CATEGORIES to match actual backend naming
- Change `'anytime_tds'` to whatever the DB actually uses
- Could be `'touchdowns'`, `'scoring'`, `'anytime_touchdown'`, etc.

**Step 3:** Add fallback handling if TD props don't exist
- Show helpful message: "TD Scorer props not available for this game"
- Link to re-run ingestion if needed

### Phase 2: Redesign Prop Cards (FanDuel Style) 🎨

**Improvements:**

1. **Player Info Enhancement:**
   ```tsx
   <PlayerCard>
     <Avatar fallback={initials} />
     <PlayerName>{name}</PlayerName>
     <PlayerMeta>
       <PositionBadge>{position}</PositionBadge>
       <TeamBadge color={teamColor}>{teamAbbrev}</TeamBadge>
     </PlayerMeta>
   </PlayerCard>
   ```

2. **Prop Button Redesign:**
   - Larger touch targets (min 48px height)
   - Bigger font sizes for odds
   - Clear visual states (idle/hover/selected)
   - Animation on selection
   ```tsx
   <PropButton selected={isSelected}>
     <PropLabel>O 250.5</PropLabel>
     <OddsLabel>-110</OddsLabel>
   </PropButton>
   ```

3. **Stat Type Organization:**
   - Group props by stat type under each player
   - Show multiple prop types per player in expandable cards
   - Example: Kenneth Walker III
     - Rushing Yards: O/U 73.5
     - Receiving Yards: O/U 20.5
     - Anytime TD: Yes (+120)

4. **Search & Filter:**
   ```tsx
   <SearchBar placeholder="Search players..." />
   <FilterChips>
     <Chip active>All Positions</Chip>
     <Chip>QB</Chip>
     <Chip>RB</Chip>
     <Chip>WR</Chip>
     <Chip>TE</Chip>
   </FilterChips>
   ```

### Phase 3: Betslip Improvements 💰

**Current Issues:**
- Legs are hard to scan quickly
- Odds calculation not shown
- No combined odds display

**Improvements:**
1. **Leg Display:**
   - Larger player names
   - Color-coded by direction (green for Over, red for Under)
   - Show projected vs actual line

2. **Odds Calculation:**
   ```tsx
   <BetslipSummary>
     <OddsRow>
       <Label>Parlay Odds</Label>
       <Value>+450</Value>
     </OddsRow>
     <OddsRow>
       <Label>To Win</Label>
       <Value>$45.00</Value>
     </OddsRow>
   </BetslipSummary>
   ```

3. **Analysis Results Enhancement:**
   - Bigger, bolder EV% display
   - Visual gauge for recommendation strength
   - Key factors as pills/chips
   - Expandable detailed breakdown

### Phase 4: Header & Navigation Improvements 🧭

**Improvements:**
1. **Breadcrumb Navigation:**
   ```tsx
   <Breadcrumb>
     <Link>Games</Link>
     <Separator>/</Separator>
     <Current>SEA @ NE</Current>
   </Breadcrumb>
   ```

2. **Game Summary Card:**
   - Team logos (placeholders)
   - Live score (if in-progress)
   - Game status badge
   - Quick stats (spread, total, time)

3. **Tab Bar Enhancement:**
   - Add icons to tabs
   - Show prop count badges
   - Sticky positioning on scroll
   - Smooth scroll animation

### Phase 5: Responsive & Accessibility ♿

1. **Mobile Optimizations:**
   - Collapsible sections
   - Swipeable tabs
   - Bottom sheet for betslip
   - Larger touch targets

2. **Accessibility:**
   - ARIA labels
   - Keyboard navigation
   - Screen reader support
   - Focus indicators

---

## 🚀 Implementation Order

1. **[HIGH PRIORITY] Fix TD Scorer Tab** (30 mins)
   - Query database for actual stat types
   - Update filter logic
   - Add fallback messaging

2. **[HIGH PRIORITY] Improve Prop Cards** (1 hour)
   - Redesign PlayerPropRow component
   - Add position badges
   - Larger, clearer buttons
   - Better hover/selected states

3. **[MEDIUM] Add Search & Filters** (45 mins)
   - Search bar component
   - Position filter chips
   - Implement filtering logic

4. **[MEDIUM] Enhance Betslip** (45 mins)
   - Redesign leg cards
   - Add odds calculator
   - Improve analysis display

5. **[LOW] Polish Header & Navigation** (30 mins)
   - Breadcrumbs
   - Game summary card
   - Tab enhancements

6. **[LOW] Responsive & A11y** (30 mins)
   - Mobile testing
   - Accessibility audit
   - Touch target sizing

---

## 📊 Success Metrics

- ✅ TD Scorer tab shows players (not empty)
- ✅ Props are easy to tap/click (min 48px targets)
- ✅ Visual hierarchy matches FanDuel
- ✅ Search filters players quickly
- ✅ Betslip odds are calculated and displayed
- ✅ Mobile experience is smooth
- ✅ All tabs show data correctly

---

## 🎨 Design References

FanDuel Design Patterns:
- Dark slate background (#0F172A, #1E293B)
- Blue accent for selected (#3B82F6)
- Green for positive EV (#10B981)
- Red for negative EV (#EF4444)
- Large, bold typography
- Generous white space
- Clear visual hierarchy

---

**Next Steps:**
1. Start with fixing TD Scorer tab (critical)
2. Then improve prop card design
3. Add search/filter functionality
4. Polish betslip
5. Final responsive pass
