#!/usr/bin/env node

/**
 * Database Safety Guard Hook (PostgreSQL/SQLAlchemy/Alembic)
 *
 * This hook prevents destructive database operations and ensures
 * that Claude investigates the current state before making assumptions
 * about what needs to be done.
 *
 * Adapted for PostgreSQL/SQLAlchemy/Alembic from the MongoDB version.
 *
 * Exit codes:
 * - 0: Success (safe operation)
 * - 2: Blocking error (dangerous operation detected)
 */

import { readFileSync, existsSync } from 'fs';
import path from 'path';

// Dangerous database operations to block (PostgreSQL/SQLAlchemy/Alembic)
const DANGEROUS_OPERATIONS = {
  commands: [
    // SQL dangerous operations
    /TRUNCATE\s+TABLE/i,
    /DROP\s+TABLE/i,
    /DROP\s+DATABASE/i,
    /DELETE\s+FROM\s+\w+\s*;/i,  // DELETE without WHERE clause
    /DELETE\s+FROM\s+\w+\s*$/i,  // DELETE without WHERE at end of string

    // SQLAlchemy dangerous operations
    /\.drop_all\(\)/i,
    /\.delete\(\)(?!\s*\.where)/i,  // delete() without where clause
    /session\.execute.*DELETE\s+FROM/i,
    /session\.execute.*TRUNCATE/i,
    /session\.execute.*DROP/i,
    /Base\.metadata\.drop_all/i,
    /engine\.execute.*DROP/i,
    /engine\.execute.*TRUNCATE/i,

    // Alembic dangerous operations
    /alembic\s+downgrade\s+base/i,
    /alembic\s+downgrade\s+-\d+/i,  // Downgrade multiple revisions
    /op\.drop_table/i,
    /op\.drop_column/i,
    /op\.drop_index/i,
    /op\.drop_constraint/i,

    // Seed/reset scripts
    /seed.*database/i,
    /reset.*database/i,
    /init.*database/i,
    /populate.*database/i,
    /clear.*database/i,

    // Python script execution patterns
    /python.*seed/i,
    /python.*reset/i,
    /python.*init.*data/i,
    /python.*populate/i,

    // FastAPI/uvicorn with dangerous scripts
    /uvicorn.*seed/i,
    /uvicorn.*reset/i
  ],

  scripts: [
    'seed-database',
    'reset-database',
    'clean-database',
    'init-database',
    'populate-database',
    'clear-data'
  ],

  filePatterns: [
    /seed.*?\.(py)$/,
    /reset.*?\.(py)$/,
    /populate.*?\.(py)$/,
    /init.*?data.*?\.(py)$/,
    /clear.*?data.*?\.(py)$/
  ]
};

// Safe investigation commands
const SAFE_ALTERNATIVES = {
  'seed': 'Create a verification script to check existing data first',
  'reset': 'Query the database to understand current state',
  'drop': 'Use SELECT queries to investigate what data exists',
  'delete': 'Use SELECT COUNT(*) to see how many records would be affected',
  'truncate': 'Check table contents with SELECT before truncating',
  'populate': 'Check if data already exists before adding more',
  'downgrade': 'Review migration history with alembic history before downgrading'
};

// Parse stdin for hook data
async function parseHookInput() {
  let inputData = '';

  return new Promise((resolve) => {
    process.stdin.on('data', (chunk) => {
      inputData += chunk;
    });

    process.stdin.on('end', () => {
      try {
        resolve(JSON.parse(inputData));
      } catch (e) {
        resolve({});
      }
    });

    setTimeout(() => resolve({}), 100);
  });
}

// Check if command is dangerous
function checkCommand(command) {
  const issues = [];

  // Check against dangerous patterns
  DANGEROUS_OPERATIONS.commands.forEach(pattern => {
    if (pattern.test(command)) {
      issues.push({
        type: 'command',
        pattern: pattern.toString(),
        match: command.match(pattern)?.[0] || 'dangerous operation'
      });
    }
  });

  // Check for dangerous script names
  DANGEROUS_OPERATIONS.scripts.forEach(script => {
    if (command.includes(script)) {
      issues.push({
        type: 'script',
        pattern: script,
        match: script
      });
    }
  });

  return issues;
}

// Check for user authorization bypass
function hasUserAuthorization(content) {
  const authPatterns = [
    /---UADO/i,
    /@UADO/i,
    /\/\/\s*@UADO/i,
    /\/\*.*@UADO.*\*\//i,
    /#\s*@UADO/i
  ];

  return authPatterns.some(pattern => pattern.test(content));
}

