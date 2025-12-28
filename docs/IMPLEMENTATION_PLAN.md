# FPL Team of the Week Predictor - Implementation Plan

## Overview

Build an ML-powered tool to predict the FPL Dream Team (Team of the Week) with 85-90% accuracy on historical data and 80% on future gameweeks.

**Success Metrics:**
- Player overlap: ≥9/11 players matching actual Dream Team
- Points ratio: Predicted XI points ÷ Actual Dream Team points ≥ 85%

---

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16 (via Docker)
- **ORM**: SQLAlchemy 2.0 + Alembic migrations
- **ML**: LightGBM, scikit-learn, scipy
- **Data Sources**: FPL API (official), Understat (xG/xA)

### Frontend
- **Framework**: Next.js 14 (React 18)
- **UI Components**: **shadcn/ui** (Radix UI primitives + Tailwind)
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Types**: TypeScript (strict mode)

### Shared Infrastructure
- **Containerization**: Docker Compose
- **Constants**: Single source of truth (`shared/constants.json`)

---

## Shared Constants Architecture (Single Source of Truth)

All domain constants are defined in a single JSON file that both Python and TypeScript read from:

```
shared/constants.json
```

### How It Works

- **Python**: `backend/app/constants.py` loads JSON and exports typed enums/constants
- **TypeScript**: `frontend/src/types/constants.ts` imports JSON and exports typed constants

### Benefits

1. **No drift**: Changes in one place automatically apply to both languages
2. **Type safety**: Both Python (enums) and TypeScript get fully typed constants
3. **Linting**: TypeScript will fail at compile time if constants are misused
4. **Single update**: Update `shared/constants.json` once, works everywhere

### Constants Defined

| Constant | Description |
|----------|-------------|
| `positions` | GKP, DEF, MID, FWD |
| `positionElementTypeMap` | FPL element_type (1-4) to position |
| `playerStatus` | Availability codes (a, d, i, n, s, u) |
| `formations` | Valid XI formations (3-4-3, 4-4-2, etc.) |
| `formationConstraints` | Min/max players per position |
| `pointsSystem` | FPL points for goals, assists, clean sheets, etc. |
| `rollingWindows` | Feature engineering windows [3, 5, 8] |
| `minGameweeksForPrediction` | Minimum GWs needed (5) |
| `fplApiBaseUrl` | API base URL |

---

## UI Component Library (shadcn/ui)

We use **shadcn/ui** for consistent, accessible, and beautiful components:

- Built on Radix UI primitives (headless, accessible)
- Fully customizable with Tailwind CSS
- Copy-paste components (no npm dependency lock-in)
- FPL-themed color scheme

### Key Components Used

| Component | Usage |
|-----------|-------|
| `Button` | Actions, navigation |
| `Card` | Player cards, stat cards |
| `Tabs` | Pitch view vs List view toggle |
| `Select` | Gameweek dropdown |
| `Tooltip` | Player stat hover info |
| `Badge` | Status indicators |

### FPL Color Theme

```css
--fpl-purple: #37003c
--fpl-purple-light: #963cff
--fpl-green: #00ff87
--fpl-cyan: #05f0ff
--fpl-pink: #e90052
--fpl-yellow: #ebff00
```

---

## Project Structure

