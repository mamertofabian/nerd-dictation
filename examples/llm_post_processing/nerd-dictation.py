# User configuration file with LLM post-processing
# Located at ~/.config/nerd-dictation/nerd-dictation.py

import re
import requests
import json
import sys
import time

# -----------------------------------------------------------------------------
# LLM Post-Processing Configuration

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral:7b-instruct"
OLLAMA_TIMEOUT = 10  # seconds

# LLM post-processing settings
LLM_ENABLED = True
LLM_MIN_WORDS = 3  # Only process with LLM if text has at least this many words

# Cache to prevent multiple LLM processing of the same text
_llm_cache = {}  # Cleared cache for conservative prompt
_last_processed_text = ""
LLM_CACHE_MAX_SIZE = 100  # Limit cache size to prevent memory issues

# Debouncing to prevent rapid LLM calls
_last_llm_call_time = 0
LLM_DEBOUNCE_DELAY = 0.3  # 300ms minimum between LLM calls

# Progressive text detection
_last_llm_processed_text = ""
MIN_TEXT_LENGTH_FOR_LLM = 15  # Minimum characters before considering LLM processing

def should_process_with_llm(text: str) -> bool:
    """Determine if text should be processed with LLM"""
    global _last_llm_processed_text
    
    # Skip very short text
    if len(text.split()) < LLM_MIN_WORDS or len(text) < MIN_TEXT_LENGTH_FOR_LLM:
        return False
    
    # Skip if this looks like progressive typing of previously processed text
    if _last_llm_processed_text and text.startswith(_last_llm_processed_text.rstrip('.,!?')):
        # This appears to be an extension of previously processed text
        return False
    
    # Skip if this looks like a substring of what we just processed
    if _last_llm_processed_text and _last_llm_processed_text.startswith(text.rstrip('.,!?')):
        return False
        
    return True

def improve_text_with_llm(text: str) -> str:
    """Send text to local Ollama for grammar correction and improvement"""
    global _last_llm_call_time, _last_llm_processed_text
    
    if not LLM_ENABLED:
        return text
        
    # Check if we should process this text
    if not should_process_with_llm(text):
        return text
    
    # Debouncing: prevent rapid successive LLM calls
    current_time = time.time()
    if current_time - _last_llm_call_time < LLM_DEBOUNCE_DELAY:
        return text
    _last_llm_call_time = current_time
    
    # Check cache to avoid reprocessing the same text
    if text in _llm_cache:
        return _llm_cache[text]
    
    prompt = f"""Fix only obvious speech recognition and grammar errors. DO NOT change technical terms, proper nouns, or already correct formatting.

FIX ONLY:
- Subject-verb disagreement: "this are" -> "this is", "we was" -> "we were"
- Missing articles: "need file" -> "need a file"
- Basic homophones from speech: "there going" -> "they're going", "by groceries" -> "buy groceries"
- Missing capitalization at sentence start
- Obvious speech recognition errors: "no" -> "know" when context is clear

PRESERVE COMPLETELY:
- Technical terms: API, JSON, MySQL, backend, frontend, login, etc.
- Programming concepts: async, await, function, class, etc.
- Proper nouns and brand names
- Already hyphenated terms: real-time, full-stack, etc.
- Any word that could be technically correct

Return the same text with only minimal grammar fixes.

Text: {text}
Fixed:"""
    
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.01,  # Extremely low temperature for conservative corrections
            "top_p": 0.7,
            "num_predict": 128,  # Shorter responses to prevent over-elaboration
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, 
                               json=data, 
                               timeout=OLLAMA_TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            improved_text = result["response"].strip()
            
            # Basic validation and cleanup
            if improved_text and len(improved_text) > 0:
                # Remove any quotes that might have been added by the LLM
                improved_text = improved_text.strip('"\'')
                
                # Remove common unwanted commentary patterns
                import re
                # Remove text in parentheses that contains explanatory words
                improved_text = re.sub(r'\s*\([^)]*(?:changes needed|pronunciation|grammar|correct)[^)]*\)', '', improved_text, flags=re.IGNORECASE)
                # Remove sentences that start with explanatory phrases
                improved_text = re.sub(r'\s*(No changes needed|Pronunciation:|Grammar:|Note:)[^.]*\.?', '', improved_text, flags=re.IGNORECASE)
                
                # Clean up extra whitespace
                improved_text = ' '.join(improved_text.split())
                
                # Validate that the result isn't too different in length or empty
                if improved_text and 0.3 <= len(improved_text) <= len(text) * 2:
                    # Cache the result (with size limit)
                    if len(_llm_cache) >= LLM_CACHE_MAX_SIZE:
                        # Remove oldest entry (simple FIFO)
                        _llm_cache.pop(next(iter(_llm_cache)))
                    _llm_cache[text] = improved_text
                    
                    # Log the improvement to stderr for debugging (optional)
                    if improved_text != text:
                        print(f"LLM improved: '{text}' → '{improved_text}'", file=sys.stderr)
                    
                    # Update last processed text tracking
                    _last_llm_processed_text = improved_text
                    return improved_text
                else:
                    # Validation failed, fall back to original text
                    print(f"LLM output validation failed, using original: '{text}'", file=sys.stderr)
                    # Cache the fallback too (with size limit)
                    if len(_llm_cache) >= LLM_CACHE_MAX_SIZE:
                        _llm_cache.pop(next(iter(_llm_cache)))
                    _llm_cache[text] = text
                    return text
            else:
                return text
        else:
            print(f"LLM API error: {response.status_code}", file=sys.stderr)
            # Cache the fallback (with size limit)
            if len(_llm_cache) >= LLM_CACHE_MAX_SIZE:
                _llm_cache.pop(next(iter(_llm_cache)))
            _llm_cache[text] = text
            return text
    except Exception as e:
        print(f"LLM processing failed: {e}", file=sys.stderr)
        # Cache the fallback (with size limit)
        if len(_llm_cache) >= LLM_CACHE_MAX_SIZE:
            _llm_cache.pop(next(iter(_llm_cache)))
        _llm_cache[text] = text
        return text

