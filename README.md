# Unwind AI Assistant - Solace Agent Mesh

A conversational AI assistant for mental health productivity, built with Solace Agent Mesh. Helps users with anxiety/ADHD manage tasks and worries through natural chat with anxiety-aware planning and compassionate support.

## Project Status

**Current Phase:** Core Implementation (60% Complete)

### ✅ Completed
- [x] Solace Agent Mesh project initialization
- [x] Database connection layer (asyncpg + Supabase PostgreSQL)
- [x] JWT authentication handler (Supabase tokens)
- [x] All 15 database tools implemented:
  - 7 Data Agent tools (query items, search, filter)
  - 3 Planning Agent tools (user stats, completion history)
  - 2 Reassurance Agent tools (worry spirals, recent wins)
  - 3 Shared tools (mark complete, update priority, add notes)
- [x] Project structure and dependencies

### 🚧 In Progress
- [ ] Agent configurations (Data, Planning, Reassurance)
- [ ] Web UI Gateway setup with CORS
- [ ] Docker Compose for deployment
- [ ] Testing and documentation

---

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL (Supabase account)
- Anthropic API key

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

**Required environment variables:**
- `LLM_SERVICE_API_KEY` - Your Anthropic API key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_DB_HOST` - Database host from Supabase
- `SUPABASE_DB_PASSWORD` - Database password
- `SUPABASE_JWT_SECRET` - JWT secret for token validation

See `.env.example` for complete list.

### 3. Run the Agent Mesh

```bash
sam run
```

The Web UI Gateway will be available at `http://localhost:8000`

---

## Architecture

### Multi-Agent System

```
┌─────────────────┐
│   Next.js App   │
│  (Frontend)     │
└────────┬────────┘
         │ HTTP/SSE
         ▼
┌─────────────────┐
│  Web UI Gateway │ ← Port 8000 (FastAPI + SSE)
│  (Built-in)     │
└────────┬────────┘
         │ A2A Protocol
         ▼
┌─────────────────────────────────────────┐
│         Solace Event Mesh (Dev Mode)     │
└─────────────────────────────────────────┘
         │
         ├──────┬──────┬──────┐
         ▼      ▼      ▼      ▼
    ┌────┐  ┌────┐  ┌────┐
    │Data│  │Plan│  │Rass│
    └─┬──┘  └─┬──┘  └─┬──┘
      │       │       │
      └───────┴───────┘
              │
              ▼
    ┌──────────────────┐
    │ Supabase Postgres │
    │  (with RLS)       │
    └──────────────────┘
```

### Three Specialized Agents

1. **Data Agent**
   - Queries database for items, tasks, worries
   - Filters by category, tags, dates
   - Full-text search
   - No interpretation, just data retrieval

2. **Planning Agent**
   - Analyzes user's anxiety type
   - Checks completion patterns
   - Suggests realistic daily plans
   - **Anxiety-aware**: Max 3 items for "overwhelmed" users

3. **Reassurance Agent**
   - Identifies worry spirals
   - Provides evidence-based reassurance
   - References actual completion history
   - **Compassionate tone**: Validates, doesn't dismiss

---

## Database Tools

### Data Agent (7 tools)
- `get_today_items(user_id)` - Items due today
- `get_week_items(user_id)` - Items due this week
- `get_items_by_category(user_id, category_name)` - Filter by category
- `get_items_by_tags(user_id, tags[])` - Filter by tags
- `search_items(user_id, query)` - Full-text search
- `get_worries(user_id)` - All worries
- `get_item_details(user_id, item_id)` - Detailed item info

### Planning Agent (3 tools)
- `get_user_stats(user_id)` - Anxiety type, completion rate
- `get_completion_history(user_id, days)` - Recent patterns
- `count_pending_by_priority(user_id)` - Pending item counts

### Reassurance Agent (2 tools)
- `get_spiral_items(user_id)` - Worry spirals with breakdown
- `get_recent_completions(user_id, limit)` - Recent wins

