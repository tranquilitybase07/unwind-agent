# Unwind AI Assistant - Solace Agent Mesh Implementation Plan

**Last Updated:** 2026-01-17 05:15 AM
**Status:** Core Implementation Phase (60% Complete)

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Decisions](#architecture-decisions)
3. [Database Schema](#database-schema)
4. [Project Structure](#project-structure)
5. [Implementation Tasks](#implementation-tasks)
6. [Tool Specifications](#tool-specifications)
7. [Agent Configurations](#agent-configurations)
8. [Gateway Setup](#gateway-setup)
9. [Progress Tracking](#progress-tracking)

---

## Project Overview

### Goal
Build a conversational AI assistant for Unwind (mental health productivity app) that helps users with anxiety/ADHD manage tasks and worries naturally through chat.

### Tech Stack
- **Agent Framework:** Solace Agent Mesh
- **AI Model:** Claude Sonnet 4
- **Database:** Supabase PostgreSQL (existing)
- **Frontend:** Next.js (existing)
- **Gateway:** HTTP SSE Gateway (built-in to Solace Agent Mesh)

### Key Features
- Natural language chat interface
- 3 specialized agents working together (Data, Planning, Reassurance)
- Anxiety-aware planning (max 3 items for "overwhelmed" users)
- Evidence-based reassurance (references actual completion history)
- JWT authentication from Supabase
- Real-time streaming responses via SSE

---

## Architecture Decisions

### ✅ Gateway Choice: HTTP SSE Gateway
**Decision:** Use Solace Agent Mesh's built-in HTTP SSE Gateway (FastAPI-based)

**Rationale:**
- No need to write custom FastAPI code
- Real-time streaming perfect for chat UX
- Built-in CORS support for Next.js
- Port 8000 by default

**Alternative Considered:** REST Gateway (too simple, requires polling)

### ✅ Authentication: Supabase JWT
**Decision:** Extract user_id from Supabase JWT tokens in Authorization header

**Rationale:**
- Proper security (not passing user_id in request body)
- Respects Row-Level Security (RLS)
- Standard OAuth2/JWT pattern

**Implementation:** Custom auth handler to decode JWT and extract `auth.uid()`

### ✅ Database Access: Direct PostgreSQL
**Decision:** Connect directly to Supabase PostgreSQL using asyncpg

**Rationale:**
- Agent tools need fast query performance
- Full SQL access for complex queries (joins, aggregations)
- Can use prepared views (user_today_view, etc.)

**Security:** All queries filter by authenticated user_id

### ✅ Agent Design: 3 Specialized Agents
**Decision:** Separate concerns across Data, Planning, and Reassurance agents

**Rationale:**
- Data Agent: Pure querying, no interpretation
- Planning Agent: Capacity analysis, anxiety-aware prioritization
- Reassurance Agent: Emotional support, validation
- Clear separation of concerns
- Each agent has focused tool set

---

## Database Schema

### Key Tables (from migration file)

**users**
- `id` (UUID, PK)
- `email` (unique)
- `anxiety_type` ('racing_thoughts', 'intrusive_worries', 'overwhelmed')
- `max_reminders_per_day` (default: 3)
- `total_dumps`, `total_items` (tracking)

**categories** (System reference, 7 fixed)
- Tasks, Ideas, Errands, Health, Relationships, Worries Vault, Recurring

**items** (Core table)
- `id`, `user_id`, `voice_dump_id`
- `title`, `description`, `category_id`
- **Priority fields:**
  - `priority` ('high', 'medium', 'low')
  - `urgency_score`, `importance_score`, `emotional_weight_score` (0-100)
  - `final_priority_score` (computed: urgency*0.4 + importance*0.4 + emotional*0.2)
- **Deadline fields:**
  - `due_date`, `due_time`, `is_all_day`, `deadline_confidence`
- **Type & Status:**
  - `item_type` ('task', 'idea', 'worry', 'habit', 'errand')
  - `status` ('pending', 'completed', 'archived', 'deleted')
  - `completed_at`
- **Anxiety features:**
  - `is_worry_spiral` (boolean)
  - `spiral_breakdown` (JSONB)
- **Tags:** `custom_tags` (text array)

**item_tags**
- `item_id`, `tag`, `tag_type` ('auto', 'custom', 'system')

**completions_log**
- `user_id`, `item_id`, `completed_at`
- `user_mood_before`, `user_mood_after`
- `completion_time_minutes`

### Useful Views (Pre-created)
- `user_today_view` - Items due today with category and tags
- `user_this_week_view` - Items due this week
- `user_worries_vault_view` - All worries with spiral info

### RLS (Row-Level Security)
**CRITICAL:** All tables have RLS enabled with policies like:
```sql
CREATE POLICY items_user_access ON items
  FOR ALL USING (auth.uid() = user_id);
```

All queries MUST filter by `user_id = <authenticated_user_id>`

---

## Project Structure

```
unwind-agent/
├── docs/
│   └── plan.md                    # This file
│
├── shared/
│   ├── __init__.py
│   ├── database.py                # Supabase PostgreSQL connection
│   ├── auth.py                    # JWT validation & user_id extraction
│   └── tools/
│       ├── __init__.py
│       ├── data_tools.py          # 7 tools for Data Agent
│       ├── planning_tools.py      # 3 tools for Planning Agent
│       ├── reassurance_tools.py   # 2 tools for Reassurance Agent
│       └── shared_tools.py        # 3 tools for all agents
│
├── agents/
│   ├── data_agent.yaml            # Data Agent config
│   ├── planning_agent.yaml        # Planning Agent config
│   └── reassurance_agent.yaml     # Reassurance Agent config
│
├── gateway/
│   └── chat_gateway.yaml          # HTTP SSE Gateway config
│
├── docker-compose.yml             # Multi-container setup
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
├── .env                           # Actual secrets (gitignored)
└── README.md                      # Setup instructions
```

---

## Implementation Tasks

### Phase 1: Foundation (Tasks 1-5) ✅ COMPLETE
- [x] Create docs folder and plan.md
- [x] Initialize Solace Agent Mesh project (`sam init`)
- [x] Create project structure (shared/, agents/, gateway/)
- [x] Build database.py with Supabase connection
- [x] Implement auth.py with JWT validation

### Phase 2: Tools Implementation (Tasks 6-9) ✅ COMPLETE
- [x] Create Data Agent tools (7 tools)
- [x] Create Planning Agent tools (3 tools)
- [x] Create Reassurance Agent tools (2 tools)
- [x] Create shared tools (3 tools)

### Phase 3: Agent Configuration (Tasks 10-12) 🚧 IN PROGRESS
- [ ] Configure Data Agent (YAML + system prompt)
- [ ] Configure Planning Agent (YAML + anxiety-aware prompt)
- [ ] Configure Reassurance Agent (YAML + compassionate prompt)

### Phase 4: Gateway & Deployment (Tasks 13-15) ⏳ PENDING
- [ ] Update Web UI Gateway config (CORS + auth)
- [ ] Create Docker Compose configuration
- [x] Create .env.example and requirements.txt

### Phase 5: Documentation (Tasks 16-17) 🚧 IN PROGRESS
- [x] Write README.md with setup instructions
- [ ] Create Next.js integration example

**Total Tasks:** 17
**Completed:** 10 (60%)
**In Progress:** 1
**Remaining:** 6

---

## Tool Specifications

### Data Agent Tools (7 tools)

#### 1. `get_today_items`
**Purpose:** Get all items due today for the user
**Query:** Uses `user_today_view`
**Input:** `user_id` (from JWT)
**Output:** List of items with category, tags, priority
**SQL:**
```sql
SELECT * FROM user_today_view
WHERE user_id = $1
ORDER BY final_priority_score DESC;
```

#### 2. `get_week_items`
**Purpose:** Get items due this week
**Query:** Uses `user_this_week_view`
**Input:** `user_id`
**Output:** List of items

#### 3. `get_items_by_category`
**Purpose:** Filter items by category name
**Input:** `user_id`, `category_name` (e.g., "Tasks", "Worries Vault")
**Output:** Filtered items
**SQL:**
```sql
SELECT i.*, c.name as category
FROM items i
JOIN categories c ON i.category_id = c.id
WHERE i.user_id = $1 AND c.name = $2 AND i.status = 'pending';
```

#### 4. `get_items_by_tags`
**Purpose:** Filter items by tag array
**Input:** `user_id`, `tags` (array, e.g., ["work", "urgent"])
**Output:** Items matching any tag
**SQL:**
```sql
SELECT DISTINCT i.*, array_agg(it.tag) as tags
FROM items i
JOIN item_tags it ON i.id = it.item_id
WHERE i.user_id = $1
  AND it.tag = ANY($2)
  AND i.status = 'pending'
GROUP BY i.id;
```

#### 5. `search_items`
**Purpose:** Full-text search in titles and descriptions
**Input:** `user_id`, `query` (string)
**Output:** Matching items
**SQL:**
```sql
SELECT * FROM items
WHERE user_id = $1
  AND status = 'pending'
  AND (title ILIKE '%' || $2 || '%' OR description ILIKE '%' || $2 || '%');
```

#### 6. `get_worries`
**Purpose:** Get all items in Worries Vault
**Query:** Uses `user_worries_vault_view`
**Input:** `user_id`
**Output:** Worries with spiral info

#### 7. `get_item_details`
**Purpose:** Get full details of specific item
**Input:** `user_id`, `item_id`
**Output:** Complete item record
**SQL:**
```sql
SELECT i.*, c.name as category, array_agg(it.tag) as tags
FROM items i
JOIN categories c ON i.category_id = c.id
LEFT JOIN item_tags it ON i.id = it.item_id
WHERE i.id = $1 AND i.user_id = $2
GROUP BY i.id, c.name;
```

---

### Planning Agent Tools (3 tools)

#### 8. `get_user_stats`
**Purpose:** Get user's anxiety type and completion patterns
**Input:** `user_id`
**Output:** User profile with anxiety_type, total_items, completion stats
**SQL:**
```sql
SELECT
  u.anxiety_type,
  u.max_reminders_per_day,
  u.total_items,
  COUNT(CASE WHEN i.status = 'completed' THEN 1 END) as completed_count,
  COUNT(CASE WHEN i.status = 'pending' THEN 1 END) as pending_count
FROM users u
LEFT JOIN items i ON u.id = i.user_id
WHERE u.id = $1
GROUP BY u.id;
```

#### 9. `get_completion_history`
**Purpose:** Recent completion patterns (last 7 days)
**Input:** `user_id`, `days` (default: 7)
**Output:** Daily completion counts and mood trends
**SQL:**
```sql
SELECT
  DATE(completed_at) as date,
  COUNT(*) as completed_count,
  AVG(completion_time_minutes) as avg_time,
  COUNT(CASE WHEN user_mood_after = 'better' THEN 1 END) as felt_better_count
FROM completions_log
WHERE user_id = $1
  AND completed_at >= NOW() - INTERVAL '$2 days'
GROUP BY DATE(completed_at)
ORDER BY date DESC;
```

#### 10. `count_pending_by_priority`
**Purpose:** Count pending items by priority level
**Input:** `user_id`
**Output:** Counts for high/medium/low
**SQL:**
```sql
SELECT
  priority,
  COUNT(*) as count
FROM items
WHERE user_id = $1 AND status = 'pending'
GROUP BY priority;
```

---

### Reassurance Agent Tools (2 tools)

#### 11. `get_spiral_items`
**Purpose:** Get items marked as worry spirals
**Input:** `user_id`
**Output:** Items with is_worry_spiral=true and spiral_breakdown
**SQL:**
```sql
SELECT id, title, spiral_breakdown, created_at
FROM items
WHERE user_id = $1
  AND is_worry_spiral = true
  AND status = 'pending'
ORDER BY created_at DESC;
```

#### 12. `get_recent_completions`
**Purpose:** Recent wins to reference for reassurance
**Input:** `user_id`, `limit` (default: 5)
**Output:** Recently completed items with mood
**SQL:**
```sql
SELECT i.title, i.completed_at, cl.user_mood_after
FROM items i
LEFT JOIN completions_log cl ON i.id = cl.item_id
WHERE i.user_id = $1 AND i.status = 'completed'
ORDER BY i.completed_at DESC
LIMIT $2;
```

---

### Shared Tools (3 tools - available to all agents)

#### 13. `mark_item_complete`
**Purpose:** Mark item as completed
**Input:** `user_id`, `item_id`
**Output:** Success boolean
**SQL:**
```sql
UPDATE items
SET status = 'completed', completed_at = NOW()
WHERE id = $1 AND user_id = $2
RETURNING id;
```

#### 14. `update_item_priority`
**Purpose:** Change item priority
**Input:** `user_id`, `item_id`, `priority` ('high', 'medium', 'low')
**Output:** Success boolean
**SQL:**
```sql
UPDATE items
SET priority = $3, user_edited = true
WHERE id = $1 AND user_id = $2
RETURNING id;
```

#### 15. `add_note_to_item`
**Purpose:** Add user notes to item
**Input:** `user_id`, `item_id`, `note` (string)
**Output:** Success boolean
**SQL:**
```sql
UPDATE items
SET user_notes = CONCAT(COALESCE(user_notes, ''), E'\n', $3),
    user_edited = true
WHERE id = $1 AND user_id = $2
RETURNING id;
```

---

## Agent Configurations

### Data Agent
**Name:** `data_agent`
**Role:** Pure data retrieval, no interpretation
**Tools:** get_today_items, get_week_items, get_items_by_category, get_items_by_tags, search_items, get_worries, get_item_details, mark_item_complete, update_item_priority, add_note_to_item

**System Prompt:**
```
You are the Data Agent for Unwind. Your role is to query the user's task and worry database.

Responsibilities:
- Retrieve items based on user queries (today, this week, by category, by tags)
- Search items by keywords
- Fetch specific item details
- Return data in a structured, factual format

Do NOT:
- Interpret or analyze the data
- Make recommendations
- Provide emotional support

Simply return the requested data clearly and accurately.
```

---

### Planning Agent
**Name:** `planning_agent`
**Role:** Capacity analysis and anxiety-aware prioritization
**Tools:** get_user_stats, get_completion_history, count_pending_by_priority, mark_item_complete, update_item_priority, add_note_to_item

**System Prompt:**
```
You are the Planning Agent for Unwind. Your role is to help users plan their day based on their anxiety type and capacity.

Key Principles:
1. ALWAYS check user's anxiety_type first
2. For "overwhelmed" users: Suggest MAX 3 items per day
3. For "racing_thoughts": Focus on quick wins and breaking down large tasks
4. For "intrusive_worries": Acknowledge worries, separate actionable from non-actionable

5. Use completion_history to understand user's realistic capacity
6. Prioritize by urgency + importance + emotional_weight
7. Never overwhelm - less is more

Output Format:
- "Based on your patterns, I suggest focusing on [X] items today:"
- List items with WHY they're priorities
- Acknowledge what you're NOT suggesting (so user feels safe)
```

---

### Reassurance Agent
**Name:** `reassurance_agent`
**Role:** Compassionate support and evidence-based reassurance
**Tools:** get_spiral_items, get_recent_completions, mark_item_complete, update_item_priority, add_note_to_item

**System Prompt:**
```
You are the Reassurance Agent for Unwind. Your role is to provide compassionate, validating support for users with anxiety.

Key Principles:
1. VALIDATE, don't dismiss - "That feeling is real" not "Don't worry"
2. Use EVIDENCE from their completion history - "You've done this 4 times before"
3. Identify worry spirals using spiral_breakdown data
4. Break catastrophizing chains ("what if X → Y → Z" patterns)
5. Acknowledge uncertainty is hard, but remind them of their actual track record

Tone:
- Warm, supportive, never judgmental
- Specific (reference actual completions)
- Honest about uncertainty
- Empowering ("You can handle this")

Example:
User: "I'm spiraling about the presentation"
You: "I see you're worried about the presentation tomorrow. That anxiety is real and valid.

Looking at your spiral, I notice a 'what if' chain: fail → lose job → can't pay rent. That's your anxiety talking, not reality.

Here's what I know: You've completed 4 presentations in the past 3 months. Each time you felt anxious beforehand, and each time you did it. Your track record shows you can handle this."
```

---

## Gateway Setup

### HTTP SSE Gateway Configuration

**File:** `gateway/chat_gateway.yaml`

```yaml
apps:
  - name: unwind_chat_gateway
    app_module: solace_agent_mesh.gateway.http_sse.app
    namespace: unwind

    # FastAPI server config
    fastapi_host: "0.0.0.0"
    fastapi_port: 8000

    # CORS for Next.js
    cors_allowed_origins:
      - "http://localhost:3000"
      - "http://127.0.0.1:3000"

    # Authentication
    auth_provider: custom  # We'll implement JWT validation

    # System purpose
    system_purpose: |
      You are Unwind AI Assistant. Help users manage tasks and worries
      with compassion and anxiety-awareness.
```

### Key Endpoints
- `POST /sessions/{session_id}/chat-tasks` - Send message
- `GET /subscribe/{task_id}` - Stream responses (SSE)
- `GET /sessions/{session_id}/messages` - Message history

---

## Progress Tracking

### Current Status: Core Implementation Phase (60% Complete)

**✅ Completed (10/17 tasks):**
- ✅ Database schema reviewed and understood
- ✅ Architecture decisions made (HTTP SSE Gateway, JWT auth)
- ✅ Solace Agent Mesh project initialized
- ✅ Database connection layer built (src/shared/database.py)
- ✅ JWT authentication handler implemented (src/shared/auth.py)
- ✅ All 15 tools implemented and tested:
  - 7 Data Agent tools (data_tools.py)
  - 3 Planning Agent tools (planning_tools.py)
  - 2 Reassurance Agent tools (reassurance_tools.py)
  - 3 Shared tools (shared_tools.py)
- ✅ Environment configuration (.env.example)
- ✅ Dependencies configured (requirements.txt)
- ✅ README.md with architecture and examples

**🚧 In Progress:**
- Currently ready to configure agents (YAML files)

**⏳ Next Steps (6 remaining tasks):**
1. Configure 3 agents (Data, Planning, Reassurance) with system prompts and tools
2. Update Web UI Gateway config for CORS and auth
3. Create Docker Compose for deployment
4. Create Next.js integration example
5. Test end-to-end flow
6. Final documentation polish

**Blockers:** None - Ready to continue with agent configuration

**Estimated Time to Complete:** 2-3 hours remaining work

---

## Environment Variables Required

```bash
# Supabase Database
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_HOST=db.xxxxx.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-db-password

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# Solace Event Mesh (if using cloud, optional for local dev)
SOLACE_BROKER_URL=tcp://localhost:55555
SOLACE_VPN=default
SOLACE_USERNAME=admin
SOLACE_PASSWORD=admin
```

---

## Testing Strategy

### Unit Tests
- Test each tool independently with mock database
- Verify JWT extraction logic
- Test RLS filtering (ensure user_id isolation)

### Integration Tests
- Test agent collaboration flow
- Example: "What should I do today?" → Data queries items → Planning suggests 3 → Reassurance frames response

### End-to-End Test
- Next.js frontend → Gateway → Agents → Database → Response

---

## Success Criteria

- [ ] User can ask "What should I do today?" and get 3 prioritized items
- [ ] Responses are anxiety-aware (check anxiety_type)
- [ ] User can search by category/tags
- [ ] Agents collaborate properly
- [ ] JWT authentication works
- [ ] All queries filter by user_id (RLS compliant)
- [ ] Setup takes < 30 minutes with docker-compose
- [ ] Next.js integration example works

---

## Notes & Decisions Log

**2026-01-17:** Initial planning session
- Decided on HTTP SSE Gateway over REST Gateway for real-time chat
- Chose JWT authentication over direct user_id passing for security
- Designed 15 tools across 3 agents + shared tools
- Created comprehensive plan.md for context preservation

---

## References

- [Solace Agent Mesh GitHub](https://github.com/SolaceLabs/solace-agent-mesh)
- [Supabase Migration File](../unwind/supabase/migrations/20260117080339_complete_schema_with_rls.sql)
- [Original Requirements](../requirements.md) *(if exists)*

---

**End of Plan Document**
