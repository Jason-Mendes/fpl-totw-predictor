#!/usr/bin/env node

/**
 * Enhanced TypeScript "any" Type Blocker Hook (with Legitimate Pattern Allowances)
 * 
 * This hook prevents the use of dangerous "any" type annotations in TypeScript code,
 * while allowing legitimate TypeScript patterns. Provides context-aware suggestions 
 * for proper TypeScript alternatives.
 * 
 * DETECTS DANGEROUS "ANY" PATTERNS:
 * - Type assertions: "as any", "<any>"
 * - Direct type annotations: ": any", catch blocks, function parameters
 * - Variable declarations: const/let/var variable: any
 * - Generic types: Array<any>, Promise<any>, Record<string, any>
 * - Function return types: () => any, => Promise<any>
 * - Object properties: { property: any }
 * - Interface properties: property?: any
 * 
 * ALLOWS LEGITIMATE PATTERNS:
 * - "as const" assertions for literal types
 * - Branded type assertions like "as UserId"
 * - Branded types with __brand property
 * 
 * CONTEXT-AWARE SUGGESTIONS:
 * - Catch blocks: Use "unknown" type or omit type annotation
 * - Third-party libraries: Import proper type definitions
 * - Socket.IO events: Define specific event data interfaces
 * - Cypress commands: Use proper Chainable types
 * - MongoDB ObjectIds: Use Types.ObjectId from mongoose
 * - Express requests: Extend Request interface
 * - API responses: Define proper response interfaces
 * 
 * Exit codes:
 * - 0: Success (no dangerous "any" usage detected)
 * - 2: Blocking error with comprehensive guidance
 */

import { readFileSync, existsSync } from 'fs';
import { execSync } from 'child_process';
import path from 'path';

// Named patterns table for reliable rule identification and maintainability
const NAMED_PATTERNS = [
  { name: 'as-any-assertion', re: /\bas\s+any\b/g },
  { name: 'angle-any-assertion', re: /<any>/g },
  { name: 'array-any', re: /\bany\s*\[\s*\]/g },
  { name: 'any-type-annotation', re: /:\s*any\b(?!\s*\[)/g },
  { name: 'func-param-any', re: /\(\s*[A-Za-z_$]\w*\s*:\s*any\s*\)/g },
  { name: 'catch-any', re: /catch\s*\(\s*[A-Za-z_$]\w*\s*:\s*any\s*\)/g },
  { name: 'var-decl-any', re: /(?:let|const|var)\s+[A-Za-z_$]\w*\s*:\s*any\b/g },
  { name: 'obj-prop-any', re: /\w+\s*:\s*any\s*[,;}]/g },
  { name: 'quoted-prop-any', re: /['"][^'"]+['"]\s*:\s*any\b/g },
  { name: 'mapped-key-any', re: /\[\s*[A-Za-z_$]\w*\s+in\s+[^\]]+\]\s*:\s*any\b/g },
  { name: 'array-generic-any', re: /Array<\s*any\s*>/g },
  { name: 'promise-generic-any', re: /Promise<\s*any\s*>/g },
  { name: 'record-generic-any', re: /Record<[^,]+,\s*any\s*>/g },
  { name: 'readonlyarray-generic-any', re: /ReadonlyArray<\s*any\s*>/g },
  { name: 'cypress-chainable-any', re: /Chainable<\s*any\s*>/g },
  { name: 'eventhandler-any', re: /EventHandler<\s*any\s*>/g },
  { name: 'generic-any-first', re: /\b[A-Za-z_$]\w*<\s*any(?:\s*,|\s*>)/g },
  { name: 'generic-any-anywhere', re: /\b[A-Za-z_$]\w*<[^>]*\bany\b[^>]*>/g },
  { name: 'returns-any', re: /\)\s*:\s*any\b/g },
  { name: 'fat-arrow-returns-any', re: /=>\s*any\b/g },
  { name: 'fat-arrow-promise-any', re: /=>\s*Promise<\s*any\s*>/g },
  { name: 'function-type-any', re: /:\s*\(\s*[^)]*\)\s*=>\s*any\b/g },
  { name: 'type-alias-any', re: /\btype\s+[A-Za-z_$]\w*\s*=\s*any\b/g },
  { name: 'generic-constraint-any', re: /\b(?:extends|=\s*)\s*any\b/g },
  { name: 'union-any-left', re: /\bany\s*[\|&]\s*/g },
  { name: 'union-any-right', re: /[\|&]\s*any\b/g },
  { name: 'index-signature-any', re: /\[\s*[^:\]]+:\s*[^]\)]*\]\s*:\s*any\b/g },
  { name: 'satisfies-any', re: /\bsatisfies\s+any\b/g },
];