### Shared Tools (3 tools)
- `mark_item_complete(user_id, item_id)` - Mark as done
- `update_item_priority(user_id, item_id, priority)` - Change priority
- `add_note_to_item(user_id, item_id, note)` - Add notes

---

## Security

### Row-Level Security (RLS)
All database queries filter by `user_id` extracted from Supabase JWT tokens:

1. Frontend sends `Authorization: Bearer <jwt>` header
2. Gateway extracts user_id from JWT
3. All queries include `WHERE user_id = $authenticated_user_id`
4. Supabase RLS policies enforce isolation

**No user can access another user's data.**

---

## File Structure

```
unwind-agent/
├── configs/
│   ├── agents/
│   │   └── main_orchestrator.yaml    # TODO: Configure agents
│   ├── gateways/
│   │   └── webui.yaml                # Web UI Gateway config
│   ├── services/
│   │   └── platform.yaml             # Platform service
│   ├── shared_config.yaml
│   └── logging_config.yaml
│
├── src/
│   └── shared/
│       ├── database.py               # ✅ Async PostgreSQL connection
│       ├── auth.py                   # ✅ JWT validation
│       └── tools/
│           ├── data_tools.py         # ✅ 7 data query tools
│           ├── planning_tools.py     # ✅ 3 planning tools
│           ├── reassurance_tools.py  # ✅ 2 reassurance tools
│           └── shared_tools.py       # ✅ 3 shared tools
│
├── docs/
│   └── plan.md                       # Comprehensive implementation plan
│
├── .env                              # Your secrets (gitignored)
├── .env.example                      # Template
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

---

## Example Conversations

### Daily Planning
```
User: "What should I focus on today?"

Data Agent → Queries today's items (8 found)
Planning Agent → User has anxiety_type='overwhelmed', suggests max 3
Reassurance Agent → Frames response compassionately

Response:
"I see you have 8 things for today, but let's focus on just 3:
1. Finish the proposal (work, due today, high priority)
2. Call mom (relationships, you've been thinking about this)
3. Buy groceries (errand, quick win)

The other 5 are safely stored for later. You don't need to think about them now."
```

### Anxiety Support
```
User: "I'm spiraling about the presentation tomorrow"

Data Agent → Finds item "presentation tomorrow"
Reassurance Agent → Checks spiral_breakdown, sees catastrophizing
Planning Agent → Extracts actionable steps

Response:
"I see you're worried about the presentation. That anxiety is real and valid.

Looking at your spiral, I notice a 'what if' chain: fail → lose job → can't pay rent. That's anxiety talking, not reality.

Here's what's actionable:
- Review slides (30 min)
- Practice once (20 min)

You've completed 4 presentations before. Your anxiety says you can't, but your history shows you can."
```

---

## Next Steps

1. **Configure Agents** - Create YAML configs for Data, Planning, Reassurance agents
2. **Update Gateway** - Add CORS for Next.js frontend
3. **Testing** - Test tools with sample data
4. **Docker** - Create docker-compose.yml for easy deployment
5. **Frontend Integration** - Next.js example API routes

See `docs/plan.md` for detailed implementation roadmap.

---

## Documentation

- **Full Plan:** [docs/plan.md](docs/plan.md) - Complete implementation plan with SQL queries, agent prompts, progress tracking
- **Supabase Schema:** [../unwind/supabase/migrations/](../unwind/supabase/migrations/) - Database schema with RLS policies

---

## Tech Stack

- **Agent Framework:** Solace Agent Mesh 1.13.6
- **AI Model:** Claude Sonnet 4
- **Database:** Supabase PostgreSQL (asyncpg)
- **Authentication:** Supabase JWT
- **Gateway:** Built-in HTTP SSE Gateway (FastAPI)
- **Event Mesh:** Solace (dev mode - no external broker)

---

## License

MIT

---

## Support

For issues or questions about:
- **Solace Agent Mesh:** [GitHub Issues](https://github.com/SolaceLabs/solace-agent-mesh/issues)
- **This Project:** See docs/plan.md for architecture decisions and implementation details
