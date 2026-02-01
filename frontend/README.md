# SmartParlay Frontend

Modern, dark-mode sports betting analytics interface built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

- **Dashboard**: View upcoming NFL games with spreads, totals, and weather
- **Parlay Builder**: Select player props and build optimized Same-Game Parlays
- **AI Analysis**: Real-time parlay analysis using Student-t Copula simulations
- **EV Visualization**: Color-coded badges showing positive/negative expected value
- **Responsive Design**: Mobile-first dark mode sportsbook aesthetic

## Tech Stack

- **Next.js 14**: App Router with React Server Components
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling with custom sportsbook theme
- **Shadcn/UI**: High-quality component library
- **TanStack Query**: Server state management
- **Axios**: HTTP client for backend API

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Backend running at `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at **http://localhost:3000**

## Project Structure

```
frontend/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # Root layout with Providers
│   ├── page.tsx             # Dashboard / Games List
│   ├── parlay/
│   │   └── [gameId]/
│   │       └── page.tsx     # Parlay Builder (dynamic route)
│   └── globals.css          # Global styles with theme
├── components/
│   ├── ui/                  # Shadcn UI components
│   │   ├── button.tsx       # Button with +EV/-EV variants
│   │   ├── card.tsx
│   │   └── badge.tsx        # Badge for EV display
│   └── providers.tsx        # React Query provider
├── lib/
│   ├── api.ts               # Axios API client
│   ├── types.ts             # TypeScript interfaces
│   └── utils.ts             # Helper functions
└── tailwind.config.ts       # Tailwind with custom colors
```

## API Integration

The frontend connects to the backend API at `http://localhost:8000`:

- `GET /api/v1/games` - Fetch upcoming games
- `GET /api/v1/games/{game_id}` - Get game details
- `GET /api/v1/players/game/{game_id}/marginals` - Get player projections
- `POST /api/v1/parlays/generate` - Generate parlay recommendation

## Custom Theme

The frontend uses a custom dark-mode sportsbook aesthetic:

- **--positive**: Green for +EV bets
- **--negative**: Red for -EV bets
- **--neutral**: Gray for neutral/informational elements

## Development Workflow

1. **Start Backend**: Ensure backend is running (`cd ../backend && docker-compose up -d`)
2. **Start Frontend**: Run `npm run dev`
3. **View Dashboard**: Navigate to http://localhost:3000
4. **Build Parlays**: Click "Build Parlay" on any game
5. **Select Props**: Choose player props (Over/Under)
6. **Analyze**: Click "Analyze Parlay" to get AI recommendation

## Troubleshooting

### Backend Connection Issues
```bash
# Check backend is running
curl http://localhost:8000/health
```

### No Games Showing
Run the backend seeding script to populate test data:
```bash
cd ../backend
docker-compose exec backend python -m app.scripts.seed_nfl_data
```

## Next Steps

- Add user authentication (JWT)
- Implement parlay history tracking
- Add more player prop types
- Build mobile app version
- Add live odds updates
- Implement bet tracking