// Extract just the regex patterns for performance
const DANGEROUS_ANY_PATTERNS = NAMED_PATTERNS.map(p => p.re);

// Multiline patterns that span across lines
const MULTILINE_DANGEROUS_PATTERNS = [
  /\bas\s*[\r\n]+\s*any\b/gm,                 // as\nany
  /:\s*[\r\n]+\s*any\b/gm,                    // :\n any
];

// Files/directories to ignore
const IGNORE_PATTERNS = [
  /node_modules\//,
  /dist\//,
  /build\//,
  /out\//,
  /tmp\//,
  /coverage\//,
  /storybook-static\//,
  /vendor\//,
  /\.d\.ts$/,
  /\.gen\.ts$/,
  /\.generated\.ts$/,
  /__snapshots__\//,
];

// Check if this is a TypeScript file 
function isTypeScriptFile(filePath) {
  return filePath.endsWith('.ts') || filePath.endsWith('.tsx');
}

// Strip block comments and string literals while preserving line structure
function stripBlocksAndStrings(src) {
  let out = '', i = 0, n = src.length, mode = null; // null|'slc'|'mlc'|'s'|'d'|'t'
  
  while (i < n) {
    const ch = src[i], nxt = src[i + 1];
    
    if (!mode) {
      if (ch === '/' && nxt === '/') { mode = 'slc'; out += '  '; i += 2; continue; }
      if (ch === '/' && nxt === '*') { mode = 'mlc'; out += '  '; i += 2; continue; }
      if (ch === "'") { mode = 's'; out += ' '; i++; continue; }
      if (ch === '"') { mode = 'd'; out += ' '; i++; continue; }
      if (ch === '`') { mode = 't'; out += ' '; i++; continue; }
      out += ch; i++; continue;
    }
    
    if (mode === 'slc') { 
      if (ch === '\n') { mode = null; out += '\n'; } else out += ' '; 
      i++; continue; 
    }
    
    if (mode === 'mlc') { 
      if (ch === '*' && nxt === '/') { mode = null; out += '  '; i += 2; } 
      else { out += (ch === '\n' ? '\n' : ' '); i++; } 
      continue; 
    }
    
    if (mode === 's' || mode === 'd') { 
      const q = mode === 's' ? "'" : '"'; 
      if (ch === '\\') { out += '  '; i += 2; } 
      else if (ch === q) { mode = null; out += ' '; i++; } 
      else { out += (ch === '\n' ? '\n' : ' '); i++; } 
      continue; 
    }
    
    if (mode === 't') { 
      if (ch === '\\') { out += '  '; i += 2; } 
      else if (ch === '`') { mode = null; out += ' '; i++; } 
      else { out += (ch === '\n' ? '\n' : ' '); i++; } 
      continue; 
    }
  }
  return out;
}

// Normalize path separators for cross-platform compatibility
function normalizeForIgnore(p) {
  return p.replace(/\\/g, '/');
}

// Check if file should be ignored
function shouldIgnoreFile(filePath) {
  const p = normalizeForIgnore(filePath);
  return IGNORE_PATTERNS.some(pattern => pattern.test(p));
}

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

