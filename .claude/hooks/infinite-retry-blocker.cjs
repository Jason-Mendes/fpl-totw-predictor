#!/usr/bin/env node

/**
 * Infinite Retry Blocker Hook
 * 
 * Prevents all types of infinite retry loops that can cause rate limiting,
 * performance issues, memory leaks, and authentication failures.
 * 
 * ORIGIN: Created after August 24, 2025 image infinite retry crisis that
 * caused store dashboard authentication failures and rate limit exhaustion.
 * 
 * This comprehensive hook detects:
 * - Image error handling infinite loops
 * - API retry loops without exponential backoff
 * - Event handler infinite recursion
 * - State update loops in React
 * - WebSocket reconnection storms
 * - Polling without proper intervals
 */

const fs = require('fs');
const path = require('path');

// Patterns that can cause infinite retry loops
const infiniteRetryPatterns = [
  // IMAGE ERROR HANDLERS - Critical Priority
  {
    pattern: /onError.*target\.src\s*=\s*["']https?:\/\//gi,
    severity: 'CRITICAL',
    message: '🚨 CRITICAL: External URL in image onError handler causes infinite retry loops!'
  },
  {
    pattern: /onError.*target\.src\s*=\s*["'][^"']*\/api\/[^"']*/gi,
    severity: 'CRITICAL', 
    message: '🚨 CRITICAL: API endpoint in image onError handler causes infinite retry loops!'
  },
  {
    pattern: /onError.*target\.src\s*=.*(?!useState|state|Error)/gi,
    severity: 'HIGH',
    message: '🔴 HIGH: Setting target.src in onError without state management can cause infinite loops!'
  },

  // API RETRY LOOPS - High Priority  
  {
    pattern: /catch.*\{\s*[\w\s]*(?:api\.|fetch\(|axios\.|request\().*\}/gi,
    severity: 'HIGH',
    message: '🔴 HIGH: API retry in catch block without backoff/limit can cause infinite loops!'
  },
  {
    pattern: /\.catch\(\(\)\s*=>\s*[\w\s]*(?:api\.|fetch\(|axios\.|request\()/gi,
    severity: 'HIGH', 
    message: '🔴 HIGH: Direct API retry in catch without backoff/limit can cause infinite loops!'
  },
  {
    pattern: /while\s*\([^)]*\)\s*\{[^}]*(?:api\.|fetch\(|axios\.|request\()/gi,
    severity: 'CRITICAL',
    message: '🚨 CRITICAL: While loop with API calls can cause infinite request storms!'
  },

  // REACT STATE LOOPS - High Priority
  {
    pattern: /useEffect\([^,]*,\s*\[[^\]]*(?:count|data|items|list|state)[^\]]*\]\)[\s\S]*?set(?:Count|Data|Items|List|State)/gi,
    severity: 'HIGH',
    message: '🔴 HIGH: useEffect depends on state it modifies - can cause infinite re-renders!'
  },
  {
    pattern: /setState[^;]*setState/gi,
    severity: 'MEDIUM',
    message: '🟡 MEDIUM: Multiple setState calls can cause render loops - consider batching!'
  },

  // EVENT HANDLER RECURSION - Medium Priority
  {
    pattern: /on\w+\s*=\s*\{[^}]*on\w+[^}]*\}/gi,
    severity: 'MEDIUM',
    message: '🟡 MEDIUM: Event handler calling other event handlers can cause recursion!'
  },

  // WEBSOCKET RECONNECTION STORMS - High Priority
  {
    pattern: /\.onerror\s*=.*new\s+WebSocket/gi,
    severity: 'HIGH',
    message: '🔴 HIGH: Immediate WebSocket reconnection in onerror can cause connection storms!'
  },
  {
    pattern: /\.onclose\s*=.*connect|\.onclose\s*=.*WebSocket/gi,
    severity: 'HIGH',
    message: '🔴 HIGH: Immediate reconnection in onclose without backoff can cause storms!'
  },

  // POLLING LOOPS - Medium Priority
  {
    pattern: /setInterval\([^,]*,\s*[0-9]{1,3}\)/gi,
    severity: 'HIGH',
    message: '🔴 HIGH: Very fast polling interval (<1000ms) can cause performance issues!'
  },
  {
    pattern: /setTimeout\([^,]*,\s*0\)/gi,
    severity: 'MEDIUM',
    message: '🟡 MEDIUM: setTimeout with 0 delay can cause tight loops!'
  },

  // RECURSIVE FUNCTION CALLS - High Priority
  {
    pattern: /function\s+(\w+)[^{]*\{[^}]*\1\s*\(/gi,
    severity: 'HIGH',
    message: '🔴 HIGH: Function calls itself - ensure proper base case to prevent stack overflow!'
  },
  {
    pattern: /const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*\1\s*\(/gi,
    severity: 'HIGH', 
    message: '🔴 HIGH: Arrow function calls itself - ensure proper base case to prevent stack overflow!'
  },

  // PROMISE CHAINS - Medium Priority
  {
    pattern: /\.catch\([^)]*\)\s*\.then\([^)]*\.catch/gi,
    severity: 'MEDIUM',
    message: '🟡 MEDIUM: Nested promise catch/then chains can cause retry loops!'
  }
];

// Safe patterns that indicate proper retry handling
const safePatterns = [
  /exponential.*backoff/gi,
  /retry.*count/gi,
  /max.*retries/gi,
  /backoff.*delay/gi,
  /useState.*error/gi,
  /\[imageError|imageLoading|hasError\]/gi,
  /setTimeout.*\*\s*2/gi, // Exponential backoff multiplier
];

function hasSafePattern(line) {
  return safePatterns.some(pattern => pattern.test(line));
}

function scanFileContent(filePath, content) {
  const violations = [];
  
  // Skip non-relevant files
  if (!filePath.endsWith('.tsx') && 
      !filePath.endsWith('.jsx') && 
      !filePath.endsWith('.ts') && 
      !filePath.endsWith('.js')) {
    return violations;
  }

  const lines = content.split('\n');
  
  infiniteRetryPatterns.forEach(({ pattern, severity, message }) => {
    lines.forEach((line, index) => {
      if (pattern.test(line) && !hasSafePattern(line)) {
        violations.push({
          file: filePath,
          line: index + 1,
          content: line.trim(),
          severity: severity,
          message: message
        });
      }
    });
  });

  return violations;
}

function scanDirectory(dirPath, violations = []) {
  if (!fs.existsSync(dirPath)) {
    return violations;
  }

  const entries = fs.readdirSync(dirPath);
  
  entries.forEach(entry => {
    const fullPath = path.join(dirPath, entry);
    
    // Skip hidden directories, node_modules, and build outputs
    if (entry.startsWith('.') || 
        entry === 'node_modules' || 
        entry === 'build' || 
        entry === 'dist' ||
        entry === 'coverage') {
      return;
    }
    
    try {
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        scanDirectory(fullPath, violations);
      } else if (stat.isFile()) {
        const content = fs.readFileSync(fullPath, 'utf8');
        const fileViolations = scanFileContent(fullPath, content);
        violations.push(...fileViolations);
      }
    } catch (error) {
      // Skip files that can't be read
    }
  });

  return violations;
}

function groupViolationsBySeverity(violations) {
  const groups = {
    CRITICAL: [],
    HIGH: [],
    MEDIUM: [],
    LOW: []
  };
  
  violations.forEach(violation => {
    groups[violation.severity].push(violation);
  });
  
  return groups;
}

function main() {
  console.log('🔍 Scanning for infinite retry loop patterns...');
  
  // Scan both frontend and backend
  const scanPaths = [
    path.join(process.cwd(), 'frontend', 'src'),
    path.join(process.cwd(), 'backend', 'src'),
    path.join(process.cwd(), 'backend', 'controllers'),
    path.join(process.cwd(), 'backend', 'services'),
    path.join(process.cwd(), 'backend', 'middleware'),
  ];
  
  let allViolations = [];
  
  scanPaths.forEach(scanPath => {
    if (fs.existsSync(scanPath)) {
      const violations = scanDirectory(scanPath);
      allViolations.push(...violations);
    }
  });
  
  if (allViolations.length === 0) {
    console.log('✅ No infinite retry loop patterns found!');
    return;
  }

  const groupedViolations = groupViolationsBySeverity(allViolations);
  
  console.log(`\n🚨 Found ${allViolations.length} potential infinite retry pattern(s):\n`);
  
  // Show violations by severity
  ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].forEach(severity => {
    const violations = groupedViolations[severity];
    if (violations.length === 0) return;
    
    console.log(`\n=== ${severity} ISSUES (${violations.length}) ===`);
    
    violations.forEach(({ file, line, content, message }, index) => {
      console.log(`\n${index + 1}. ${message}`);
      console.log(`   File: ${path.relative(process.cwd(), file)}:${line}`);
      console.log(`   Code: ${content}`);
    });
  });

  console.log(`\n📋 GENERAL PREVENTION PATTERNS:`);
  console.log(`
✅ SAFE API Retry Pattern:
const MAX_RETRIES = 3;
const INITIAL_DELAY = 1000;

const apiWithRetry = async (url, retryCount = 0) => {
  try {
    return await api.get(url);
  } catch (error) {
    if (retryCount < MAX_RETRIES) {
      const delay = INITIAL_DELAY * Math.pow(2, retryCount); // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, delay));
      return apiWithRetry(url, retryCount + 1);
    }
    throw error;
  }
};

✅ SAFE Image Error Pattern:
const [imageError, setImageError] = useState(false);
// Use state-based fallback, never set target.src in onError

✅ SAFE WebSocket Reconnection:
let reconnectAttempts = 0;
const MAX_RECONNECTS = 5;
const reconnectWithBackoff = () => {
  if (reconnectAttempts < MAX_RECONNECTS) {
    const delay = 1000 * Math.pow(2, reconnectAttempts);
    setTimeout(connect, delay);
    reconnectAttempts++;
  }
};

✅ SAFE useEffect Dependencies:
useEffect(() => {
  // Use functional update to avoid dependency loop
  setCount(prevCount => prevCount + 1);
}, []); // Empty dependency array

✅ SAFE Polling Pattern:
const POLLING_INTERVAL = 5000; // Minimum 5 seconds
setInterval(fetchData, POLLING_INTERVAL);
`);
  
  const criticalCount = groupedViolations.CRITICAL.length;
  const highCount = groupedViolations.HIGH.length;
  
  if (criticalCount > 0) {
    console.log(`\n🚨 ${criticalCount} CRITICAL issues must be fixed immediately!`);
    console.log('🔗 See CLAUDE.md Section 4 for image error handling requirements.');
    process.exit(1);
  } else if (highCount > 0) {
    console.log(`\n🔴 ${highCount} HIGH priority issues should be addressed.`);
    console.log('⚠️  These patterns can cause performance issues and rate limiting.');
    // Don't exit for HIGH priority - allow commit but warn
  } else {
    console.log(`\n🟡 Found ${allViolations.length} potential issues - please review patterns.`);
  }
}

if (require.main === module) {
  main();
}

module.exports = { scanFileContent, scanDirectory, groupViolationsBySeverity };