# -----------------------------------------------------------------------------
# Traditional Text Processing (from default example)

# Replace Multiple Words - Software Development Focus
TEXT_REPLACE_REGEX = (
    # General development terms
    ("\\b" "data type" "\\b", "data-type"),
    ("\\b" "copy on write" "\\b", "copy-on-write"),
    ("\\b" "key word" "\\b", "keyword"),
    ("\\b" "back end" "\\b", "backend"),
    ("\\b" "front end" "\\b", "frontend"),
    ("\\b" "full stack" "\\b", "full-stack"),
    ("\\b" "real time" "\\b", "real-time"),
    ("\\b" "run time" "\\b", "runtime"),
    ("\\b" "compile time" "\\b", "compile-time"),
    ("\\b" "time out" "\\b", "timeout"),
    ("\\b" "log in" "\\b", "login"),
    ("\\b" "log out" "\\b", "logout"),
    ("\\b" "set up" "\\b", "setup"),
    ("\\b" "work flow" "\\b", "workflow"),
    ("\\b" "name space" "\\b", "namespace"),
    ("\\b" "data base" "\\b", "database"),
    ("\\b" "web site" "\\b", "website"),
    ("\\b" "user name" "\\b", "username"),
    ("\\b" "file name" "\\b", "filename"),
    ("\\b" "file path" "\\b", "filepath"),
    ("\\b" "code base" "\\b", "codebase"),
    ("\\b" "open source" "\\b", "open-source"),
    ("\\b" "pull request" "\\b", "pull request"),
    ("\\b" "merge request" "\\b", "merge request"),
    
    # Programming concepts
    ("\\b" "callback function" "\\b", "callback"),
    ("\\b" "async await" "\\b", "async/await"),
    ("\\b" "try catch" "\\b", "try-catch"),
    ("\\b" "if else" "\\b", "if-else"),
    ("\\b" "for loop" "\\b", "for-loop"),
    ("\\b" "while loop" "\\b", "while-loop"),
    ("\\b" "switch case" "\\b", "switch-case"),
    ("\\b" "test driven development" "\\b", "test-driven development"),
    ("\\b" "behavior driven development" "\\b", "behavior-driven development"),
    ("\\b" "continuous integration" "\\b", "continuous integration"),
    ("\\b" "continuous deployment" "\\b", "continuous deployment"),
    ("\\b" "micro service" "\\b", "microservice"),
    ("\\b" "micro services" "\\b", "microservices"),
    
    # File extensions and formats
    ("\\b" "dot js" "\\b", ".js"),
    ("\\b" "dot ts" "\\b", ".ts"),
    ("\\b" "dot py" "\\b", ".py"),
    ("\\b" "dot json" "\\b", ".json"),
    ("\\b" "dot yml" "\\b", ".yml"),
    ("\\b" "dot yaml" "\\b", ".yaml"),
    ("\\b" "dot md" "\\b", ".md"),
    ("\\b" "dot txt" "\\b", ".txt"),
    ("\\b" "dot html" "\\b", ".html"),
    ("\\b" "dot css" "\\b", ".css"),
    ("\\b" "dot sql" "\\b", ".sql"),
    ("\\b" "dot xml" "\\b", ".xml"),
    ("\\b" "dot sh" "\\b", ".sh"),
    ("\\b" "dot env" "\\b", ".env"),
    ("\\b" "dot config" "\\b", ".config"),
    
    # Version control
    ("\\b" "git commit" "\\b", "git commit"),
    ("\\b" "git push" "\\b", "git push"),
    ("\\b" "git pull" "\\b", "git pull"),
    ("\\b" "git merge" "\\b", "git merge"),
    ("\\b" "git rebase" "\\b", "git rebase"),
    ("\\b" "git checkout" "\\b", "git checkout"),
    ("\\b" "git branch" "\\b", "git branch"),
    ("\\b" "git status" "\\b", "git status"),
    ("\\b" "git diff" "\\b", "git diff"),
    ("\\b" "git log" "\\b", "git log"),
    ("\\b" "git add" "\\b", "git add"),
    ("\\b" "git clone" "\\b", "git clone"),
)
TEXT_REPLACE_REGEX = tuple(
    (re.compile(match), replacement)
    for (match, replacement) in TEXT_REPLACE_REGEX
)