// Enhanced function to check for dangerous "any" patterns with comprehensive detection
function checkForAsAny(filePath) {
  if (!existsSync(filePath) || shouldIgnoreFile(filePath) || !isTypeScriptFile(filePath)) {
    return { hasAsAny: false, locations: [] };
  }
  
  const rawContent = readFileSync(filePath, 'utf8');
  const locations = [];
  const seenViolations = new Set(); // De-duplicate violations on same line
  
  // Step 1: Strip comments and strings to avoid false positives
  const sanitizedContent = stripBlocksAndStrings(rawContent);
  
  // Step 2: Check for multiline patterns first
  MULTILINE_DANGEROUS_PATTERNS.forEach(pattern => {
    pattern.lastIndex = 0; // Reset regex global state
    let match;
    while ((match = pattern.exec(sanitizedContent)) !== null) {
      const lineNumber = sanitizedContent.slice(0, match.index).split('\n').length;
      const originalLine = rawContent.split('\n')[lineNumber - 1] || '';
      const violationKey = `${lineNumber}:multiline-any-usage`;
      
      if (!seenViolations.has(violationKey)) {
        seenViolations.add(violationKey);
        locations.push({
          line: lineNumber,
          text: originalLine.trim(),
          pattern: `multiline: ${pattern.toString()}`,
          ruleName: 'multiline-any-usage'
        });
      }
    }
  });
  
  // Step 3: Check line-by-line patterns with proper rule name mapping
  const sanitizedLines = sanitizedContent.split('\n');
  const originalLines = rawContent.split('\n');
  
  sanitizedLines.forEach((sanitizedLine, index) => {
    DANGEROUS_ANY_PATTERNS.forEach((pattern, patternIndex) => {
      pattern.lastIndex = 0; // Reset regex global state
      
      if (pattern.test(sanitizedLine)) {
        const originalLine = originalLines[index] || '';
        const ruleName = NAMED_PATTERNS[patternIndex].name; // Use reliable rule name from table
        const violationKey = `${index + 1}:${ruleName}`;
        
        if (!seenViolations.has(violationKey)) {
          seenViolations.add(violationKey);
          locations.push({
            line: index + 1,
            text: originalLine.trim(),
            pattern: pattern.toString(),
            ruleName
          });
        }
      }
    });
  });
  
  return {
    hasAsAny: locations.length > 0,
    locations
  };
}