// Check if file content contains dangerous operations
function checkFileContent(content, filePath) {
  // First check if user has explicitly authorized dangerous operations
  if (hasUserAuthorization(content)) {
    return []; // User authorized - skip all checks
  }

  const issues = [];
  const lines = content.split('\n');

  lines.forEach((line, index) => {
    DANGEROUS_OPERATIONS.commands.forEach(pattern => {
      if (pattern.test(line)) {
        // Skip if it's in a comment
        const pythonCommentIndex = line.indexOf('#');
        const matchIndex = line.search(pattern);

        if (pythonCommentIndex === -1 || matchIndex < pythonCommentIndex) {
          issues.push({
            line: index + 1,
            text: line.trim(),
            pattern: pattern.toString()
          });
        }
      }
    });
  });

  // Check if this is a seed/reset script
  const fileName = path.basename(filePath);
  DANGEROUS_OPERATIONS.filePatterns.forEach(pattern => {
    if (pattern.test(fileName)) {
      issues.push({
        type: 'filename',
        pattern: pattern.toString(),
        fileName
      });
    }
  });

  return issues;
}

// Generate investigation guidance
function generateInvestigationGuidance(issues) {
  const guidance = [];

  guidance.push('Required Investigation Steps:');
  guidance.push('  1. Check what data currently exists in the database');
  guidance.push('  2. Understand the current state before making changes');
  guidance.push('  3. Create verification scripts instead of seed scripts');
  guidance.push('  4. Query specific tables to see their contents');
  guidance.push('');
  guidance.push('Safe Alternatives:');

  const uniqueTypes = new Set(issues.map(i => i.match || i.fileName || 'unknown'));
  uniqueTypes.forEach(type => {
    if (type && typeof type === 'string') {
      const key = Object.keys(SAFE_ALTERNATIVES).find(k =>
        type.toLowerCase().includes(k)
      );
      if (key) {
        guidance.push(`  Instead of ${type}: ${SAFE_ALTERNATIVES[key]}`);
      }
    }
  });

  guidance.push('');
  guidance.push('Example Investigation Script (Python/SQLAlchemy):');
  guidance.push('  ```python');
  guidance.push('  # Check existing data first');
  guidance.push('  from sqlalchemy import select, func');
  guidance.push('  from app.database import get_session');
  guidance.push('  from app.models import Player, Team, Gameweek');
  guidance.push('  ');
  guidance.push('  async with get_session() as session:');
  guidance.push('      player_count = await session.scalar(select(func.count(Player.id)))');
  guidance.push('      team_count = await session.scalar(select(func.count(Team.id)))');
  guidance.push('      print(f"Found {player_count} players, {team_count} teams")');
  guidance.push('  ```');

  return guidance.join('\n');
}

// Generate Claude instructions for database safety
function generateClaudeInstructions(issues) {
  const guidance = [];

  guidance.push('Database Safety Protocol (PostgreSQL/SQLAlchemy)');
  guidance.push('================================================');
  guidance.push('Dangerous database operation detected!');
  guidance.push('');
  guidance.push('Blocked operations:');
  issues.forEach(issue => {
    guidance.push(`  ${issue.match} (${issue.type || 'dangerous pattern'})`);
  });
  guidance.push('');

  guidance.push('REQUIRED ACTIONS FOR CLAUDE:');
  guidance.push('');
  guidance.push('1. **FIRST: Check what\'s in the database**');
  guidance.push('   Run investigation queries:');
  guidance.push('   ```python');
  guidance.push('   # In Python shell or script');
  guidance.push('   from app.database import get_session');
  guidance.push('   from app.models import Player, Team, Gameweek');
  guidance.push('   from sqlalchemy import select, func');
  guidance.push('   ');
  guidance.push('   async with get_session() as session:');
  guidance.push('       result = await session.execute(select(func.count()).select_from(Player))');
  guidance.push('       print(f"Players: {result.scalar()}")');
  guidance.push('   ```');
  guidance.push('');
  guidance.push('2. **ANALYZE the output to determine:**');
  guidance.push('   - How many players exist?');
  guidance.push('   - How many teams exist?');
  guidance.push('   - How many gameweeks are synced?');
  guidance.push('   - Is the database empty or populated?');
  guidance.push('');
  guidance.push('3. **DECIDE based on findings:**');
  guidance.push('   - If database is EMPTY: Proceed with seeding/initialization');
  guidance.push('   - If database has DATA: Use existing data or create targeted updates');
  guidance.push('   - If specific data is MISSING: Create targeted scripts to add only what\'s needed');
  guidance.push('');

  guidance.push('EXAMPLES OF SAFE APPROACHES:');
  guidance.push('   "If no players found, sync from FPL API"');
  guidance.push('   "If no teams found, seed team data"');
  guidance.push('   "If specific gameweek missing, sync that gameweek only"');
  guidance.push('');

  guidance.push('DO NOT run seed/reset commands without verification!');
  guidance.push('This follows the user\'s instruction: "always before doping any changes to the db, first see whats in the db"');
  guidance.push('');
  guidance.push('BYPASS MECHANISM (USER-ONLY):');
  guidance.push('   If the user has explicitly approved dangerous operations,');
  guidance.push('   they can add one of these short flags to the file:');
  guidance.push('   # @UADO  or  ---UADO');
  guidance.push('   Claude should NEVER add these flags automatically!');
  guidance.push('   Only the user can authorize bypassing safety checks!');

  return guidance.join('\n');
}