# Replace Single Words - Software Development Focus
WORD_REPLACE = {
    # Grammar basics
    "i": "I",
    "um": "",
    "uh": "",
    
    # Common tech terms that need capitalization
    "api": "API",
    "rest": "REST",
    "http": "HTTP",
    "https": "HTTPS",
    "url": "URL",
    "uri": "URI",
    "sql": "SQL",
    "json": "JSON",
    "xml": "XML",
    "html": "HTML",
    "css": "CSS",
    "dom": "DOM",
    "crud": "CRUD",
    "oauth": "OAuth",
    "jwt": "JWT",
    "ssl": "SSL",
    "tls": "TLS",
    "ssh": "SSH",
    "tcp": "TCP",
    "udp": "UDP",
    "ip": "IP",
    "dns": "DNS",
    "cdn": "CDN",
    "aws": "AWS",
    "gcp": "GCP",
    "ide": "IDE",
    "cli": "CLI",
    "gui": "GUI",
    "ui": "UI",
    "ux": "UX",
    "ci": "CI",
    "cd": "CD",
    "devops": "DevOps",
    "mlops": "MLOps",
    "ai": "AI",
    "ml": "ML",
    "iot": "IoT",
    "saas": "SaaS",
    "paas": "PaaS",
    "iaas": "IaaS",
    
    # Operating Systems and Platforms
    "linux": "Linux",
    "ubuntu": "Ubuntu",
    "centos": "CentOS",
    "debian": "Debian",
    "redhat": "Red Hat",
    "macos": "macOS",
    "windows": "Windows",
    "android": "Android",
    "ios": "iOS",
    
    # Programming Languages
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "python": "Python",
    "java": "Java",
    "csharp": "C#",
    "cplusplus": "C++",
    "golang": "Go",
    "rust": "Rust",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "ruby": "Ruby",
    "php": "PHP",
    "perl": "Perl",
    "scala": "Scala",
    "haskell": "Haskell",
    "clojure": "Clojure",
    "elixir": "Elixir",
    "dart": "Dart",
    
    # Frameworks and Libraries
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "express": "Express",
    "flask": "Flask",
    "django": "Django",
    "rails": "Rails",
    "spring": "Spring",
    "laravel": "Laravel",
    "nextjs": "Next.js",
    "nuxt": "Nuxt",
    "gatsby": "Gatsby",
    "svelte": "Svelte",
    "jquery": "jQuery",
    "bootstrap": "Bootstrap",
    "tailwind": "Tailwind",
    "redux": "Redux",
    "mobx": "MobX",
    "graphql": "GraphQL",
    "apollo": "Apollo",
    "prisma": "Prisma",
    "mongoose": "Mongoose",
    "sequelize": "Sequelize",
    
    # Databases
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "cassandra": "Cassandra",
    "dynamodb": "DynamoDB",
    "firebase": "Firebase",
    "sqlite": "SQLite",
    
    # Development Tools
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "jenkins": "Jenkins",
    "ansible": "Ansible",
    "terraform": "Terraform",
    "vagrant": "Vagrant",
    "webpack": "Webpack",
    "babel": "Babel",
    "eslint": "ESLint",
    "prettier": "Prettier",
    "jest": "Jest",
    "mocha": "Mocha",
    "cypress": "Cypress",
    "selenium": "Selenium",
    "postman": "Postman",
    "insomnia": "Insomnia",
    "vscode": "VS Code",
    "vim": "Vim",
    "emacs": "Emacs",
    "intellij": "IntelliJ",
    "eclipse": "Eclipse",
    "xcode": "Xcode",
    
    # Cloud and Services
    "amazon": "Amazon",
    "microsoft": "Microsoft",
    "google": "Google",
    "azure": "Azure",
    "cloudflare": "Cloudflare",
    "heroku": "Heroku",
    "netlify": "Netlify",
    "vercel": "Vercel",
    "digitalocean": "DigitalOcean",
    "linode": "Linode",
    
    # Common misspellings or mispronunciations
    "async": "async",
    "await": "await",
    "boolean": "boolean",
    "integer": "integer",
    "string": "string",
    "object": "object",
    "array": "array",
    "function": "function",
    "method": "method",
    "class": "class",
    "interface": "interface",
    "enum": "enum",
    "struct": "struct",
    "union": "union",
    "constant": "constant",
    "variable": "variable",
    "parameter": "parameter",
    "argument": "argument",
    "return": "return",
    "import": "import",
    "export": "export",
    "module": "module",
    "package": "package",
    "library": "library",
    "framework": "framework",
    "dependency": "dependency",
    "repository": "repository",
    "branch": "branch",
    "commit": "commit",
    "merge": "merge",
    "rebase": "rebase",
    "checkout": "checkout",
    "pull": "pull",
    "push": "push",
    "clone": "clone",
    "fork": "fork",
    "issue": "issue",
    "bug": "bug",
    "feature": "feature",
    "refactor": "refactor",
    "optimize": "optimize",
    "deploy": "deploy",
    "build": "build",
    "compile": "compile",
    "debug": "debug",
    "test": "test",
    "unit": "unit",
    "integration": "integration",
    "endpoint": "endpoint",
    "middleware": "middleware",
    "authentication": "authentication",
    "authorization": "authorization",
    "encryption": "encryption",
    "hash": "hash",
    "algorithm": "algorithm",
    "data": "data",
    "schema": "schema",
    "model": "model",
    "controller": "controller",
    "service": "service",
    "component": "component",
    "template": "template",
    "configuration": "configuration",
    "environment": "environment",
    "production": "production",
    "development": "development",
    "staging": "staging",
    "localhost": "localhost",
    "server": "server",
    "client": "client",
    "browser": "browser",
    "mobile": "mobile",
    "responsive": "responsive",
    "performance": "performance",
    "scalability": "scalability",
    "security": "security",
    "vulnerability": "vulnerability",
}

