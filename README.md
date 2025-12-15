# 🏙️ Maintenance Debt Index (MDI) - Urban Infrastructure Credit Score

A comprehensive platform that treats urban infrastructure maintenance delays as accumulating financial debt, quantifies neglect using time-based compounding costs, and produces an **Urban Credit Score** for assets, wards, and cities.


## 🎯 Core Concepts
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/cc8833e3-c016-42fa-8856-70fbf60bc2be" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/a008e7d0-2061-4f8b-afb7-3ef0680cfeb9" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/42df5d66-3f99-4924-9ece-c4119907fec6" />



### Maintenance Debt
Maintenance Debt is the **additional cost incurred due to delayed maintenance** beyond an expected repair timeline. Debt grows **non-linearly** with time delay using compound interest formulas:

```
decay_cost = base_cost × (1 + decay_rate)^delay_days
maintenance_debt = decay_cost - base_cost
```

### MDI Score (0-100)
| Score | Category | Description |
|-------|----------|-------------|
| 90-100 | Excellent | Infrastructure well-maintained |
| 70-89 | Good | Minor delays, manageable debt |
| 50-69 | Fair | Significant delays accumulating |
| 30-49 | Poor | Critical maintenance needed |
| 0-29 | Critical | Severe neglect, emergency intervention required |

## 🔧 Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, SQLAlchemy, Celery, Redis |
| **Frontend** | React 18, Tailwind CSS, Mapbox GL, Recharts |
| **Database** | PostgreSQL 15 with PostGIS |
| **AI/NLP** | spaCy, OpenAI (optional) |

## 📁 Project Structure

```
hack-proto/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # REST API endpoints
│   │   ├── core/                # Config, DB, Debt Engine
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   ├── workers/             # Celery background tasks
│   │   ├── main.py              # FastAPI app
│   │   └── seed.py              # Sample data seeder
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API service layer
│   │   └── utils/               # Helper functions
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate
cd hack-proto

# Start all services
docker-compose up -d

# Seed sample data
docker-compose exec backend python -m app.seed

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup

#### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with PostGIS extension
- Redis

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env
# Edit .env with your database credentials

# Initialize database
python -c "from app.core.database import init_db; init_db()"

# Seed sample data
python -m app.seed

# Start API server
uvicorn app.main:app --reload --port 8000
```

#### Celery Workers (Separate terminals)

```bash
cd backend
venv\Scripts\activate

# Worker
celery -A app.workers.celery_worker worker --loglevel=info

# Beat scheduler (for daily calculations)
celery -A app.workers.celery_worker beat --loglevel=info
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📊 API Endpoints

### Assets
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/assets` | List all assets (paginated) |
| GET | `/api/v1/assets/map` | Get assets for map view |
| POST | `/api/v1/assets` | Create new asset |
| GET | `/api/v1/assets/{id}` | Get asset details |
| PUT | `/api/v1/assets/{id}` | Update asset |
| DELETE | `/api/v1/assets/{id}` | Delete asset |

### Issues
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/issues` | List issues (with filters) |
| POST | `/api/v1/issues` | Report new issue |
| PATCH | `/api/v1/issues/{id}/resolve` | Mark issue resolved |

### Debt
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/debt/asset/{id}` | Get asset debt details |
| GET | `/api/v1/debt/asset/{id}/history` | Get debt history |
| POST | `/api/v1/debt/simulate` | Simulate future debt |
| GET | `/api/v1/debt/city` | Get city-wide debt |

### Scores
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/scores/dashboard` | Get dashboard summary |
| GET | `/api/v1/scores/asset/{id}` | Get asset MDI score |
| GET | `/api/v1/scores/ward/{id}` | Get ward MDI score |
| GET | `/api/v1/scores/city` | Get city-wide score |
| GET | `/api/v1/scores/wards` | Get all ward scores |

### Explanations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/explain/asset/{id}` | Explain asset debt |
| GET | `/api/v1/explain/ward/{id}` | Explain ward score |

## 🧮 Debt Calculation Formula

```python
# 1. Calculate expected fix date
expected_fix_date = report_date + SLA_days

# 2. Calculate delay days
delay_days = max(0, current_date - expected_fix_date)

# 3. Calculate decay cost with compound growth
decay_cost = base_cost × (1 + decay_rate)^delay_days

# 4. Apply severity multiplier
effective_growth = (decay_cost/base_cost - 1) × severity_multiplier
final_cost = base_cost × (1 + effective_growth)

# 5. Calculate maintenance debt
maintenance_debt = final_cost - base_cost
```

### Default Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| `decay_rate` | 0.02 (2%) | Daily compound rate |
| `max_multiplier` | 10× | Cap on cost escalation |

### SLA Days by Asset Type
| Asset Type | SLA Days |
|------------|----------|
| Road | 14 |
| Drain | 7 |
| Streetlight | 3 |
| Bridge | 21 |
| Sidewalk | 10 |

## 🗺️ Frontend Features

1. **Dashboard** - City-wide MDI overview with charts
2. **Interactive Map** - Color-coded assets by health score
3. **Asset List** - Searchable, filterable asset management
4. **Asset Detail** - Debt breakdown, history, and projections
5. **Ward Rankings** - Compare ward performance
6. **Debt Simulator** - Visualize cost escalation over time

## 🚢 Deployment

### Vercel (Frontend)
```bash
cd frontend
npm run build
vercel deploy --prod
```

### Render (Backend)
1. Create a new Web Service
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`

### Database (Render/Supabase)
- Use Render PostgreSQL or Supabase (free tier available)
- Enable PostGIS extension
- Update `DATABASE_URL` environment variable

## ✅ Success Criteria

The system is successful if:
- ✅ A delayed asset **visibly increases cost over time**
- ✅ MDI score **drops as neglect increases**
- ✅ Judges can **visually understand "cost of waiting"**
- ✅ **Preventive maintenance becomes obviously cheaper**

## 📝 Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/mdi_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Optional
MAPBOX_TOKEN=your_mapbox_token
OPENAI_API_KEY=your_openai_key
```

## 📄 License

MIT License - See LICENSE file for details.

---

Built with ❤️ for urban infrastructure management