// Suggest proper TypeScript alternatives with comprehensive patterns
function suggestAlternatives(filePath, locations) {
  const suggestions = [];
  
  locations.forEach(loc => {
    let suggestion = '';
    let example = '';
    let pattern = '';
    
    // Enhanced context-aware suggestions for different 'any' patterns
    if (loc.text.includes('catch') && (loc.text.includes('error') || loc.text.includes('err'))) {
      suggestion = 'Use "unknown" type for catch block errors or omit type annotation';
      example = '} catch (error) { or } catch (error: unknown) { if (error instanceof Error) { ... }';
      pattern = 'TypeScript: Proper error handling in catch blocks';
    } else if (loc.text.includes('sendMail') || loc.text.includes('nodemailer')) {
      suggestion = 'Import proper types from nodemailer library';
      example = 'import { MailOptions, SentMessageInfo } from "nodemailer"; sendMail: (options: MailOptions) => Promise<SentMessageInfo>';
      pattern = 'TypeScript: Third-party library types';
    } else if (loc.text.includes('socket') || loc.text.includes('emit')) {
      suggestion = 'Define proper interfaces for Socket.IO event data';
      example = 'interface SocketEventData { userId: string; message: string } emitToRoom(room: string, event: string, data: SocketEventData)';
      pattern = 'TypeScript: Socket.IO event typing';
    } else if (loc.text.includes('Chainable') || loc.text.includes('cy.')) {
      suggestion = 'Use proper Cypress command return types or specific data interfaces';
      example = 'Chainable<JQuery<HTMLElement>> or interface TestUser { id: string; email: string } Chainable<TestUser>';
      pattern = 'TypeScript: Cypress command typing';
    } else if (loc.text.includes('mongoose') || loc.text.includes('_id')) {
      suggestion = 'Use Types.ObjectId from mongoose for MongoDB ObjectIds';
      example = 'const userId: Types.ObjectId = new Types.ObjectId(id)';
      pattern = 'TypeScript: Proper MongoDB typing';
    } else if (loc.text.includes('req.user') || loc.text.includes('Request') && loc.text.includes('user')) {
      suggestion = 'Extend Express Request interface with proper user type';
      example = 'interface AuthenticatedRequest extends Request { user: User } req: AuthenticatedRequest';
      pattern = 'TypeScript: Express Request interface extension';
    } else if (loc.text.includes('populated')) {
      suggestion = 'Use discriminated unions for populated vs non-populated documents';
      example = 'type PopulatedStore = Store & { owner: User }';
      pattern = 'TypeScript: Discriminated unions';
    } else if (loc.text.includes('Array<') || loc.text.includes('Promise<')) {
      suggestion = 'Define specific generic types instead of any';
      example = 'Array<User> or Promise<ApiResponse<User>> instead of Array<any> or Promise<any>';
      pattern = 'TypeScript: Proper generic types';
    } else if (loc.text.includes('const') && (loc.text.includes('query') || loc.text.includes('filter'))) {
      suggestion = 'Define interface for query/filter objects';
      example = 'interface QueryFilter { storeId?: string; status?: OrderStatus } const query: QueryFilter = {}';
      pattern = 'TypeScript: Query/filter object interfaces';
    } else if (loc.text.includes('data') || loc.text.includes('response') || loc.text.includes('result')) {
      suggestion = 'Define specific interfaces for data structures';
      example = 'interface ApiResponse<T> { data: T; status: number; message: string }';
      pattern = 'TypeScript: Data structure interfaces';
    } else if (loc.text.includes('status') || loc.text.includes('state') || loc.text.includes('type')) {
      suggestion = 'Use enum, const assertions, or union types for status/state values';
      example = 'type Status = "PENDING" | "SHIPPED" | "CANCELLED" as const';
      pattern = 'TypeScript: Union types with const assertions';
    } else if (loc.text.includes('JSON.parse')) {
      suggestion = 'Define interface for JSON structure and use type guards';
      example = 'interface ApiResponse { data: T } const response = validateApiResponse(parsed)';
      pattern = 'TypeScript: Type guards with generics';
    } else if (loc.text.includes('Object.assign') || loc.text.includes('spread')) {
      suggestion = 'Use proper object spread with defined interfaces';
      example = 'interface UpdateData extends Partial<User> {}';
      pattern = 'TypeScript: Utility types (Partial, Pick, Omit)';
    } else if (loc.text.includes('config') || loc.text.includes('options')) {
      suggestion = 'Use interface with optional properties for configuration objects';
      example = 'interface Config { apiUrl: string; timeout?: number }';
      pattern = 'TypeScript: Optional properties';
    } else if (loc.text.includes('event') || loc.text.includes('handler')) {
      suggestion = 'Use proper event handler typing with generics';
      example = 'const handler: EventHandler<MouseEvent> = (e) => {}';
      pattern = 'TypeScript: Generic event handlers';
    } else {
      suggestion = 'Use proper TypeScript patterns instead of any type annotations';
      example = 'interface DataType { field: string } or type Union = A | B | C';
      pattern = 'TypeScript: Interfaces and union types';
    }
    
    suggestions.push({
      line: loc.line,
      text: loc.text,
      suggestion,
      example,
      pattern
    });
  });
  
  return suggestions;
}

