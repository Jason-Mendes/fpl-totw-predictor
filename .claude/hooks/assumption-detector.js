#!/usr/bin/env node

/**
 * Assumption Detector Hook
 * 
 * This hook prevents Claude from making assumptions and ensures proper
 * investigation before making changes. It detects assumption-based language
 * and prompts for verification first.
 * 
 * The problem this solves:
 * - Claude saying "I don't see X endpoint" without searching
 * - Using "probably", "maybe", "for now" without verification
 * - Making changes based on assumptions rather than facts
 * 
 * Exit codes:
 * - 0: No assumptions detected or user approved action
 * - Uses PermissionDecision "ask" to prompt user for verification
 */

import { readFileSync, existsSync } from 'fs';
import path from 'path';

// Assumption patterns that indicate Claude is guessing instead of verifying
const ASSUMPTION_PATTERNS = [
  // Direct assumption words
  /\bprobably\b/i,
  /\bmaybe\b/i,
  /\bcould be\b/i,
  /\bmight be\b/i,
  /\bseems like\b/i,
  /\bappears to be\b/i,
  /\bassume\b/i,
  /\blikely\b/i,
  /\bpossibly\b/i,
  /\bpresumably\b/i,
  /\bI think\b/i,
  /\bI believe\b/i,
  /\bI suspect\b/i,
  
  // Dangerous assumption phrases that led to the driver API problem
  /I don't see.*\. (The|For now|Let me)/i,
  /may be incorrect\. For now/i,
  /doesn't exist\. (For now|Let me)/i,
  /not implemented\. (For now|I'll)/i,
  /missing\. (For now|Let me)/i,
  
  // Action phrases that bypass investigation
  /for now, let me/i,
  /for the moment/i,
  /temporarily/i,
  /as a workaround/i,
  /quick fix/i,
  
  // Endpoint/code existence assumptions
  /I don't see.*endpoint/i,
  /doesn't appear to exist/i,
  /seems to be missing/i,
  /may not exist/i
];

// Verification suggestions based on assumption type
const VERIFICATION_SUGGESTIONS = {
  'endpoint': [
    'Search backend routes with Grep tool',
    'Check API documentation or route files',
    'Verify actual endpoint structure in controllers'
  ],
  'function': [
    'Search codebase for function definition',
    'Check imports and module exports',
    'Verify function signature and location'
  ],
  'component': [
    'Search for existing component in submodules',
    'Check component directory structure',
    'Verify if component needs to be migrated'
  ],
  'general': [
    'Use Search/Grep tools to verify existence',
    'Read relevant files to understand current implementation',
    'Check documentation or related code first'
  ]
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

// Analyze text for assumption patterns
function detectAssumptions(text) {
  const assumptions = [];
  
  ASSUMPTION_PATTERNS.forEach(pattern => {
    const matches = text.match(new RegExp(pattern.source, pattern.flags + 'g'));
    if (matches) {
      matches.forEach(match => {
        assumptions.push({
          pattern: pattern.toString(),
          text: match,
          context: getContextAroundMatch(text, match)
        });
      });
    }
  });
  
  return assumptions;
}

// Get context around the matched assumption text
function getContextAroundMatch(text, match) {
  const index = text.indexOf(match);
  const start = Math.max(0, index - 50);
  const end = Math.min(text.length, index + match.length + 50);
  return text.substring(start, end).trim();
}

// Determine verification type based on assumption content
function getVerificationType(assumptionText) {
  if (/endpoint|api|route/i.test(assumptionText)) return 'endpoint';
  if (/function|method|call/i.test(assumptionText)) return 'function';
  if (/component|jsx|tsx/i.test(assumptionText)) return 'component';
  return 'general';
}

// Generate verification suggestions
function generateVerificationSuggestions(assumptions) {
  const suggestions = [];
  const verificationTypes = new Set();
  
  assumptions.forEach(assumption => {
    const type = getVerificationType(assumption.text);
    verificationTypes.add(type);
  });
  
  verificationTypes.forEach(type => {
    const typeSuggestions = VERIFICATION_SUGGESTIONS[type] || VERIFICATION_SUGGESTIONS.general;
    suggestions.push(...typeSuggestions);
  });
  
  return [...new Set(suggestions)]; // Remove duplicates
}

// Generate user-friendly assumption explanation
function generateAssumptionExplanation(assumptions) {
  const explanations = [];
  
  assumptions.forEach(assumption => {
    if (/I don't see.*endpoint/i.test(assumption.text)) {
      explanations.push('🔍 You mentioned not seeing an endpoint - should I search the backend routes first?');
    } else if (/may be incorrect/i.test(assumption.text)) {
      explanations.push('⚠️ You suggested something "may be incorrect" - should I verify the actual implementation?');
    } else if (/for now, let me/i.test(assumption.text)) {
      explanations.push('🚨 You\'re about to make a temporary fix - should I investigate the root cause first?');
    } else if (/probably|maybe|likely/i.test(assumption.text)) {
      explanations.push('🤔 You used uncertain language - should I verify this assumption?');
    } else {
      explanations.push(`📝 Detected assumption: "${assumption.text}" - should I verify first?`);
    }
  });
  
  return explanations;
}

// Main execution
async function main() {
  const hookData = await parseHookInput();
  
  // This hook works on UserPromptSubmit to catch assumption language in responses
  const toolName = hookData.tool_name || '';
  const prompt = hookData.prompt || '';
  const toolInput = hookData.tool_input || {};
  
  // For UserPromptSubmit, check the prompt content
  let textToAnalyze = '';
  
  if (hookData.prompt) {
    // UserPromptSubmit hook
    textToAnalyze = hookData.prompt;
  } else if (toolName === 'Write' && toolInput.content) {
    // PreToolUse Write operation - check content being written
    textToAnalyze = toolInput.content;
  } else if (toolName === 'MultiEdit' && toolInput.edits) {
    // PreToolUse MultiEdit operation - check edit content
    textToAnalyze = toolInput.edits.map(edit => edit.new_string || '').join('\n');
  }
  
  // Skip very short text or empty content
  if (textToAnalyze.length < 20) {
    process.exit(0);
  }
  
  const assumptions = detectAssumptions(textToAnalyze);
  
  if (assumptions.length > 0) {
    const verificationType = getVerificationType(textToAnalyze);
    const suggestions = generateVerificationSuggestions(assumptions);
    const explanations = generateAssumptionExplanation(assumptions);
    
    // For UserPromptSubmit hook, add context about the assumptions detected
    const contextMessage = [
      `⚠️ ASSUMPTION DETECTED: Found ${assumptions.length} assumption pattern(s)`,
      '',
      ...explanations,
      '',
      '🔍 Verification suggestions:',
      ...suggestions.map(s => `• ${s}`),
      '',
      '⚠️ Making assumptions led to the driver API endpoint issues. Should I verify facts first?'
    ].join('\n');
    
    const decision = {
      hookEventName: "UserPromptSubmit",
      additionalContext: contextMessage
    };
    
    // Output JSON decision for Claude Code to process
    console.log(JSON.stringify(decision, null, 2));
    
    process.exit(0); // Let Claude Code handle the permission decision
  }
  
  process.exit(0); // No assumptions detected, allow operation
}

// Run the hook
main().catch(error => {
  console.error('Assumption detector error:', error);
  process.exit(1);
});