# Regular expressions for partial word replacement
WORD_REPLACE_REGEX = (
    ("^i'(.*)", "I'\\1"),
)
WORD_REPLACE_REGEX = tuple(
    (re.compile(match), replacement)
    for (match, replacement) in WORD_REPLACE_REGEX
)

# Add Punctuation - Enhanced for Software Development
CLOSING_PUNCTUATION = {
    "period": ".",
    "comma": ",",
    "question mark": "?",
    "exclamation mark": "!",
    "close quote": '"',
    "close single quote": "'",
    "semicolon": ";",
    "colon": ":",
    "close paren": ")",
    "close bracket": "]",
    "close brace": "}",
    "close angle": ">",
}

OPENING_PUNCTUATION = {
    "open quote": '"',
    "open single quote": "'",
    "open paren": "(",
    "open bracket": "[",
    "open brace": "{",
    "open angle": "<",
}

# Developer-specific code patterns
CODE_PATTERNS = {
    "arrow function": "=>",
    "fat arrow": "=>",
    "equals equals": "==",
    "triple equals": "===",
    "not equals": "!=",
    "not triple equals": "!==",
    "greater than or equal": ">=",
    "less than or equal": "<=",
    "plus equals": "+=",
    "minus equals": "-=",
    "times equals": "*=",
    "divide equals": "/=",
    "modulo equals": "%=",
    "and and": "&&",
    "or or": "||",
    "not not": "!!",
    "plus plus": "++",
    "minus minus": "--",
    "dot dot dot": "...",
    "spread operator": "...",
    "rest operator": "...",
    "nullish coalescing": "??",
    "optional chaining": "?.",
    "ternary": "?",
    "pipe": "|",
    "ampersand": "&",
    "tilde": "~",
    "caret": "^",
    "backslash": "\\",
    "forward slash": "/",
    "at symbol": "@",
    "hash": "#",
    "dollar sign": "$",
    "percent": "%",
    "underscore": "_",
    "backtick": "`",
}