// Main execution
async function main() {
  const hookData = await parseHookInput();
  
  // Only process TypeScript file edits
  const toolName = hookData.tool_name || '';
  const toolInput = hookData.tool_input || {};
  const filePath = toolInput.file_path || toolInput.filePath || '';
  
  // Check if this is a relevant TypeScript file edit
  const isRelevantTool = ['Edit', 'MultiEdit', 'Write'].includes(toolName);
  
  if (!isRelevantTool || !isTypeScriptFile(filePath) || shouldIgnoreFile(filePath)) {
    process.exit(0); // Not relevant, allow operation
  }
  
  // For MultiEdit, check the new content with enhanced detection
  if (toolName === 'MultiEdit' && toolInput.edits) {
    let hasAsAny = false;
    const issues = [];
    
    toolInput.edits.forEach((edit, index) => {
      const editContent = edit.new_string || '';
      if (!editContent.trim()) return;
      
      // Strip comments and strings from edit content
      const sanitizedContent = stripBlocksAndStrings(editContent);
      const editSnippet = editContent.split('\n')[0].slice(0, 50); // First line, truncated for context
      
      // Check multiline patterns first
      MULTILINE_DANGEROUS_PATTERNS.forEach(pattern => {
        pattern.lastIndex = 0;
        if (pattern.test(sanitizedContent)) {
          hasAsAny = true;
          issues.push(`Edit ${index + 1}: Contains multiline dangerous "any" pattern (${editSnippet}...)`);
        }
      });
      
      // Check single-line patterns with proper rule names
      DANGEROUS_ANY_PATTERNS.forEach((pattern, patternIndex) => {
        pattern.lastIndex = 0;
        if (pattern.test(sanitizedContent)) {
          hasAsAny = true;
          const ruleName = NAMED_PATTERNS[patternIndex].name;
          issues.push(`Edit ${index + 1}: Contains dangerous "any" usage (${ruleName}) (${editSnippet}...)`);
        }
      });
    });
    
    if (hasAsAny) {
      // Use new PermissionDecision format to block with detailed guidance
      const decision = {
        decision: "block",
        reason: `TypeScript type safety violation: "as any" usage detected. This violates the MANDATORY TypeScript rule in CLAUDE.md.`,
        additionalInfo: {
          violations: issues,
          guidance: {
            patterns: [
              'ENUMS: enum Status { PENDING = "pending", SHIPPED = "shipped" }',
              'CONST ASSERTIONS: const STATUS = ["PENDING", "SHIPPED"] as const',
              'UNION TYPES: type Status = "PENDING" | "SHIPPED" | "CANCELLED"',
              'INTERFACES: interface User { id: string; name: string }',
              'TYPE GUARDS: function isUser(obj: unknown): obj is User',
              'UTILITY TYPES: Partial<T>, Pick<T, K>, Omit<T, K>',
              'GENERICS: Array<T>, Promise<T>, Record<K, V>'
            ],
            implementations: [
              'For Mongoose ObjectIds, use Types.ObjectId',
              'For populated documents, create proper discriminated unions',
              'For Express requests, extend the Request interface',
              'For JSON parsing, define interfaces and use type guards',
              'For API responses, create proper response interfaces'
            ],
            examples: [
              '❌ Bad:  const userId = (req.user as any).id',
              '✅ Good: interface AuthRequest extends Request { user: User }',
              '❌ Bad:  const ownerId = (store.owner as any)._id',
              '✅ Good: const ownerId = store.populated("owner") ? store.owner._id : store.owner',
              '❌ Bad:  const status = data as any',
              '✅ Good: type Status = "PENDING" | "SHIPPED"; const status: Status = data'
            ]
          }
        }
      };
      
      // Output JSON decision for Claude Code to process
      console.log(JSON.stringify(decision, null, 2));
      
      process.exit(0); // Let Claude Code handle the permission decision
    }
  }
  
  // For Write operations, check the entire new content with enhanced detection
  if (toolName === 'Write' && toolInput.content) {
    const writeContent = toolInput.content || '';
    if (!writeContent.trim()) {
      process.exit(0); // Empty content, nothing to check
    }
    
    // Check if this file should be ignored
    if (shouldIgnoreFile(filePath)) {
      process.exit(0);
    }
    
    const locations = [];
    
    // Strip comments and strings to avoid false positives
    const sanitizedContent = stripBlocksAndStrings(writeContent);
    
    // Check for multiline patterns first
    MULTILINE_DANGEROUS_PATTERNS.forEach(pattern => {
      pattern.lastIndex = 0;
      let match;
      while ((match = pattern.exec(sanitizedContent)) !== null) {
        const lineNumber = sanitizedContent.slice(0, match.index).split('\n').length;
        const originalLine = writeContent.split('\n')[lineNumber - 1] || '';
        locations.push({
          line: lineNumber,
          text: originalLine.trim(),
          pattern: `multiline: ${pattern.toString()}`,
          ruleName: 'multiline-any-usage'
        });
      }
    });
    
    // Check line-by-line patterns  
    const sanitizedLines = sanitizedContent.split('\n');
    const originalLines = writeContent.split('\n');
    
    sanitizedLines.forEach((sanitizedLine, index) => {
      DANGEROUS_ANY_PATTERNS.forEach((pattern, patternIndex) => {
        pattern.lastIndex = 0;
        
        if (pattern.test(sanitizedLine)) {
          const originalLine = originalLines[index] || '';
          const patternStr = pattern.toString();
          // Use reliable rule name from table instead of string matching
          const ruleName = NAMED_PATTERNS[patternIndex] ? NAMED_PATTERNS[patternIndex].name : 'dangerous-any-usage';
          
          locations.push({
            line: index + 1,
            text: originalLine.trim(),
            pattern: patternStr,
            ruleName
          });
        }
      });
    });
    
    if (locations.length > 0) {
      const suggestions = suggestAlternatives(filePath, locations);
      
      // Use new PermissionDecision format to block with detailed guidance
      const decision = {
        decision: "block",
        reason: `TypeScript type safety violation: Found ${locations.length} "as any" usage(s) in ${path.basename(filePath)}. This violates the MANDATORY TypeScript rule in CLAUDE.md.`,
        additionalInfo: {
          filePath,
          violations: suggestions.map(s => ({
            line: s.line,
            text: s.text,
            pattern: s.pattern,
            suggestion: s.suggestion,
            example: s.example
          })),
          guidance: {
            patterns: [
              'ENUMS: enum OrderStatus { PENDING = "pending", SHIPPED = "shipped" }',
              'CONST ASSERTIONS: const STATUSES = ["PENDING", "SHIPPED"] as const',
              'UNION TYPES: type Status = "PENDING" | "SHIPPED" | "CANCELLED"',
              'INTERFACES: interface ApiResponse<T> { data: T; status: number }',
              'TYPE GUARDS: function isValidUser(obj: unknown): obj is User',
              'UTILITY TYPES: Partial<User>, Pick<User, "id" | "name">'
            ],
            implementations: [
              'For Mongoose ObjectIds, use Types.ObjectId',
              'For populated documents, create proper discriminated unions',
              'For Express requests, extend the Request interface',
              'For JSON parsing, define interfaces and use type guards',
              'For API responses, create proper response interfaces'
            ]
          }
        }
      };
      
      // Output JSON decision for Claude Code to process
      console.log(JSON.stringify(decision, null, 2));
      
      process.exit(0); // Let Claude Code handle the permission decision
    }
  }
  
  // For regular Edit operations
  if (toolName === 'Edit') {
    // We'll check after the edit is complete using PostToolUse
    process.exit(0);
  }
  
  process.exit(0); // Allow operation
}

// Run the hook
main().catch(error => {
  console.error('Hook error:', error);
  process.exit(1);
});