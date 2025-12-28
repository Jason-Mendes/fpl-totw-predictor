#!/usr/bin/env node

/**
 * Commit Message Blocker Hook
 *
 * This hook prevents Claude from adding model signatures and attribution text
 * to git commit messages, enforcing the "Never add Claude contributions" rule
 * from CLAUDE.md and user instructions.
 *
 * BLOCKS THESE PATTERNS:
 * - Model signatures: "▝▜█████▛▘ Sonnet 4.5 · Claude Max"
 * - Partial matches: "Sonnet 4.5", "Claude Max"
 * - Box drawing characters: "▝▜█████▛▘"
 * - Attribution: "Generated with Claude Code"
 * - Co-authorship: "Co-Authored-By: Claude"
 *
 * DETECTION STRATEGY:
 * - Intercepts Bash tool commands (PreToolUse event)
 * - Detects git commit commands
 * - Extracts commit message from various formats:
 *   - Simple: git commit -m "message"
 *   - Heredoc: git commit -m "$(cat <<'EOF'...EOF)"
 *   - Multi-line messages
 * - Checks for prohibited patterns
 * - Blocks with helpful guidance if found
 *
 * Exit codes:
 * - 0: Success (no prohibited text or not a git commit)
 */

import { readFileSync, existsSync } from 'fs';
import path from 'path';

// Prohibited text patterns that should never appear in commit messages
const PROHIBITED_PATTERNS = [
  {
    name: 'model-signature-full',
    pattern: /▝▜█████▛▘.*Sonnet.*Claude Max/i,
    description: 'Full model signature with box characters'
  },
  {
    name: 'model-signature-partial-sonnet',
    pattern: /Sonnet\s+4\.5/i,
    description: 'Partial model signature (Sonnet 4.5)'
  },
  {
    name: 'model-signature-partial-claude-max',
    pattern: /Claude\s+Max/i,
    description: 'Partial model signature (Claude Max)'
  },
  {
    name: 'box-drawing-characters',
    pattern: /▝▜█████▛▘/,
    description: 'Box drawing characters from model signature'
  },
  {
    name: 'claude-code-attribution',
    pattern: /Generated with.*Claude Code/i,
    description: 'Claude Code attribution text'
  },
  {
    name: 'robot-emoji-attribution',
    pattern: /🤖\s*Generated with/i,
    description: 'Robot emoji with Claude Code attribution'
  },
  {
    name: 'claude-co-author',
    pattern: /Co-Authored-By:\s*Claude/i,
    description: 'Claude co-authorship attribution'
  },
  {
    name: 'anthropic-attribution',
    pattern: /claude\.com\/claude-code/i,
    description: 'Claude Code URL attribution'
  },
  {
    name: 'anthropic-email',
    pattern: /noreply@anthropic\.com/i,
    description: 'Anthropic email address in co-author'
  }
];

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

    // Timeout after 100ms if no input
    setTimeout(() => resolve({}), 100);
  });
}