# -----------------------------------------------------------------------------
# Main Processing Function

def nerd_dictation_process(text: str) -> str:
    """
    Main text processing function with LLM-first architecture.
    LLM handles grammar on raw speech, then technical corrections are applied.
    """
    global _last_processed_text
    
    # Store original text for cache comparison
    original_text = text
    
    # FIRST: Apply LLM processing to raw dictated text
    # This prevents conflicts between LLM and technical corrections
    if original_text != _last_processed_text and original_text.strip():
        text = improve_text_with_llm(text)
        _last_processed_text = original_text  # Use original for comparison
    
    # THEN: Apply deterministic technical corrections
    # These won't conflict with LLM since they're applied after
    
    # Apply multi-word technical replacements
    for match, replacement in TEXT_REPLACE_REGEX:
        text = match.sub(replacement, text)
    
    # Apply punctuation replacements
    for match, replacement in CLOSING_PUNCTUATION.items():
        text = text.replace(" " + match, replacement)
    
    for match, replacement in OPENING_PUNCTUATION.items():
        text = text.replace(match + " ", replacement)
    
    # Apply developer-specific code patterns
    for match, replacement in CODE_PATTERNS.items():
        text = text.replace(match, replacement)
    
    # Apply single word replacements (technical terms, capitalization)
    words = text.split(" ")
    for i, w in enumerate(words):
        w_init = w
        w_test = WORD_REPLACE.get(w)
        if w_test is not None:
            w = w_test
        if w_init == w:
            for match, replacement in WORD_REPLACE_REGEX:
                w_test = match.sub(replacement, w)
                if w_test != w:
                    w = w_test
                    break
        words[i] = w
    
    # Strip any words that were replaced with empty strings
    words[:] = [w for w in words if w]
    text = " ".join(words)
    
    return text