```
fpl_totw/
├── shared/
│   └── constants.json              # Single source of truth for constants
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Settings/env vars
│   │   ├── constants.py            # Loads from shared/constants.json
│   │   ├── database.py             # DB connection
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── team.py
│   │   │   ├── player.py
│   │   │   ├── gameweek.py
│   │   │   ├── fixture.py
│   │   │   ├── player_stats.py
│   │   │   ├── prediction.py
│   │   │   └── dream_team.py
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   └── *.py
│   │   ├── api/                    # API routes
│   │   │   ├── __init__.py
│   │   │   ├── predictions.py
│   │   │   ├── gameweeks.py
│   │   │   ├── players.py
│   │   │   └── backtest.py
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── fpl_client.py       # FPL API client
│   │   │   ├── understat_client.py # Understat scraper
│   │   │   ├── data_ingestion.py   # Data sync jobs
│   │   │   ├── feature_engineering.py
│   │   │   ├── predictor.py        # ML prediction
│   │   │   └── backtest.py         # Backtesting harness
│   │   └── ml/                     # ML models
│   │       ├── __init__.py
│   │       ├── minutes_model.py    # P(start) + E[minutes]
│   │       ├── points_model.py     # E[points]
│   │       ├── formation_solver.py # XI optimization
│   │       └── train.py            # Training pipeline
│   ├── migrations/                 # Alembic migrations
│   ├── tests/
│   ├── requirements.txt
│   ├── alembic.ini
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Home/redirect
│   │   │   ├── layout.tsx
│   │   │   ├── globals.css         # Tailwind + shadcn/ui CSS vars
│   │   │   ├── predictions/
│   │   │   │   └── [gw]/page.tsx   # Main prediction view
│   │   │   └── backtest/
│   │   │       └── page.tsx        # Backtest results
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── tabs.tsx
│   │   │   │   └── ...
│   │   │   ├── PitchView.tsx       # Pitch layout
│   │   │   ├── PlayerCard.tsx      # Player on pitch
│   │   │   ├── ListView.tsx        # Table view
│   │   │   ├── GameweekSelector.tsx
│   │   │   ├── StatsHeader.tsx     # Total points, POTW
│   │   │   └── BacktestChart.tsx
│   │   ├── lib/
│   │   │   ├── api.ts              # API client
│   │   │   └── utils.ts            # shadcn/ui cn() helper
│   │   └── types/
│   │       ├── index.ts            # API types
│   │       └── constants.ts        # Imports shared/constants.json
│   ├── public/
│   │   └── jerseys/                # Team jersey images
│   ├── components.json             # shadcn/ui config
│   ├── package.json
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Database Schema

### Tables

```sql
-- Teams (20 PL teams)
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    fpl_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(10),
    strength_attack_home INTEGER,
    strength_attack_away INTEGER,
    strength_defence_home INTEGER,
    strength_defence_away INTEGER
);

-- Players (~700 players)
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    fpl_id INTEGER UNIQUE NOT NULL,
    team_id INTEGER REFERENCES teams(id),
    understat_id INTEGER,              -- For xG/xA matching
    web_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100),
    second_name VARCHAR(100),
    position VARCHAR(10) NOT NULL,     -- GKP, DEF, MID, FWD
    now_cost INTEGER,                  -- Current price (x10)
    status VARCHAR(20),                -- a, d, i, n, s, u
    chance_of_playing INTEGER,
    news TEXT,
    is_penalty_taker BOOLEAN DEFAULT FALSE,
    is_corner_taker BOOLEAN DEFAULT FALSE,
    is_freekick_taker BOOLEAN DEFAULT FALSE
);

-- Gameweeks (38 per season)
CREATE TABLE gameweeks (
    id SERIAL PRIMARY KEY,
    fpl_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(50),
    deadline TIMESTAMP,
    finished BOOLEAN DEFAULT FALSE,
    is_current BOOLEAN DEFAULT FALSE,
    is_next BOOLEAN DEFAULT FALSE
);

-- Fixtures (~380 per season)
CREATE TABLE fixtures (
    id SERIAL PRIMARY KEY,
    fpl_id INTEGER UNIQUE NOT NULL,
    gameweek_id INTEGER REFERENCES gameweeks(id),
    team_home_id INTEGER REFERENCES teams(id),
    team_away_id INTEGER REFERENCES teams(id),
    kickoff_time TIMESTAMP,
    difficulty_home INTEGER,
    difficulty_away INTEGER,
    team_h_score INTEGER,
    team_a_score INTEGER,
    finished BOOLEAN DEFAULT FALSE
);

-- Player gameweek stats (main data table)
CREATE TABLE player_gw_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(id),
    gameweek_id INTEGER REFERENCES gameweeks(id),
    fixture_id INTEGER REFERENCES fixtures(id),
    minutes INTEGER DEFAULT 0,
    goals_scored INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    clean_sheets INTEGER DEFAULT 0,
    goals_conceded INTEGER DEFAULT 0,
    own_goals INTEGER DEFAULT 0,
    penalties_saved INTEGER DEFAULT 0,
    penalties_missed INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    bonus INTEGER DEFAULT 0,
    bps INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    -- Underlying stats
    shots INTEGER DEFAULT 0,
    key_passes INTEGER DEFAULT 0,
    xg DECIMAL(5,2),                   -- From Understat
    xa DECIMAL(5,2),                   -- From Understat
    npxg DECIMAL(5,2),                 -- Non-penalty xG
    UNIQUE(player_id, gameweek_id)
);

