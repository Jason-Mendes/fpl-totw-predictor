# FPL TOTW Hooks System

Claude Code hooks for the FPL Team of the Week project to enforce development best practices and prevent common mistakes.

## Available Hooks

### 1. Commit Message Blocker (`commit-message-blocker.js`)

**Purpose**: Prevents Claude from adding model signatures and attribution text to git commit messages.

**Triggers**: PreToolUse on Bash tool with `git commit` commands

**What it blocks**:
- Model signatures: `Sonnet 4.5`, `Claude Max`
- Attribution: `Generated with Claude Code`
- Co-authorship: `Co-Authored-By: Claude`
- Anthropic URLs/emails

**Example**:
```bash
# Blocked:
git commit -m "Fix bug\n\nGenerated with Claude Code"

# Allowed:
git commit -m "FEATURE: Add player prediction model\n\n- Implement LightGBM regressor\n- Add feature engineering pipeline"
```

### 2. Assumption Detector (`assumption-detector.js`)

**Purpose**: Prevents Claude from making assumptions without verification. Detects assumption-based language and prompts for verification.

**Triggers**: UserPromptSubmit

**What it detects**:
- Words: "probably", "maybe", "I think", "I believe", "likely"
- Phrases: "I don't see", "doesn't exist", "for now, let me"
- Dangerous patterns that bypass investigation

**Example**:
```
# Detected:
"I don't see this endpoint. For now, let me create a new one..."

# Suggested:
"Let me search the backend routes first to verify if this endpoint exists..."
```

### 3. Database Safety Guard (`database-safety-guard.js`)

**Purpose**: Prevents destructive PostgreSQL/SQLAlchemy/Alembic operations and ensures investigation-first approach.

**Triggers**: PreToolUse on Bash and Write tools

**What it blocks**:
- SQL: `TRUNCATE TABLE`, `DROP TABLE`, `DELETE FROM` (without WHERE)
- SQLAlchemy: `.drop_all()`, `.delete()` without where
- Alembic: `downgrade base`, `op.drop_table`
- Scripts: seed-database, reset-database, etc.

**Bypass** (User-only):
Add `# @UADO` to your file to bypass checks when explicitly authorized.

### 4. TypeScript Any Blocker (`typescript-as-any-blocker.js`)

**Purpose**: Prevents use of `any` type in TypeScript code, enforcing type safety.

**Triggers**: PreToolUse on Write, Edit, MultiEdit for `.ts`/`.tsx` files

**What it blocks**:
- `as any` assertions
- `: any` type annotations
- `Array<any>`, `Promise<any>` generics
- Catch blocks with `any` type

**Example**:
```typescript
// Blocked:
const data = response as any;

// Suggested:
interface ApiResponse { data: Player[]; }
const data: ApiResponse = response;
```

### 5. Infinite Retry Blocker (`infinite-retry-blocker.cjs`)

**Purpose**: Prevents infinite retry loops that can cause rate limiting and performance issues.

**What it detects**:
- Image `onError` handlers setting `target.src`
- API retry in catch blocks without backoff
- React useEffect state update loops
- WebSocket reconnection storms
- Fast polling intervals (<1000ms)

**Safe patterns allowed**:
- Exponential backoff
- Retry count limits
- useState for error handling

## Configuration

Hooks are configured in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "node .claude/hooks/commit-message-blocker.js" },
          { "type": "command", "command": "node .claude/hooks/database-safety-guard.js" }
        ]
      },
      {
        "matcher": "Write",
        "hooks": [
          { "type": "command", "command": "node .claude/hooks/typescript-as-any-blocker.js" },
          { "type": "command", "command": "node .claude/hooks/database-safety-guard.js" }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "node .claude/hooks/assumption-detector.js" }
        ]
      }
    ]
  }
}
```

## User Authorization Bypass (UADO)

For legitimate dangerous operations, users can add a bypass flag:

```python
# @UADO
# This script intentionally seeds the database
async def seed_database():
    ...
```

**UADO Meaning**: **U**ser **A**uthorized **D**angerous **O**peration

**Rules**:
- Only users can add UADO flags
- Claude must NEVER add these flags automatically
- Claude must NEVER suggest adding UADO flags

## Exit Codes

- **0**: Success / Allow operation
- **1**: Non-blocking warning (shown to user)
- **2**: Blocking error (operation prevented)

## Testing Hooks

```bash
# Test commit message blocker
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"Fix bug\""}}' | node .claude/hooks/commit-message-blocker.js

# Test with attribution (should block)
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"Fix\n\nGenerated with Claude Code\""}}' | node .claude/hooks/commit-message-blocker.js
```

## Troubleshooting

### Hook Not Working
1. Check if hook file exists and has correct permissions
2. Verify `settings.local.json` configuration is valid JSON
3. Check for syntax errors in hook files

### False Positives
1. **Database guard**: Add `# @UADO` if operation is intentional
2. **TypeScript any**: Use proper types instead of any
3. **Assumption detector**: Rephrase to avoid assumption language

---

**Adapted from**: [Etomart Hooks System](https://github.com/cognitoinc/DezCorp/Etomart-Fusion-V1_SUB-MODULES)