// Extract commit message from git command
function extractCommitMessage(command) {
  if (!command || typeof command !== 'string') {
    return null;
  }

  // Check if this is a git commit command
  if (!command.includes('git commit')) {
    return null;
  }

  // Pattern 1: git commit -m "message" (simple quoted message)
  // Handle both single and double quotes
  const simpleQuotePatterns = [
    /git\s+commit[^"]*-m\s+"([^"]+)"/,  // Double quotes
    /git\s+commit[^']*-m\s+'([^']+)'/   // Single quotes
  ];

  for (const pattern of simpleQuotePatterns) {
    const match = command.match(pattern);
    if (match) {
      return match[1];
    }
  }

  // Pattern 2: git commit -m "$(cat <<'EOF'...EOF)" (heredoc format)
  const heredocPattern = /\$\(cat\s+<<'?EOF'?\s+([\s\S]*?)\s+EOF\s*\)/;
  const heredocMatch = command.match(heredocPattern);
  if (heredocMatch) {
    return heredocMatch[1];
  }

  // Pattern 3: git commit with -F or --file flag
  // Cannot check pre-commit without reading file, return null
  if (command.includes('-F ') || command.includes('--file')) {
    return null;
  }

  // Pattern 4: git commit --amend
  // Cannot check amended message pre-commit, return null
  if (command.includes('--amend')) {
    return null;
  }

  return null;
}

// Check if message contains prohibited text
function checkForProhibitedText(message) {
  if (!message || typeof message !== 'string') {
    return { found: false };
  }

  const violations = [];

  for (const { name, pattern, description } of PROHIBITED_PATTERNS) {
    const match = message.match(pattern);
    if (match) {
      violations.push({
        patternName: name,
        description,
        matchedText: match[0],
        patternString: pattern.toString()
      });
    }
  }

  return {
    found: violations.length > 0,
    violations
  };
}

// Generate user-friendly guidance
function generateGuidance(violations) {
  return {
    issue: 'Commit message contains prohibited model signature or attribution text',
    rule: 'Per CLAUDE.md: "Never add Claude contributions to commit messages"',
    violations: violations.map(v => ({
      type: v.description,
      found: v.matchedText
    })),
    properFormat: {
      title: 'Proper Commit Message Format (from CLAUDE.md):',
      structure: [
        'FUNCTIONALITY_CATEGORY: Brief description of change',
        '',
        '- Specific change 1 with technical details',
        '- Specific change 2 with implementation approach',
        '- Specific change 3 with affected components'
      ],
      examples: [
        '✅ GOOD: AUTHENTICATION: Add JWT token refresh mechanism',
        '✅ GOOD: DATABASE: Optimize order query performance with indexes',
        '✅ GOOD: UI ENHANCEMENT: Add loading states to checkout flow',
        '❌ BAD: fix: update checkout ▝▜█████▛▘ Sonnet 4.5 · Claude Max',
        '❌ BAD: Generated with Claude Code - fix authentication',
        '❌ BAD: Add feature\n\nCo-Authored-By: Claude <noreply@anthropic.com>'
      ]
    },
    functionalityCategories: [
      'AUTHENTICATION',
      'API INTEGRATION',
      'DATABASE',
      'UI ENHANCEMENT',
      'PERFORMANCE',
      'TESTING',
      'MAPS CHECKOUT',
      'STORE MANAGEMENT',
      'DRIVER NAVIGATION'
    ],
    reminder: 'Focus on WHAT was implemented and WHY, not WHO implemented it'
  };
}

// Main execution
async function main() {
  const hookData = await parseHookInput();

  const toolName = hookData.tool_name || '';
  const toolInput = hookData.tool_input || {};
  const command = toolInput.command || '';

  // Only check Bash tool commands
  if (toolName !== 'Bash') {
    process.exit(0);
  }

  // Extract commit message from git command
  const commitMessage = extractCommitMessage(command);

  // If no commit message could be extracted, allow operation
  if (!commitMessage) {
    process.exit(0);
  }

  // Check for prohibited text
  const result = checkForProhibitedText(commitMessage);

  if (result.found) {
    const guidance = generateGuidance(result.violations);

    const decision = {
      decision: 'block',
      reason: `Commit message contains ${result.violations.length} prohibited pattern(s). Model signatures and Claude attributions are not allowed in commit messages.`,
      additionalInfo: {
        commitMessagePreview: commitMessage.substring(0, 200) + (commitMessage.length > 200 ? '...' : ''),
        violations: result.violations,
        guidance,
        mandatoryRules: [
          '🚫 NEVER add model signatures (Sonnet 4.5, Claude Max, etc.)',
          '🚫 NEVER add "Generated with Claude Code"',
          '🚫 NEVER add "Co-Authored-By: Claude"',
          '🚫 NEVER add box drawing characters (▝▜█████▛▘)',
          '✅ ALWAYS use FUNCTIONALITY: format from CLAUDE.md',
          '✅ ALWAYS focus on WHAT changed and WHY'
        ],
        nextSteps: [
          '1. Remove all model signatures and attribution text',
          '2. Use proper FUNCTIONALITY_CATEGORY format',
          '3. Write specific, technical bullet points',
          '4. Focus on implementation details, not authorship'
        ]
      }
    };

    // Output JSON decision for Claude Code to process
    console.log(JSON.stringify(decision, null, 2));

    process.exit(0); // Let Claude Code handle the block decision
  }

  // No prohibited text found, allow commit
  process.exit(0);
}

// Run the hook
main().catch(error => {
  console.error('Commit message blocker error:', error);
  process.exit(1);
});