-- Dream Team (ground truth)
CREATE TABLE dream_teams (
    id SERIAL PRIMARY KEY,
    gameweek_id INTEGER REFERENCES gameweeks(id),
    player_id INTEGER REFERENCES players(id),
    position_slot INTEGER,             -- 1-11
    points INTEGER,
    UNIQUE(gameweek_id, player_id)
);

-- Predictions
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    gameweek_id INTEGER REFERENCES gameweeks(id),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    total_predicted_points INTEGER,
    formation VARCHAR(10)              -- e.g., "4-5-1"
);

-- Predicted players
CREATE TABLE prediction_players (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES predictions(id),
    player_id INTEGER REFERENCES players(id),
    position_slot INTEGER,             -- 1-11
    predicted_points DECIMAL(5,2),
    predicted_minutes DECIMAL(5,2),
    start_probability DECIMAL(3,2),
    confidence DECIMAL(3,2)
);

-- Backtest results
CREATE TABLE backtest_results (
    id SERIAL PRIMARY KEY,
    gameweek_id INTEGER REFERENCES gameweeks(id),
    prediction_id INTEGER REFERENCES predictions(id),
    player_overlap INTEGER,            -- 0-11
    points_ratio DECIMAL(5,4),         -- predicted/actual
    actual_total INTEGER,
    predicted_total INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### Backend API (FastAPI)

```
GET  /api/health                       # Health check

# Gameweeks
GET  /api/gameweeks                    # List all gameweeks
GET  /api/gameweeks/current            # Current gameweek
GET  /api/gameweeks/{gw_id}            # Gameweek details

# Players
GET  /api/players                      # All players (with filters)
GET  /api/players/{player_id}          # Player details + history
GET  /api/players/top?gw={gw}&limit=50 # Top predicted players

# Predictions
GET  /api/predictions/{gw_id}          # Predicted XI for gameweek
POST /api/predictions/generate/{gw_id} # Trigger prediction generation

# Dream Team (actual)
GET  /api/dream-team/{gw_id}           # Actual dream team

# Backtest
GET  /api/backtest/summary             # Overall backtest metrics
GET  /api/backtest/{gw_id}             # Single GW backtest result
POST /api/backtest/run                 # Run full backtest

# Data Sync
POST /api/sync/fpl                     # Sync FPL data
POST /api/sync/understat               # Sync Understat xG/xA
```

---

## Data Ingestion Pipeline

### 1. FPL Data Sync (`services/fpl_client.py`)

```python
FPL_BASE = "https://fantasy.premierleague.com/api"

ENDPOINTS = {
    "bootstrap": "/bootstrap-static/",
    "fixtures": "/fixtures/",
    "live": "/event/{gw}/live/",
    "element": "/element-summary/{player_id}/",
    "dream_team": "/dream-team/{gw}/",
    "set_pieces": "/team/set-piece-notes/"
}
```

**Sync Order:**
1. Bootstrap → Teams, Players, Gameweeks
2. Fixtures → All fixtures
3. Live data → Player GW stats (for finished GWs)
4. Dream Team → Ground truth (for finished GWs)
5. Set pieces → Update penalty/corner takers

### 2. Understat xG/xA Sync (`services/understat_client.py`)

Use `understatapi` Python package to scrape:
- Player match-level xG, xA, npxG
- Match by player name + date to FPL player_id

---

## Feature Engineering (`services/feature_engineering.py`)

### Features per Player per GW

```python
ROLLING_WINDOWS = [3, 5, 8]  # Last N games

features = {
    # Form features (rolling)
    "points_rolling_{w}": "mean points over last {w} games",
    "minutes_rolling_{w}": "mean minutes over last {w}",
    "goals_rolling_{w}": "sum goals",
    "assists_rolling_{w}": "sum assists",
    "xg_rolling_{w}": "sum xG",
    "xa_rolling_{w}": "sum xA",
    "bonus_rolling_{w}": "sum bonus points",
    "bps_rolling_{w}": "mean BPS",

    # Consistency
    "starts_rolling_{w}": "games with >60 mins",
    "points_std_{w}": "volatility/explosiveness",

    # Fixture context
    "is_home": "home fixture",
    "opponent_strength": "opponent attack/defence strength",
    "fixture_difficulty": "FPL difficulty rating",

    # Player attributes
    "position": "GKP/DEF/MID/FWD",
    "is_penalty_taker": "penalty duty",
    "is_set_piece_taker": "corners/free kicks",
    "price": "current cost",

    # Team context
    "team_form": "team points last 5",
    "team_cs_rate": "clean sheet probability proxy",

    # Position-specific
    "saves_rolling": "GK only",
    "cs_rolling": "DEF/GK",
    "shots_rolling": "MID/FWD"
}
```

---

## ML Model Architecture

### Two-Stage Approach

**Stage 1: Minutes Model** (`ml/minutes_model.py`)
- Predict: `P(start)` and `E[minutes | start]`
- Model: LightGBM classifier + regressor
- Features: injury status, recent minutes, rotation patterns

**Stage 2: Points Model** (`ml/points_model.py`)
- Predict: `E[points | played]`
- Model: LightGBM regressor
- Features: form, xG/xA, fixture, position, set pieces

**Combined:**
```python
E[points] = P(start) * E[minutes]/90 * E[points | 90 mins played]
```

### Formation Solver (`ml/formation_solver.py`)

Optimize XI selection subject to:
- Exactly 1 GK
- 3-5 DEF
- 2-5 MID
- 1-3 FWD
- Total = 11 players

Use `scipy.optimize` or OR-Tools for ILP.

---

## Backtesting Harness (`services/backtest.py`)

```python
def run_backtest(start_gw: int, end_gw: int) -> BacktestSummary:
    """
    Rolling-origin backtest:
    - Train on GWs 1 to (gw-1)
    - Predict GW
    - Compare to actual dream team
    """
    results = []
    for gw in range(start_gw, end_gw + 1):
        # Train model on historical data
        model = train_model(max_gw=gw-1)

        # Generate prediction
        predicted_xi = model.predict_xi(gw)

        # Get actual dream team
        actual_xi = get_dream_team(gw)

        # Calculate metrics
        overlap = calculate_overlap(predicted_xi, actual_xi)
        points_ratio = sum(p.points for p in predicted_xi) / sum(p.points for p in actual_xi)

        results.append({
            "gw": gw,
            "overlap": overlap,
            "points_ratio": points_ratio
        })

    return BacktestSummary(results)
```

**Metrics Tracked:**
- `overlap@11`: Players matching (0-11)
- `points_ratio`: Predicted points / Actual points
- `overlap_by_position`: GK, DEF, MID, FWD breakdown
- `mean_overlap`, `std_overlap`
- `weeks_above_threshold`: Count of GWs with ≥9/11 overlap

---

## Frontend Components

### Key Pages

1. **`/predictions/[gw]`** - Main prediction view
   - PitchView with predicted XI
   - GameweekSelector to navigate
   - StatsHeader with total points, POTW
   - Toggle to ListView

2. **`/backtest`** - Backtest results dashboard
   - Line chart of overlap over time
   - Summary stats (avg overlap, avg points ratio)
   - Table of per-GW results

### Components

**`PitchView.tsx`**
- SVG/CSS pitch background
- Render PlayerCards in formation positions
- Support 4-5-1, 4-4-2, 3-5-2, 3-4-3, 5-4-1, 5-3-2

**`PlayerCard.tsx`**
- Team jersey (from `/public/jerseys/{team_id}.png`)
- Player name
- Points (predicted or actual)
- Optional: confidence indicator

**`GameweekSelector.tsx`**
- Left/right arrows
- Current GW display
- Jump to GW dropdown

---

## Implementation Phases

### Phase 1: Backend Foundation (Day 1-2)
1. Initialize backend project structure
2. Set up PostgreSQL + SQLAlchemy models
3. Create Alembic migrations
4. Implement FPL API client
5. Build data ingestion for bootstrap, fixtures, live stats
6. Write tests for data ingestion

### Phase 2: Feature Engineering (Day 2-3)
1. Build feature engineering pipeline
2. Create rolling stats calculations
3. Add Understat xG/xA integration
4. Test feature generation

### Phase 3: ML Models (Day 3-4)
1. Implement minutes prediction model
2. Implement points prediction model
3. Build formation solver (XI optimization)
4. Create training pipeline
5. Write model tests

### Phase 4: Backtesting (Day 4-5)
1. Build backtesting harness
2. Implement metrics calculation
3. Run initial backtest (GW 6-current)
4. Tune model for target accuracy
5. Store backtest results

### Phase 5: API Layer (Day 5)
1. Create FastAPI routes
2. Add prediction endpoints
3. Add backtest endpoints
4. Add data sync endpoints
5. Write API tests

### Phase 6: Frontend (Day 6-7)
1. Initialize Next.js project
2. Build PitchView component
3. Build PlayerCard component
4. Create predictions page
5. Create backtest dashboard
6. Add team jersey images
7. Style with Tailwind (FPL purple/green theme)

### Phase 7: Integration & Polish (Day 7-8)
1. Docker Compose setup
2. End-to-end testing
3. Documentation (README)
4. Final accuracy validation

---

## Key Files to Create (in order)

### Backend
1. `backend/requirements.txt`
2. `backend/app/config.py`
3. `backend/app/database.py`
4. `backend/app/models/*.py` (all models)
5. `backend/migrations/` (alembic init + initial)
6. `backend/app/services/fpl_client.py`
7. `backend/app/services/data_ingestion.py`
8. `backend/app/services/understat_client.py`
9. `backend/app/services/feature_engineering.py`
10. `backend/app/ml/minutes_model.py`
11. `backend/app/ml/points_model.py`
12. `backend/app/ml/formation_solver.py`
13. `backend/app/ml/train.py`
14. `backend/app/services/predictor.py`
15. `backend/app/services/backtest.py`
16. `backend/app/api/*.py` (all routes)
17. `backend/app/main.py`
18. `backend/tests/test_*.py`

### Frontend
1. `frontend/package.json`
2. `frontend/tailwind.config.js`
3. `frontend/src/types/index.ts`
4. `frontend/src/lib/api.ts`
5. `frontend/src/components/PlayerCard.tsx`
6. `frontend/src/components/PitchView.tsx`
7. `frontend/src/components/GameweekSelector.tsx`
8. `frontend/src/components/StatsHeader.tsx`
9. `frontend/src/components/ListView.tsx`
10. `frontend/src/app/layout.tsx`
11. `frontend/src/app/predictions/[gw]/page.tsx`
12. `frontend/src/app/backtest/page.tsx`
13. `frontend/public/jerseys/*.png`

### Root
1. `docker-compose.yml`
2. `.env.example`
3. `README.md`

---

## Dependencies

### Backend (`requirements.txt`)
```
fastapi==0.109.0
uvicorn==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
pydantic==2.5.3
httpx==0.26.0
pandas==2.1.4
numpy==1.26.3
scikit-learn==1.4.0
lightgbm==4.2.0
scipy==1.12.0
understatapi==0.7.0
pytest==7.4.4
pytest-asyncio==0.23.3
```

### Frontend (`package.json` dependencies)
```json
{
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "tailwindcss": "3.4.1",
    "recharts": "2.10.4"
  }
}
```

---

## Success Criteria

Before marking complete, verify:

1. **Backtest accuracy**: Run backtest on GW 6-19 (current season)
   - Average overlap ≥ 8.5/11 (77%)
   - Average points ratio ≥ 85%
   - At least 50% of weeks with ≥9/11 overlap

2. **Frontend**: Pitch view renders correctly with player cards

3. **Data flow**: FPL sync → DB → Features → Model → Prediction → API → Frontend

4. **Tests pass**: All backend tests green

---

## Unresolved Questions

None - ready to implement.