// Main execution
async function main() {
  const hookData = await parseHookInput();

  const toolName = hookData.tool_name || '';
  const toolInput = hookData.tool_input || {};

  // Check Bash commands
  if (toolName === 'Bash') {
    const command = toolInput.command || '';
    const issues = checkCommand(command);

    if (issues.length > 0) {
      // Use PermissionDecision format to ask for user confirmation
      const decision = {
        decision: "ask",
        reason: `Potentially destructive database operation detected: ${issues.map(i => i.match).join(', ')}. Please confirm if you want to proceed.`,
        additionalInfo: {
          dangerousPatterns: issues.map(issue => ({
            pattern: issue.match,
            regex: issue.pattern
          })),
          guidance: generateClaudeInstructions(issues)
        }
      };

      // Output JSON decision for Claude Code to process
      console.log(JSON.stringify(decision, null, 2));

      process.exit(0); // Let Claude Code handle the permission decision
    }
  }

  // Check file writes for dangerous scripts - ALLOW creation but provide guidance
  if (toolName === 'Write' || toolName === 'MultiEdit') {
    const filePath = toolInput.file_path || toolInput.filePath || '';

    // Skip test files, frontend files, and other safe file types
    const skipPatterns = [
      /\.test\./,
      /\.spec\./,
      /test_.*\.py$/,
      /__tests__\//,
      /\.md$/,
      /\.json$/,
      /\.txt$/,
      /\.tsx$/,
      /\.jsx$/,
      /\.css$/,
      /\.scss$/,
      /frontend\//,
      /components\//,
      /pages\//,
      /types\//,
      /schemas\//,  // Pydantic schemas are safe
      /constants\//
    ];

    const shouldSkip = skipPatterns.some(pattern => pattern.test(filePath));
    if (shouldSkip) {
      process.exit(0); // Skip checking frontend files and documentation
    }

    let content = '';

    if (toolName === 'Write') {
      content = toolInput.content || '';
    } else if (toolInput.edits) {
      content = toolInput.edits.map(e => e.new_string || '').join('\n');
    }

    const issues = checkFileContent(content, filePath);

    if (issues.length > 0) {
      console.log('Database Script Safety Notice');
      console.log('================================');
      console.log('Script created successfully');
      console.log('');
      console.log(`Created: ${path.basename(filePath)}`);

      if (issues.some(i => i.type === 'filename')) {
        console.log(`Contains potentially destructive operations`);
      }

      const codeIssues = issues.filter(i => i.line);
      if (codeIssues.length > 0) {
        console.log('Potentially dangerous operations detected:');
        codeIssues.forEach(issue => {
          console.log(`  Line ${issue.line}: ${issue.text.substring(0, 50)}...`);
        });
      }

      console.log('');
      console.log('IMPORTANT - Please review this script before running:');
      console.log('');
      console.log('1. FIRST: Review the script content to understand what it does');
      console.log(`   cat ${filePath}`);
      console.log('');
      console.log('2. SECOND: Check your database state');
      console.log('   python -c "from app.database import ...; # run count queries"');
      console.log('');
      console.log('3. THIRD: If you\'re comfortable with the script, run it:');
      console.log(`   python ${filePath}`);
      console.log('');
      console.log('4. FOURTH: Tell Claude the output in your next prompt so it can continue');
      console.log('   Example: "I ran the script and got: [paste output here]"');
      console.log('');
      console.log('This approach ensures safety while allowing script creation');
      console.log('The script is created but you control when/if it runs');

      // ALLOW the creation (exit 1) but show guidance message
      process.exit(1);
    }
  }

  process.exit(0);
}

// Run the hook
main().catch(error => {
  console.error('Hook error:', error);
  process.exit(1);
});
