# FPL Team of the Week Predictor

An ML-powered tool that predicts the Fantasy Premier League Dream Team (Team of the Week) before each gameweek.

## Features

- **ML Predictions**: Uses LightGBM to predict player points based on form, fixtures, and xG/xA data
- **Formation Optimizer**: MILP solver selects optimal XI within FPL constraints
- **Pitch Visualization**: Interactive pitch view showing predicted/actual Dream Teams
- **Backtesting**: Rolling-origin backtest to validate prediction accuracy
- **Real-time Data**: Syncs with official FPL API and Understat for xG/xA

## Target Accuracy

- **Historical backtest**: ≥85% points ratio, ≥9/11 player overlap
- **Future predictions**: ~80% accuracy

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, LightGBM
- **Frontend**: Next.js 14, React 18, Tailwind CSS, shadcn/ui
- **Database**: PostgreSQL 16
- **Deployment**: Docker Compose

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd fpl_totw
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Usage

### 1. Sync FPL Data

Click "Sync Data" on the main page or via API:
```bash
curl -X POST http://localhost:8000/api/sync/fpl
```

This fetches:
- All teams and players
- Gameweek fixtures and results
- Player statistics per gameweek
- Actual Dream Teams (for finished gameweeks)

### 2. Generate Predictions

Select a gameweek and click "Generate Prediction":
```bash
curl -X POST http://localhost:8000/api/predictions/generate/15
```

The ML model predicts the best XI based on:
- Rolling form (3, 5, 8 game windows)
- Fixture difficulty
- xG/xA from Understat
- Position-specific features

### 3. Run Backtest

Navigate to `/backtest` or via API:
```bash
curl -X POST http://localhost:8000/api/backtest/run
```

This runs rolling-origin backtest from GW 6 onwards, showing:
- Player overlap per gameweek
- Points ratio vs actual Dream Team
- Summary statistics

## Project Structure

```
fpl_totw/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── ml/           # ML models (points, formation solver)
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── constants.py  # Shared constants (from JSON)
│   │   └── main.py       # FastAPI app
│   ├── migrations/       # Alembic migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   ├── lib/          # API client, utilities
│   │   └── types/        # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── shared/
│   └── constants.json    # Single source of truth
├── docs/
│   └── IMPLEMENTATION_PLAN.md
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Data Sync
- `POST /api/sync/fpl` - Sync all FPL data

### Gameweeks
- `GET /api/gameweeks` - List all gameweeks
- `GET /api/gameweeks/current` - Current gameweek
- `GET /api/gameweeks/{id}` - Gameweek details

### Players
- `GET /api/players` - List players (with filters)
- `GET /api/players/{id}` - Player details

### Predictions
- `GET /api/predictions/{gw_id}` - Get prediction for gameweek
- `POST /api/predictions/generate/{gw_id}` - Generate new prediction

### Dream Team
- `GET /api/dream-team/{gw_id}` - Actual Dream Team

### Backtest
- `GET /api/backtest/summary` - Backtest summary
- `POST /api/backtest/run` - Run full backtest

## Shared Constants

Both Python and TypeScript read from `shared/constants.json` to ensure consistency:

```json
{
  "positions": { "GKP": "GKP", "DEF": "DEF", "MID": "MID", "FWD": "FWD" },
  "formationConstraints": { "minGkp": 1, "maxGkp": 1, "minDef": 3, "maxDef": 5, ... },
  "rollingWindows": [3, 5, 8]
}
```

## Development

### Local Backend (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Local Frontend (without Docker)

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend lint
cd frontend
npm run lint
```

## ML Model Details

### Feature Engineering

Rolling window features (3, 5, 8 games):
- Points, goals, assists, bonus
- xG, xA, npxG (from Understat)
- Minutes played, starts
- BPS (Bonus Point System)

Fixture features:
- Home/away indicator
- Opponent strength (attack/defence)
- Fixture difficulty rating

### Points Model

LightGBM regressor trained to predict `E[points]` per player per gameweek.

### Formation Solver

MILP optimization that selects XI maximizing total predicted points subject to:
- Exactly 1 GKP
- 3-5 DEF
- 2-5 MID
- 1-3 FWD
- Total = 11 players

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@db:5432/fpl_totw` |
| `DEBUG` | Enable debug mode | `true` |
| `NEXT_PUBLIC_API_URL` | Backend API URL for frontend | `http://localhost:8000` |

## License

MIT

## Acknowledgments

- [Fantasy Premier League API](https://fantasy.premierleague.com/api/)
- [Understat](https://understat.com/) for xG/xA data
- [shadcn/ui](https://ui.shadcn.com/) for UI components
