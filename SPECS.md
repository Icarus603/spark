# Spark - AI Coding Platform Technical Specification

> **"Sut-pak, Spark, 識拍火花"**  
> *AI that learns your rhythm, ignites your innovation*

## Executive Summary

**Spark** is a complete AI-powered coding platform that learns from your development patterns and autonomously explores new coding possibilities. Built by transforming the robust CUA (Computer Use Agent) monorepo into a comprehensive AI coding platform, Spark leverages proven automation infrastructure to deliver intelligent coding assistance through pattern learning, autonomous code exploration, and curated discovery presentation.

### **Current Reality Check** 🔍
**Project Status**: Early development phase
- ✅ **Solid Foundation**: Complete CUA automation infrastructure (agent system, computer interface, multi-platform support)
- 🚧 **Spark Intelligence Layer**: In planning/development phase  
- 📋 **AI Coding Features**: Awaiting implementation (learning, exploration, discovery)

### Core Value Proposition
- **Learn Your Rhythm**: Automatically analyzes your coding patterns, preferences, and workflows
- **Autonomous Exploration**: Generates and explores new coding approaches while you sleep
- **Curated Discoveries**: Presents valuable findings through an intuitive terminal interface
- **Safe Integration**: Provides secure ways to incorporate discoveries into your projects

### Technical Foundation
**Spark Platform = Learning Engine + Exploration Engine + CUA Foundation**

---

## System Architecture

### High-Level Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SPARK PLATFORM                          │
│                     AI Coding Intelligence                      │
├─────────────────────────────────────────────────────────────────┤
│                      USER EXPERIENCE LAYER                      │
│  CLI Interface  │  Discovery UI  │  Integration  │  Analytics   │
│  ─────────────  │  ────────────  │  ───────────  │  ─────────   │ 
│  spark          │  Terminal      │  Safe Code    │  Progress    │
│  spark learn    │  Presentation  │  Merging      │  Tracking    │
│  spark explore  │  Rich Format   │  Rollback     │  Insights    │
├─────────────────────────────────────────────────────────────────┤
│                       INTELLIGENCE LAYER                        │
│  Learning Eng.  │  Exploration   │  Discovery    │  Git         │
│  ─────────────  │  Engine        │  Manager      │  Analysis    │
│  Pattern Recog  │  Autonomous    │  Curation     │  Workflow    │
│  Style Analysis │  Code Gen      │  Ranking      │  Insights    │
│  Preference Map │  Test & Valid  │  Filtering    │  History     │
├─────────────────────────────────────────────────────────────────┤
│                      AUTOMATION FOUNDATION                      │
│  CUA Agent      │  Computer      │  Core         │  Extensions  │
│  ─────────────  │  Interface     │  Services     │  ─────────   │ 
│  Agent Loops    │  Multi-OS      │  Telemetry    │  SOM         │
│  Callbacks      │  Automation    │  Logging      │  MCP         │
│  Trajectories   │  Providers     │  Config       │  PyLume      │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
┌─── LEARNING PHASE (Continuous) ────────────────────────────────┐
│                                                                │
│  File Changes → Git Analysis → Pattern Recognition →           │
│  Style Detection → Preference Mapping → Pattern Storage        │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌─── EXPLORATION PHASE (Scheduled) ──────────────────────────────┐
│                                                                │
│  User Patterns → Exploration Goals → CUA Agent Execution →     │
│  Code Generation → Testing & Validation → Discovery Storage    │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌─── DISCOVERY PHASE (On-Demand) ────────────────────────────────┐
│                                                                │
│  Discovery Request → Curation & Ranking → Rich Presentation →  │
│  User Selection → Safe Integration → Project Update            │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Project Structure & Organization

### Monorepo Architecture

**Current Location**: `/Users/liuzetfung/Code/projects/spark/` (Project Root)

```
spark/                                          # PROJECT ROOT (current directory)
│
├── 📦 EMBEDDED FOUNDATION (CUA)                # Automation Infrastructure
│   └── libs/python/
│       ├── agent/          # Agent system (loops, callbacks, adapters)
│       ├── computer/       # Computer interface (cross-platform automation)
│       ├── core/           # Core utilities (telemetry, logging)
│       ├── som/            # Set-of-Mark functionality
│       ├── mcp-server/     # Model Context Protocol server
│       ├── computer-server/# Computer automation server
│       ├── pylume/         # Virtualization support
│       │
│       └── spark/          # 🚀 SPARK MAIN IMPLEMENTATION
│           ├── learning/       # Pattern learning and analysis
│           │   ├── pattern_engine.py      # Core pattern recognition
│           │   ├── style_analyzer.py      # Code style analysis  
│           │   ├── preference_mapper.py   # User preference detection
│           │   └── confidence_scorer.py   # Pattern confidence metrics
│           │
│           ├── exploration/    # Autonomous code exploration
│           │   ├── exploration_agent.py   # Main exploration orchestrator
│           │   ├── code_generator.py      # Code generation engine
│           │   ├── validator.py           # Code testing and validation
│           │   └── goal_planner.py        # Exploration goal planning
│           │
│           ├── discovery/      # Discovery management and curation
│           │   ├── curator.py            # Discovery filtering and ranking  
│           │   ├── presenter.py          # Rich terminal presentation
│           │   ├── integrator.py         # Safe code integration
│           │   └── feedback_collector.py # User feedback processing
│           │
│           ├── git/           # Git repository analysis 🔲
│           │   ├── repository.py         # Git repo interface
│           │   ├── commit_analyzer.py    # Commit pattern analysis
│           │   ├── code_detector.py      # Semantic code change detection
│           │   ├── branch_analyzer.py    # Workflow pattern recognition
│           │   └── integration.py        # CLI command integration
│           │
│           ├── storage/        # Data persistence layer  
│           │   ├── patterns_v2.py        # Enhanced pattern storage
│           │   ├── discoveries_v2.py     # Discovery database  
│           │   ├── migration.py          # Schema migration system
│           │   ├── backup.py             # Data backup and sync
│           │   ├── privacy.py            # Data encryption and privacy
│           │   └── indexing.py           # Search and indexing
│           │
│           ├── cli/           # Command-line interface
│           │   ├── main.py              # Main CLI entry point
│           │   ├── commands/            # Individual command implementations
│           │   │   ├── learn.py         # Background learning commands
│           │   │   ├── explore.py       # Exploration commands  
│           │   │   ├── discover.py      # Discovery browsing commands
│           │   │   └── integrate.py     # Integration commands
│           │   ├── ui/                  # CLI user interface components
│           │   │   ├── dashboard.py     # Interactive status dashboard
│           │   │   ├── presenter.py     # Rich content presentation
│           │   │   └── progress.py      # Progress tracking display
│           │   └── integration.py       # CLI framework integration
│           │
│           └── core/          # Core Spark utilities
│               ├── config.py            # Configuration management
│               ├── telemetry.py         # Usage analytics and telemetry  
│               ├── scheduler.py         # Task scheduling system
│               └── error_recovery.py    # Error handling and recovery
│
├── 🎯 PROJECT CONFIGURATION & EXECUTION        # Project Root Files
│   ├── pyproject.toml         # Workspace and dependency configuration  
│   ├── run_spark.py          # Development runner script
│   └── __main__.py           # Direct execution entry point
│
├── 📚 DOCUMENTATION & EXAMPLES                 # Documentation and Guides
│   ├── README.md                  # User installation and usage guide
│   ├── SPECS.md                   # This technical specification
│   ├── DESIGN.md                  # User experience and design decisions
│   ├── PRD.md                     # Product requirements and vision
│   ├── docs/                      # Detailed documentation
│   └── examples/                  # Usage examples and tutorials
│
└── 🧪 DEVELOPMENT & TESTING                    # Development Support  
    ├── tests/                     # Test suites
    ├── benchmarks/                # Performance benchmarks
    ├── scripts/                   # Development and build scripts
    └── notebooks/                 # Development notebooks and explorations
```

**CLI Execution Methods:**
```bash
# Primary: Direct spark command (like claude)
spark                             # Main command - auto-detects and initializes

# Development: Module execution  
python -m spark                   # Uses libs/python/spark/__main__.py

# Development: Direct runner
python run_spark.py              # Uses run_spark.py in project root
```

---

## Core Components Specification

Based on deep analysis of the PRD and DESIGN documents, Spark is architected as an AI-powered coding exploration platform that learns from developer patterns and autonomously explores during nighttime hours. The core components work together to deliver the key user journey: **Learn → Explore → Discover → Integrate**.

### 1. Pattern Learning Engine (`libs/python/spark/learning/`) 🔲

**Mission**: Learn the developer's rhythm, style, and preferences through continuous, passive observation.

**Architecture Philosophy**: 
Spark learns not just *what* you code, but *how* you think and work. It builds a comprehensive model of your coding DNA through multiple observation layers.

**Key Components**:

#### 1.1 Git Pattern Analyzer (`learning/git_patterns.py`)
- **Purpose**: Extract high-level development patterns from git history
- **Capabilities**:
  - Commit message pattern recognition (conventional commits, personal style)
  - Branching workflow detection (feature branches, release cycles)
  - Development rhythm analysis (work hours, commit frequency, merge patterns)  
  - Collaboration style detection (code review patterns, pair programming signals)
- **Integration**: Leverages CUA's trajectory system for git interaction automation

#### 1.2 Code Style Analyzer (`learning/style_analyzer.py`)  
- **Purpose**: Understand coding preferences across languages and paradigms
- **Capabilities**:
  - AST-based pattern detection (function length, nesting preferences, naming conventions)
  - Language feature usage patterns (functional vs OOP, async patterns, error handling styles)
  - Architectural preference detection (layered, modular, microservices, monolith tendencies)
  - Testing philosophy recognition (TDD signals, coverage preferences, test organization)
- **Multi-Language Support**: Python, JavaScript/TypeScript, Go, Rust, Java initially

#### 1.3 Preference Mapper (`learning/preferences.py`)
- **Purpose**: Build predictive models of developer choices and interests  
- **Capabilities**:
  - Technology adoption patterns (early adopter vs. conservative, framework preferences)
  - Problem-solving approach patterns (performance vs. readability trade-offs)
  - Learning trajectory prediction (what technologies/concepts to explore next)
  - Context-aware preference switching (work vs. personal project different styles)
- **Intelligence**: Uses simple rule-based inference, not ML models (keeping it maintainable)

#### 1.4 Pattern Confidence Scorer (`learning/confidence.py`)
- **Purpose**: Assign confidence levels to detected patterns for exploration targeting
- **Capabilities**:
  - Statistical confidence based on sample size and consistency
  - Pattern stability scoring (how consistent patterns are over time)
  - Context validity scoring (pattern strength in different project types)
  - Exploration readiness scoring (which patterns are strong enough to base explorations on)

**Data Sources**:
- Git repository analysis (commits, branches, merges, tags)
- File system monitoring (file types, directory structure, import patterns)
- Development tool integration (IDE preferences, terminal usage, test runners)
- Time-based behavioral patterns (work hours, session lengths, break patterns)

**Privacy Design**: All learning happens locally with optional encrypted pattern sharing

---

### 2. Autonomous Exploration Engine (`libs/python/spark/exploration/`) 🔲

**Mission**: During nighttime hours, autonomously explore coding possibilities that align with learned patterns but push creative boundaries.

**Architecture Philosophy**:
The exploration engine is Spark's creative core. It combines learned patterns with AI-powered code generation, using CUA's automation capabilities to actually execute and test explorations.

**Key Components**:

#### 2.1 Exploration Orchestrator (`exploration/orchestrator.py`)
- **Purpose**: Plan and execute autonomous exploration sessions
- **Capabilities**:
  - Session planning based on available time and resource budgets
  - Risk-adjusted exploration (conservative to experimental based on user preferences)
  - Parallel exploration execution (multiple concurrent experiments)
  - Progress monitoring and adaptive session management
- **Integration**: Deep integration with CUA agent loops for autonomous operation

#### 2.2 Goal Generator (`exploration/goal_generator.py`)
- **Purpose**: Transform patterns and context into specific exploration objectives
- **Capabilities**:
  - Pattern-driven goal synthesis (e.g., "user loves functional patterns" → "explore functional approaches to async error handling")
  - Context-aware goal adaptation (recent commits, current project phase, industry trends)
  - Risk-balanced goal generation (safe improvements vs. boundary-pushing experiments)
  - Multi-objective exploration planning (performance + readability + maintainability)
- **Intelligence**: Rule-based goal generation with pattern-matching algorithms

#### 2.3 Code Generation Engine (`exploration/code_generator.py`)
- **Purpose**: Generate exploratory code that builds on learned patterns
- **Capabilities**:
  - Pattern-guided code generation using Claude Code SDK integration
  - Multi-approach generation (generate 3-5 different approaches per goal)
  - Context-aware generation (understands existing codebase and constraints)
  - Incremental refinement (improve generated code through testing feedback)
- **AI Integration**: Primary integration point with Claude Code SDK for intelligent code generation

#### 2.4 Execution & Validation Engine (`exploration/validator.py`)
- **Purpose**: Execute generated code and validate results automatically
- **Capabilities**:
  - Sandboxed code execution using CUA's computer interface
  - Automated testing (unit tests, integration tests, performance benchmarks)  
  - Code quality assessment (linting, security scanning, best practices check)
  - Result documentation (capture screenshots, performance metrics, output examples)
- **Safety**: Comprehensive sandboxing with rollback capabilities

**Exploration Categories**:
- **Performance Optimization**: Find faster algorithms, better data structures, caching strategies
- **Architecture Exploration**: Test new patterns, refactoring approaches, modular designs
- **Technology Integration**: Explore new libraries, frameworks, language features
- **Creative Coding**: Generate art, visualizations, and experimental projects
- **Learning Projects**: Create educational examples and documentation

---

### 3. Discovery Curation System (`libs/python/spark/discovery/`) 🔲

**Mission**: Transform raw exploration results into curated, actionable discoveries that provide clear value to the developer.

**Architecture Philosophy**:
The morning discovery ritual is Spark's signature experience. Curation is not just filtering—it's about presenting discoveries in a way that inspires and enables action.

**Key Components**:

#### 3.1 Value Assessor (`discovery/value_assessor.py`)
- **Purpose**: Score explorations based on potential impact and relevance
- **Scoring Criteria**:
  - **Technical Value**: Performance improvements, code quality gains, educational value
  - **Relevance Score**: Alignment with current project needs and learned patterns
  - **Actionability**: How easily the discovery can be integrated into real work
  - **Novelty Factor**: Whether it introduces genuinely new concepts or approaches
- **Algorithms**: Multi-factor scoring with user feedback learning

#### 3.2 Discovery Curator (`discovery/curator.py`)
- **Purpose**: Filter and organize discoveries into compelling presentations
- **Capabilities**:
  - Deduplication and similarity grouping
  - Narrative generation (tell the story of each discovery)
  - Impact analysis (before/after comparisons, performance metrics)
  - Integration difficulty assessment with safety scoring
- **Intelligence**: Pattern recognition for discovery quality and user preferences

#### 3.3 Rich Presenter (`discovery/presenter.py`)
- **Purpose**: Create beautiful, terminal-native presentations of discoveries
- **Features**:
  - Rich terminal UI with syntax highlighting and code diffs
  - Interactive browsing with keyboard navigation
  - Expandable sections with detailed explanations
  - Integration preview with step-by-step guides
- **Technology**: Built on `rich` library for beautiful terminal formatting

#### 3.4 Safe Integrator (`discovery/integrator.py`)
- **Purpose**: Provide safe, reversible ways to integrate discoveries into projects
- **Integration Strategies**:
  - **Experimental Branches**: Create feature branches for safe testing
  - **Partial Integration**: Apply only parts of discoveries with clear boundaries
  - **Documentation Mode**: Generate detailed guides without direct code changes
  - **Rollback System**: Complete state restoration if integration causes issues
- **Safety Features**: Comprehensive backup and versioning before any integration

---

### 4. Terminal-Native CLI System (`libs/python/spark/cli/`) 🔲

**Mission**: Provide an intuitive, powerful command-line interface that makes Spark's capabilities easily accessible through the terminal.

**Architecture Philosophy**:
The CLI is not just a command interface—it's the primary user experience. Every interaction should feel natural, informative, and empowering.

**Key Components**:

#### 4.1 Command Framework (`cli/framework.py`)
- **Purpose**: Robust, extensible command structure with rich help and error handling
- **Features**:
  - Hierarchical command structure (`spark learn`, `spark explore`)
  - Context-aware help with examples and common workflows
  - Intelligent error recovery with actionable suggestions
  - Command completion and interactive prompts
- **Integration**: Built on argparse with rich terminal enhancements

#### 4.2 Interactive Dashboard (`cli/dashboard.py`)
- **Purpose**: Real-time status display for learning and exploration progress
- **Features**:
  - Live learning progress with detected patterns
  - Exploration status with time remaining and current activities
  - Discovery count with quick preview of latest findings
  - System health and resource usage monitoring
- **Technology**: Real-time terminal updates with rich formatting

#### 4.3 Discovery Browser (`cli/discovery_browser.py`)
- **Purpose**: Interactive browsing and management of discoveries
- **Features**:
  - Searchable, filterable discovery list with categorization
  - Rich preview with code highlighting and explanations
  - Integration workflow with safety confirmations
  - Historical discovery tracking and favorite management
- **UX**: Inspired by modern CLI tools like `fzf` and `bat` for intuitive navigation

**Core Commands**:
- `spark` - Main status (auto-initializes on first run)
- `spark learn` - Manage background learning
- `spark explore` - Schedule tonight's exploration  
- `spark morning` - Browse discoveries from last exploration
- `spark show` - Browse discoveries and patterns
- `spark integrate <discovery>` - Safely integrate a discovery

---

### 5. Local-First Data Architecture (`libs/python/spark/storage/`) 🔲  

**Mission**: Provide secure, privacy-focused data persistence with advanced search and synchronization capabilities.

**Architecture Philosophy**:
All user data stays local by default. The storage layer is designed for performance, privacy, and extensibility with optional cloud synchronization.

**Key Components**:

#### 5.1 Pattern Database (`storage/patterns.py`)
- **Purpose**: Versioned storage of learned patterns with relationship mapping
- **Schema**:
  - Pattern entities with confidence scores and temporal data  
  - Pattern relationships (complementary, conflicting, derivative patterns)
  - Pattern evolution history with change tracking
  - Context metadata (project type, language, team vs. solo)
- **Technology**: SQLite with JSON fields for flexible schema evolution

#### 5.2 Discovery Archive (`storage/discoveries.py`)
- **Purpose**: Comprehensive storage of exploration results and user feedback
- **Schema**:
  - Discovery entities with full exploration context and results
  - User interaction history (viewed, integrated, dismissed, favorited)
  - Integration history with rollback information
  - Performance metrics and benchmark data
- **Features**: Full-text search using SQLite FTS5 for discovery content

#### 5.3 Privacy & Encryption Layer (`storage/privacy.py`)
- **Purpose**: Protect sensitive data with encryption and PII detection
- **Capabilities**:
  - AES-256 encryption for sensitive pattern data
  - PII detection and automatic anonymization
  - Configurable privacy levels (minimal, standard, detailed logging)
  - Secure key derivation and storage
- **Compliance**: Designed for GDPR compliance with data portability

#### 5.4 Backup & Sync System (`storage/backup.py`)
- **Purpose**: Incremental backups with optional encrypted cloud synchronization
- **Features**:
  - Local incremental backups with configurable retention
  - Optional encrypted cloud sync (S3, GCS) with zero-knowledge design
  - Cross-device synchronization of patterns (with user consent)
  - Disaster recovery with complete state restoration
- **Privacy**: All cloud data encrypted with user-controlled keys

---

### 6. CUA Foundation Integration Layer (`libs/python/spark/foundation/`) 🔲

**Mission**: Seamlessly integrate Spark's intelligence with CUA's proven automation capabilities.

**Architecture Philosophy**:
Spark extends CUA's capabilities without modifying core CUA code. This layer provides clean abstractions for Spark to leverage CUA's powerful automation features.

**Key Components**:

#### 6.1 Agent Integration (`foundation/agent_integration.py`)
- **Purpose**: Integrate Spark's exploration agents with CUA's agent loop system
- **Capabilities**:
  - Spark-aware agent loop customization
  - Exploration-specific callback registration
  - Progress tracking and intermediate result capture
  - Safe exploration boundaries and resource limits
- **Integration**: Extends CUA agent system without core modifications

#### 6.2 Computer Interface Extensions (`foundation/computer_extensions.py`)  
- **Purpose**: Extend CUA's computer interface for Spark-specific automation needs
- **Capabilities**:
  - Development tool automation (IDE control, terminal sessions)
  - Code execution sandboxing and result capture
  - File system monitoring for pattern learning
  - Screenshot and screen recording for result documentation
- **Technology**: Builds on CUA's cross-platform computer interface

#### 6.3 Trajectory Analysis (`foundation/trajectory_analysis.py`)
- **Purpose**: Analyze CUA trajectories for pattern learning and exploration insights
- **Capabilities**:
  - Development session analysis from CUA trajectory data
  - Behavioral pattern extraction from computer interaction logs
  - Workflow optimization insights from automation patterns
  - Integration success metrics from trajectory analysis
- **Data Source**: CUA's comprehensive trajectory logging system

This component architecture reflects Spark's true nature: an AI coding platform that learns from developers and autonomously explores creative possibilities while maintaining safety, privacy, and user control. Each component is designed to work together in the **Learn → Explore → Discover → Integrate** workflow that defines the Spark experience.

---

## Command-Line Interface Specification

Based on DESIGN.md's comprehensive user experience design, the Spark CLI provides a terminal-native interface that embodies the **"Learn → Explore → Discover → Integrate"** workflow through intuitive command design and rich interaction patterns.

### CLI Architecture Philosophy

**Design Principles**:
- **Terminal-Native**: CLI-first interface that feels natural to developers
- **Context-Aware**: Responses adapt to user patterns, time, and current project state
- **Progressive Disclosure**: Essential information by default, detailed breakdowns on request
- **Non-Disruptive**: Background learning without workflow interruption
- **Integration-Ready**: Commands designed for immediate practical use

**Main Command**: `spark`
**Data Architecture**: `~/.spark/` directory with organized pattern and discovery storage

### Core Command Specifications

#### `spark` - Main Command (Auto-Initialize) 🔲
**Purpose**: Primary command that shows status and auto-initializes on first run (like `claude` command).

**First Run Auto-Setup**:
```bash
$ spark
🚀 Welcome to spark! Let's learn your coding rhythm.

📂 Auto-detected projects:
  • ~/Code/projects (5 repositories)
  • ~/Desktop/experiments (3 repositories)
  
🧠 Starting pattern learning...
  • Git analysis: ✓
  • File monitoring: ✓
  • Code style detection: ✓

⚡ Learning started! Use 'spark learn' to manage.
```

**Regular Status Display**:
```bash
$ spark

🧠 Learning Progress (Day 8):
  • Confidence: 85% (Ready for exploration)
  • Languages: Python (67%), TypeScript (23%), Rust (10%)
  • Latest activity: 12 commits, 3 new patterns

🚀 Ready to explore: spark explore
🌅 Check discoveries: spark morning
📊 View patterns: spark show patterns
```

**Auto-Initialize Features**:
- Automatically detects git repositories and starts learning
- No separate setup step required
- Creates `~/.spark/` directory and configuration on first run
- Immediately starts background learning process

---

#### `spark learn` - Learning Management 🔲
**Purpose**: Start/stop passive background learning from filesystem and git activity.

**Usage Patterns**:
```bash
$ spark learn                    # Start background learning
$ spark learn --status          # Check if learning is active  
$ spark learn --stop            # Stop background learning
$ spark learn --watch ~/Code    # Add specific directory to monitoring
```

**Background Process Architecture**:
- **File System Monitoring**: inotify/fsevents for real-time file change detection
- **Git Repository Analysis**: Hooks + periodic scans for commit pattern analysis
- **Pattern Confidence Calculation**: Continuous refinement of detected patterns
- **Resource Management**: <5% CPU usage, <50MB memory footprint

**Learning Sources**:
- Git commit history and branch patterns
- File modification patterns and development sessions
- Code structure changes and refactoring patterns
- Testing patterns and coverage preferences
- Import patterns and dependency usage

---

#### `spark status` - Learning Progress & Pattern Analysis 🔲
**Purpose**: Display current learning state, confidence levels, and detected patterns with actionable insights.

**Default Output Format**:
```bash
$ spark status

🧠 Learning Progress (Day 8):
  • Patterns detected: 52 coding habits
  • Code style: Functional-focused (78% pure functions)
  • Testing habits: TDD practitioner (87% tests-first)
  • Curiosity vectors: Rust integration, Performance optimization

📊 Recent Activity Analysis:
  • 12 commits in last 3 days
  • New explorations: WebAssembly, async patterns
  • Strongest patterns: Error handling, Type safety

🎯 Confidence Level: 85% (Ready for autonomous exploration)

📈 Pattern Details: spark patterns
⚙️  Configuration: spark config
🌙 Plan Tonight: spark explore
```

**Progressive Disclosure Flags**:
- `--detailed`: Extended pattern breakdown with confidence scores
- `--raw`: JSON output for scripting and external analysis
- `--patterns`: Focus on detected patterns with statistical analysis
- `--interactive`: Real-time dashboard with live learning updates

**Intelligence Features**:
- Pattern confidence scoring based on sample size and consistency
- Exploration readiness assessment
- Recent activity contextual analysis
- Actionable next steps based on current state

---

#### `spark explore` - Autonomous Exploration Planning 🔲
**Purpose**: Configure and schedule nighttime autonomous exploration sessions based on learned patterns and user intentions.

**Interactive Planning Flow**:
```bash
$ spark explore

🌅 Based on your patterns, here's tonight's exploration plan:

🎯 Detected Interests:
  • Rust-Python integration (high confidence)
  • Async performance patterns (medium confidence)
  • WebAssembly experiments (emerging interest)

🚀 Proposed Explorations (4-hour budget):
  1. Build Rust extension for your data pipeline functions
  2. Create async utilities matching your error handling style  
  3. Explore WASM compilation for browser deployment

⚙️  Adjust exploration:
  • Focus: [rust|async|wasm|mixed] (default: mixed)
  • Time limit: [2h|4h|6h] (default: 4h)
  • Risk level: [conservative|balanced|experimental] (default: balanced)

Confirm tonight's exploration? [y/n]
✅ Exploration scheduled. Sweet dreams! 🌙
```

**Configuration Options**:
- **Focus Areas**: Language-specific, concept-based, or mixed explorations
- **Time Budget**: 2h/4h/6h exploration windows with resource management
- **Risk Tolerance**: Conservative (safe improvements) to experimental (boundary pushing)
- **Notification Preferences**: Morning summary style and detail level

**Technical Architecture**:
- Pattern-driven goal generation using learned preferences
- CUA agent integration for autonomous execution
- Resource-aware session planning and management
- Safety mechanisms and exploration sandboxing

---

#### `spark morning` - Discovery Experience & Integration 🔲
**Purpose**: Present overnight exploration results with rich presentation and integration assistance.

**Morning Discovery Flow**:
```bash
$ spark morning

🌅 Good morning! While you slept, I explored 3 concepts:

✨ Featured Discovery: Rust Data Pipeline Extension
   📈 Performance: 3.2x speedup on your sorting functions
   💻 Code: /tmp/spark-discoveries/rust-pipeline/
   🧪 Tests: 12 passing, benchmarks included
   
📚 Other Explorations:
   2. Async error handling patterns → spark show async-errors
   3. WASM browser deployment → spark show wasm-deploy

🎯 Integration Ready:
   • Rust extension has zero-config setup for your project
   • Want me to integrate? [y/n]

💡 Learning Update:
   • Confidence in Rust patterns: 67% → 84%
   • New pattern detected: Prefer explicit error types
   
📊 Full Report: spark show
🔄 Give Feedback: spark rate last-exploration
```

**Discovery Presentation Priority**:
1. **Featured Discovery**: Most promising/successful exploration with quantified benefits
2. **Secondary Results**: Other completed explorations with brief descriptions  
3. **Learning Updates**: New patterns detected and confidence improvements
4. **Integration Opportunities**: Ready-to-use discoveries with safety assessment
5. **Feedback Requests**: Rating system for continuous learning improvement

**Integration Workflow**:
- `spark integrate <discovery>` for automatic code integration
- Safety checks and backup creation before modification
- Clear rollback instructions and conflict resolution
- Step-by-step integration guides with validation

---

#### `spark show` - Discovery Management 🔲
**Purpose**: Browse, search, and manage all historical discoveries with simple interface.

**Discovery Management Features**:
```bash
$ spark show                          # List recent discoveries
$ spark show rust                     # Show Rust-related discoveries
$ spark show --all                    # Show all discoveries
$ spark show patterns                 # Show detected patterns
$ spark show config                   # Show configuration
```

**Discovery Organization**:
- **Chronological Browsing**: Date-organized with flexible date ranges
- **Tag-Based Filtering**: Language, concept, success rate, integration status
- **Search Functionality**: Full-text search across descriptions, code, and metadata
- **Export Capabilities**: JSON, markdown, or code-only exports for documentation
- **Archive Management**: Storage optimization with configurable retention policies

**Rich Terminal UI**:
- Interactive browsing with keyboard navigation
- Expandable sections with detailed explanations and code previews
- Integration preview with step-by-step guides
- Historical discovery tracking with user ratings and feedback

---

#### `spark patterns` - Advanced Pattern Analysis 🔲
**Purpose**: Deep dive into detected coding patterns with confidence analysis and learning insights.

**Pattern Analysis Categories**:
```bash
$ spark patterns                      # Overview of all detected patterns
$ spark patterns --detailed          # Statistical breakdown with confidence scores
$ spark patterns --lang python       # Language-specific pattern analysis
$ spark patterns --evolution         # Pattern changes over time
$ spark patterns --export           # Export patterns for sharing or backup
```

**Pattern Categories**:
- **Language Preferences**: Usage frequency, style patterns, idiomatic preferences
- **Workflow Habits**: Git patterns, testing approaches, file organization strategies
- **Learning Trajectory**: Skill development patterns, curiosity evolution tracking
- **Style Consistency**: Formatting preferences, naming conventions, architectural choices

**Confidence Indicators**:
- **Sample Size**: Number of observations supporting each pattern
- **Consistency**: Variance in pattern application across different contexts
- **Recency**: How current and active the pattern detection is
- **Validation**: Success rate of pattern-based exploration predictions

---

#### `spark integrate <discovery>` - Safe Discovery Integration 🔲
**Purpose**: Provide safe, reversible ways to integrate discoveries into existing projects with comprehensive safety mechanisms.

**Integration Strategies**:
```bash
$ spark integrate rust-pipeline       # Direct integration with safety checks
$ spark integrate --dry-run async-errors  # Preview integration without changes
$ spark integrate --branch experimental   # Create feature branch for testing
$ spark integrate --partial rust-pipeline # Apply only specific parts
$ spark integrate --rollback             # Rollback previous integration
```

**Safety Features**:
- **Experimental Branches**: Create feature branches for safe testing and validation
- **Partial Integration**: Apply only parts of discoveries with clear boundaries
- **Documentation Mode**: Generate detailed implementation guides without code changes
- **Rollback System**: Complete state restoration if integration causes issues
- **Conflict Resolution**: Intelligent merge conflict resolution with user guidance

**Integration Workflow**:
1. **Pre-Integration Analysis**: Impact assessment and compatibility checking
2. **Backup Creation**: Complete project state backup before modifications
3. **Staged Application**: Incremental integration with validation at each step
4. **Testing Integration**: Automated testing of integrated changes
5. **Rollback Availability**: One-command rollback with full state restoration

---

#### `spark show <discovery>` & `spark rate <discovery>` - Discovery Interaction 🔲
**Purpose**: Detailed discovery viewing and feedback collection for continuous learning improvement.

**Discovery Viewing**:
```bash
$ spark show rust-pipeline           # Detailed discovery presentation
$ spark show async-errors --code    # Focus on code changes and examples
$ spark show wasm-deploy --impact   # Highlight performance and impact metrics
```

**Feedback Collection**:
```bash
$ spark rate last-exploration 4/5   # Explicit numerical rating
$ spark rate rust-pipeline excellent # Qualitative feedback
$ spark rate --comment "Great performance improvement, easy integration"
```

**Learning Enhancement**:
- **Implicit Feedback**: Integration actions as positive signals, ignoring as neutral
- **Explicit Ratings**: 1-5 scale with optional detailed comments
- **Adaptive Behavior**: High-rated patterns get reinforced in future explorations
- **Pattern Validation**: Success metrics improve confidence in related patterns

---

### Advanced Command Features

#### Context-Aware Help System
```bash
$ spark help                         # Context-sensitive help based on current state
$ spark help learn                   # Command-specific help with examples
$ spark help --getting-started      # Guided workflow for new users
```

#### Configuration Management
```bash
$ spark config                       # Show current configuration
$ spark config --privacy-settings   # Privacy and data collection preferences
$ spark config --exploration-prefs  # Exploration scheduling and risk preferences
$ spark config --reset             # Reset to defaults with confirmation
```

#### System Integration
```bash
$ spark --version                   # Version information and dependency status
$ spark --health                    # System health check and diagnostics
$ spark --logs                      # Access learning and exploration logs
```

This CLI specification provides a comprehensive, user-centered interface that transforms the complex AI coding exploration process into intuitive, terminal-native commands that respect developer workflows while delivering powerful autonomous exploration capabilities.

---

## Implementation Roadmap

**Current Reality Assessment**: The project has a solid CUA foundation with proven automation capabilities, but all Spark intelligence components need to be implemented from scratch. This roadmap prioritizes delivering value incrementally while building toward the complete autonomous exploration vision.

**Foundation Status**: ✅ **CUA Infrastructure Complete**
- ✅ Agent system with loops and callbacks
- ✅ Cross-platform computer interface  
- ✅ Core services (telemetry, logging, config)
- ✅ Monorepo structure and build system

**Implementation Priority**: Build Spark intelligence layer on top of proven CUA foundation

---

### Stage 1: Minimal Viable Spark (Weeks 1-6)
**Goal**: Deliver immediate value with basic learning and discovery workflow

#### Stage 1.1: Basic CLI & Learning Foundation (Weeks 1-2)
**Deliverable**: Working `spark` (auto-init), `spark learn`, `spark status` commands with simple pattern detection

**Implementation Tasks**:
- [x] **CLI Framework**: Basic command structure using CUA patterns (libs/python/spark/cli/) ✅
  - Core command parsing and routing (`cli/main.py`, `cli/commands/`)
  - Basic configuration management (`core/config.py`)
  - Initial terminal formatting using `rich` library
- [x] **Git Pattern Detection**: Simple git analysis for initial learning (libs/python/spark/learning/) ✅
  - Basic commit pattern analysis (`learning/git_patterns.py`)
  - Simple language detection from file extensions  
  - Confidence scoring based on commit frequency and recency
- [x] **Local Storage**: SQLite-based pattern storage (libs/python/spark/storage/) ✅
  - Basic pattern database schema (`storage/patterns.py`)
  - Configuration persistence (`storage/config.py`)
  - Data migration foundation (`storage/migration.py`)

**Success Criteria**:
- `spark` successfully auto-initializes and configures monitoring for git repositories
- `spark learn --status` shows basic patterns (languages, commit frequency)
- `spark status` displays confidence level and detected patterns
- Background learning runs without affecting system performance (<5% CPU)

#### Stage 1.2: Enhanced Pattern Learning (Weeks 3-4)
**Deliverable**: Sophisticated pattern detection worthy of autonomous exploration

**Implementation Tasks**:
- [x] **Multi-Dimensional Pattern Analysis** (libs/python/spark/learning/) ✅
  - Code style detection using AST parsing (`learning/style_analyzer.py`)
  - Development rhythm analysis (work hours, session patterns)
  - Technology preference mapping (`learning/preference_mapper.py`)
  - Pattern confidence refinement (`learning/confidence_scorer.py`)
- [x] **File System Integration** (libs/python/spark/learning/) ✅
  - Real-time file change monitoring (inotify/fsevents)
  - Import pattern analysis and dependency tracking
  - Project structure analysis and architectural preferences
- [x] **Rich Status Interface** (libs/python/spark/cli/) ✅
  - Detailed pattern breakdown with confidence scores
  - Interactive status dashboard (`cli/terminal.py`)
  - Pattern export and analysis tools

**Success Criteria**:
- Pattern detection accuracy >80% (validated by user feedback)
- Confidence level reaches "exploration ready" (>85%) within 5-7 days of use
- `spark status --detailed` provides actionable insights about coding patterns
- `spark patterns` shows comprehensive analysis across multiple dimensions

#### Stage 1.3: Basic Discovery System (Weeks 5-6)
**Deliverable**: Simple exploration execution and discovery presentation

**Implementation Tasks**:
- [ ] **Manual Exploration Mode** (libs/python/spark/exploration/)
  - Simple exploration orchestrator for user-initiated explorations
  - Basic code generation using Claude Code SDK integration
  - Exploration result capture and storage
- [ ] **Discovery Presentation** (libs/python/spark/discovery/)
  - Basic discovery curation and ranking (`discovery/curator.py`)
  - Rich terminal presentation of exploration results (`discovery/presenter.py`)
  - Simple discovery storage and retrieval
- [ ] **Integration Commands** (libs/python/spark/cli/)
  - `spark show` for browsing exploration results
  - `spark show <discovery>` for detailed discovery viewing
  - Basic feedback collection (`spark rate <discovery>`)

**Success Criteria**:
- Users can manually trigger explorations that produce working code
- Discovery presentation clearly communicates value and integration steps
- Basic feedback loop improves exploration relevance over time
- Exploration results stored and retrievable through CLI commands

---

### Stage 2: Autonomous Exploration Engine (Weeks 7-12)
**Goal**: Implement the core "nighttime exploration" experience that defines Spark

#### Stage 2.1: Exploration Scheduling & Planning (Weeks 7-8)
**Deliverable**: Working `spark explore` command with intelligent exploration planning

**Implementation Tasks**:
- [ ] **Goal Generation Engine** (libs/python/spark/exploration/)
  - Pattern-driven exploration goal synthesis (`exploration/goal_generator.py`)
  - Risk-adjusted goal planning (conservative to experimental)
  - Time-budget aware session planning
- [ ] **Exploration Scheduler** (libs/python/spark/core/)
  - Scheduling system with cron-like capabilities (`core/scheduler.py`)
  - Resource management and exploration session limits
  - Progress monitoring and adaptive time management
- [ ] **Evening Planning Interface** (libs/python/spark/cli/)
  - `spark explore` interactive planning workflow
  - Exploration preference configuration and adjustment
  - Pre-exploration summary and confirmation

**Success Criteria**:
- `spark explore` generates relevant exploration goals based on learned patterns
- Exploration scheduling works reliably across different operating systems
- Users can customize focus areas, time limits, and risk tolerance
- Exploration sessions respect resource limits and time budgets

#### Stage 2.2: Autonomous Code Generation & Validation (Weeks 9-10)
**Deliverable**: CUA-powered autonomous exploration that generates and tests code

**Implementation Tasks**:
- [ ] **Exploration Agent** (libs/python/spark/exploration/)
  - CUA agent integration for autonomous operation (`exploration/orchestrator.py`)
  - Claude Code SDK integration for intelligent code generation
  - Multi-approach generation (3-5 variations per goal)
- [ ] **Execution & Validation Engine** (libs/python/spark/exploration/)
  - Sandboxed code execution using CUA computer interface
  - Automated testing pipeline for generated code (`exploration/validator.py`)
  - Code quality assessment and benchmarking
- [ ] **Session Management** (libs/python/spark/core/)
  - Exploration session recording and trajectory capture
  - Progress tracking and intermediate result storage
  - Error recovery and graceful session termination

**Success Criteria**:
- Autonomous explorations produce working, tested code >70% of the time
- Exploration sessions complete within time budgets without manual intervention  
- Generated code follows detected user patterns and style preferences
- Exploration failures are logged and contribute to learning improvements

#### Stage 2.3: Morning Discovery Experience (Weeks 11-12)
**Deliverable**: Rich `spark morning` experience with safe integration

**Implementation Tasks**:
- [ ] **Advanced Discovery Curation** (libs/python/spark/discovery/)
  - Multi-factor ranking algorithms for discovery quality
  - Impact analysis and integration difficulty assessment
  - Narrative generation for discovery storytelling
- [ ] **Safe Integration System** (libs/python/spark/discovery/)
  - Multiple integration strategies (branch, partial, documentation) (`discovery/integrator.py`)
  - Comprehensive backup and rollback mechanisms  
  - Conflict resolution and user guidance
- [ ] **Morning Discovery Interface** (libs/python/spark/cli/)
  - `spark morning` rich presentation with featured discoveries
  - Integration workflow with safety confirmations
  - Learning updates and feedback collection

**Success Criteria**:
- >60% of morning discoveries rated as valuable by users
- Integration success rate >80% with zero data loss incidents
- Morning ritual takes <10 minutes but provides clear value
- Users consistently use `spark morning` as part of daily workflow

---

### Stage 3: Production Polish & Advanced Features (Weeks 13-20)
**Goal**: Production-ready Spark with advanced intelligence and reliability

#### Stage 3.1: Advanced Pattern Recognition (Weeks 13-15)
**Deliverable**: Sophisticated learning that improves over time

**Implementation Tasks**:
- [ ] **Cross-Project Learning** (libs/python/spark/learning/)
  - Pattern analysis across multiple repositories and projects
  - Team collaboration pattern detection and analysis
  - Domain-specific pattern recognition (web, ML, systems, mobile)
- [ ] **Temporal Pattern Analysis** (libs/python/spark/learning/)
  - Pattern evolution tracking over time
  - Skill development and learning trajectory analysis
  - Seasonal and contextual pattern adaptation
- [ ] **Advanced Confidence Scoring** (libs/python/spark/learning/)
  - Multi-dimensional confidence with uncertainty quantification
  - Pattern validation through exploration success metrics
  - Adaptive learning rate based on pattern stability

**Success Criteria**:
- Pattern recognition accuracy >90% after 30 days of use
- Learning adapts to changing user preferences and skill development
- Cross-project insights provide valuable architectural and technology guidance
- Pattern confidence correlates strongly with exploration success rates

#### Stage 3.2: Intelligent Exploration Goals (Weeks 16-17)
**Deliverable**: Proactive exploration suggestions and continuous improvement

**Implementation Tasks**:
- [ ] **Proactive Goal Suggestion** (libs/python/spark/exploration/)
  - Industry trend analysis and technology adoption detection
  - Proactive exploration goal generation based on detected gaps
  - Integration with external knowledge sources (documentation, tutorials)
- [ ] **Contextual Awareness** (libs/python/spark/exploration/)
  - Project phase detection (prototyping, development, maintenance)
  - Deadline and constraint awareness for exploration prioritization
  - Team collaboration context for exploration relevance
- [ ] **Continuous Learning** (libs/python/spark/core/)
  - Exploration outcome analysis for goal generation improvement
  - User feedback integration for personalized exploration strategy
  - A/B testing framework for exploration approach optimization

**Success Criteria**:
- Proactive exploration suggestions have >50% user acceptance rate
- Exploration relevance improves continuously based on user feedback
- Context-aware exploration adapts to project constraints and deadlines
- Exploration strategies optimize based on historical success patterns

#### Stage 3.3: Production Readiness (Weeks 18-20)
**Deliverable**: Reliable, performant, well-documented Spark ready for broad use

**Implementation Tasks**:
- [ ] **Performance Optimization** (All components)
  - Memory usage optimization for long-running learning processes
  - Background operation efficiency improvements
  - Discovery presentation and CLI responsiveness optimization
- [ ] **Cross-Platform Reliability** (libs/python/spark/)
  - Comprehensive testing on macOS, Linux, and Windows (via containers)
  - Platform-specific optimization and compatibility improvements
  - CI/CD pipeline with automated testing across platforms
- [ ] **Documentation & Onboarding** (Documentation)
  - Complete user documentation with tutorials and troubleshooting
  - Developer documentation for extending and customizing Spark
  - Community onboarding materials and contribution guidelines
- [ ] **Security & Privacy** (libs/python/spark/storage/, libs/python/spark/core/)
  - Data encryption for sensitive pattern information
  - Privacy controls and data anonymization options  
  - Security audit and vulnerability assessment

**Success Criteria**:
- System stability >99% uptime for background learning processes
- CLI response times consistently meet performance specifications (<500ms for status)
- Cross-platform compatibility with consistent user experience
- Security and privacy controls meet enterprise-grade standards

---

### Risk Mitigation & Dependencies

#### High-Risk Areas
1. **Claude Code SDK Integration Complexity**
   - *Risk*: SDK integration more complex than anticipated
   - *Mitigation*: Early prototype integration in Stage 1.3, fallback to direct API calls

2. **Autonomous Exploration Safety**
   - *Risk*: Explorations cause system instability or data loss
   - *Mitigation*: Comprehensive sandboxing in Stage 2.2, extensive safety testing

3. **Pattern Learning Accuracy**
   - *Risk*: Pattern detection insufficient for valuable explorations  
   - *Mitigation*: User feedback integration from Stage 1.2, manual pattern override options

#### Critical Dependencies
1. **CUA Stability**: Continued development and maintenance of CUA foundation
2. **Claude Code SDK Access**: Reliable access to Claude Code SDK for code generation  
3. **User Feedback**: Active user feedback for pattern validation and exploration improvement

#### Success Gates
- **Stage 1 Gate**: 5+ daily active users with >80% pattern accuracy
- **Stage 2 Gate**: >70% exploration success rate and user satisfaction >4/5
- **Stage 3 Gate**: Production deployment with >100 daily active users

This implementation roadmap prioritizes delivering immediate value while building systematically toward the complete Spark vision, with clear milestones and realistic timelines based on the current CUA foundation.

---

## Success Metrics & Quality Gates

### Functional Success Criteria
- [ ] **Learning Accuracy**: >85% agreement between detected patterns and developer self-assessment
- [ ] **Exploration Success**: >70% of explorations produce working, valuable code
- [ ] **Integration Safety**: 100% rollback capability with <1% data loss incidents
- [ ] **Performance**: Background learning with <5% performance impact on development workflow
- [ ] **Reliability**: <2% error rate in normal operation with graceful failure handling

### User Experience Success Criteria  
- [ ] **Discoverability**: Users can find and understand key functionality within 5 minutes
- [ ] **Value Recognition**: >60% of discoveries rated as valuable or actionable by users
- [ ] **Integration Confidence**: >80% of users comfortable with safe integration process
- [ ] **Non-Disruptive Learning**: Background learning invisible to normal development workflow
- [ ] **Clear Communication**: All system states and actions clearly communicated to users

### Technical Success Criteria
- [ ] **Modular Architecture**: Clear separation of concerns with testable components
- [ ] **Extensible Design**: Easy addition of new learning sources and exploration types
- [ ] **Data Privacy**: All user data remains local with optional encrypted cloud backup
- [ ] **Cross-Platform**: Consistent functionality across macOS, Linux, and Windows
- [ ] **Resource Efficient**: Intelligent resource usage with configurable limits

---

## Technology Stack & Architecture Decisions

This section details the technical architecture decisions for Spark, balancing the need for sophisticated AI capabilities with reliability, performance, and user privacy. Each technology choice reflects Spark's core principles: **local-first operation**, **non-invasive learning**, **autonomous exploration**, and **safe integration**.

### Core Technology Architecture

#### Programming Language: Python 3.12+
**Decision Rationale**: 
- **CUA Compatibility**: Spark extends the existing CUA Python foundation
- **AI Ecosystem**: Rich ecosystem for AI/ML libraries and Claude Code SDK integration
- **Performance**: Python 3.12+ provides significant performance improvements and enhanced type system
- **Development Velocity**: Rapid prototyping and iteration capabilities essential for AI experimentation
- **Cross-Platform**: Consistent behavior across macOS, Linux, and Windows environments

**Specific Requirements**:
- **Minimum Version**: Python 3.12 for improved performance and typing features
- **Type Safety**: Strict typing enforcement using mypy for reliable autonomous operations
- **Async/Await**: Full async/await support for non-blocking learning and exploration
- **Memory Management**: Efficient memory usage for long-running background processes

#### Dependency Management: PDM (Python Dependency Manager)
**Decision Rationale**:
- **CUA Foundation**: Inherits from existing CUA monorepo using PDM backend
- **Workspace Management**: Native workspace support for monorepo structure with PDM
- **Lock File Reliability**: Deterministic dependency resolution with pdm.lock
- **PEP Standards**: Full compliance with PEP 517/518/621 for modern Python packaging
- **Editable Installs**: Efficient editable package management for development

**Configuration Strategy**:
- **Workspace Dependencies**: Core Spark dependencies managed at workspace level via PDM
- **Fast Installation**: PDM for dependency management and workspace setup
- **Lock File Management**: Single pdm.lock file for deterministic builds
- **Development Dependencies**: Editable installations using file:// paths

### AI Integration Architecture

#### Primary AI Provider: Claude Code SDK
**Decision Rationale**:
- **Code Generation Quality**: Superior code generation capabilities with context awareness
- **Integration Design**: Native integration with development workflows and tools
- **Pattern Understanding**: Advanced ability to understand and replicate coding patterns
- **Safety Features**: Built-in safety mechanisms for code generation and execution
- **Developer-Focused**: Designed specifically for developer productivity and exploration

**Integration Strategy**:
```python
# Architectural pattern for Claude Code SDK integration
class SparkAIOrchestrator:
    def __init__(self):
        self.claude_code = ClaudeCodeSDK(
            context_awareness=True,
            pattern_integration=True,
            safety_checks=True
        )
        self.fallback_providers = [DirectAnthropicAPI(), LocalLLM()]
    
    async def generate_exploration(self, patterns, context):
        # Primary: Claude Code SDK for context-aware generation
        # Fallback: Direct API calls for resilience
        # Local: Privacy-first option for sensitive projects
```

**Fallback Architecture**:
- **Direct Anthropic API**: Fallback for Claude Code SDK unavailability
- **Local LLM Integration**: Privacy-focused option using local models (Ollama, LMStudio)
- **Pattern-Based Generation**: Template-based code generation without external AI

#### Computer Automation: CUA Foundation
**Decision Rationale**:
- **Proven Foundation**: Mature, tested system for computer automation
- **Cross-Platform**: Reliable automation across different operating systems  
- **Agent System**: Sophisticated agent loops perfect for autonomous exploration
- **Trajectory System**: Complete session recording for learning and debugging
- **Extensible Design**: Clean extension points for Spark-specific functionality

**Extension Architecture**:
```python
# Spark extends CUA without modifying core CUA code
class SparkComputerExtensions(ComputerInterface):
    def __init__(self, cua_computer):
        self.cua = cua_computer
        self.spark_capabilities = SparkCapabilities()
    
    # Extend CUA's capabilities for Spark-specific needs
    async def execute_exploration_session(self, goals, patterns):
        # Use CUA's proven automation with Spark intelligence
        return await self.cua.execute_with_callbacks(
            SparkExplorationCallbacks(goals, patterns)
        )
```

### Data Architecture & Storage

#### Local-First Storage: SQLite + Extensions
**Decision Rationale**:
- **Privacy by Design**: All data remains local by default
- **Performance**: Fast queries for pattern analysis and discovery retrieval
- **Reliability**: ACID compliance for critical pattern and discovery data
- **Portability**: Single file database for easy backup and synchronization
- **Extension Ecosystem**: Rich ecosystem of SQLite extensions for advanced features

**Database Design**:
```sql
-- Core pattern storage with versioning
CREATE TABLE patterns (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSON NOT NULL  -- Flexible schema for different pattern types
);

-- Full-text search for discoveries and patterns
CREATE VIRTUAL TABLE patterns_search USING fts5(
    pattern_id, content, tokenize = 'porter unicode61'
);

-- Discovery storage with relationship tracking
CREATE TABLE discoveries (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    rank INTEGER NOT NULL,
    success_score REAL NOT NULL,
    integration_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON NOT NULL
);
```

**Advanced Features**:
- **SQLite FTS5**: Full-text search across patterns and discoveries
- **JSON Columns**: Flexible schema evolution without migration complexity
- **WAL Mode**: Write-Ahead Logging for concurrent read/write operations
- **Backup API**: Built-in backup and restore functionality

#### Privacy & Security Layer
**Decision Rationale**:
- **Local-First**: All sensitive data processed locally
- **Encryption**: AES-256 encryption for sensitive pattern data
- **PII Detection**: Automatic detection and anonymization of personal information
- **User Control**: Granular control over data collection and processing
- **Audit Trail**: Complete logging of all data access and modifications

**Security Implementation**:
```python
class SparkPrivacyManager:
    def __init__(self):
        self.encryption = AES256Encryption()
        self.pii_detector = PIIDetector()
        self.anonymizer = DataAnonymizer()
    
    def store_sensitive_pattern(self, pattern_data):
        # Automatic PII detection and anonymization
        cleaned_data = self.pii_detector.clean(pattern_data)
        encrypted_data = self.encryption.encrypt(cleaned_data)
        return self.store_encrypted(encrypted_data)
```

### User Interface Architecture

#### Terminal-Native Interface: Rich + Custom Components
**Decision Rationale**:
- **Developer-Friendly**: Terminal interface matches developer preferences and workflows
- **Performance**: Fast, responsive interface without browser overhead
- **Accessibility**: Screen reader compatible with clear information hierarchy
- **Customization**: Adapts to user's terminal theme and preferences
- **Cross-Platform**: Consistent behavior across different terminal environments

**UI Component Architecture**:
```python
# Modular UI components for consistent experience
class SparkTerminalUI:
    def __init__(self):
        self.console = rich.console.Console()
        self.components = {
            'status_dashboard': StatusDashboard(),
            'discovery_browser': DiscoveryBrowser(), 
            'pattern_analyzer': PatternAnalyzer(),
            'integration_guide': IntegrationGuide()
        }
    
    def render_adaptive_content(self, content, context):
        # Adaptive rendering based on terminal capabilities
        return self.components[content].render(context)
```

**Terminal Optimization**:
- **Rich Library**: Advanced terminal formatting with syntax highlighting
- **Progressive Enhancement**: Graceful degradation for limited terminal capabilities
- **Keyboard Navigation**: Full keyboard navigation for accessibility
- **Responsive Layout**: Adapts to different terminal window sizes

### Development & Quality Assurance

#### Testing Framework: pytest + Custom Test Infrastructure
**Decision Rationale**:
- **Async Testing**: Native support for async/await testing patterns
- **Fixture System**: Powerful fixture system for complex test scenarios
- **Parallel Execution**: Fast test execution with parallel test running
- **Mocking Capabilities**: Comprehensive mocking for external dependencies
- **Integration Testing**: Support for full system integration testing

**Test Architecture**:
```python
# Comprehensive testing for autonomous AI systems
@pytest.fixture
async def spark_test_environment():
    """Complete test environment with mocked AI and CUA components"""
    return SparkTestEnvironment(
        mock_claude_sdk=True,
        mock_computer_interface=True,
        isolated_storage=True
    )

@pytest.mark.asyncio
async def test_autonomous_exploration(spark_test_environment):
    """Test complete exploration workflow in isolated environment"""
    exploration_result = await spark_test_environment.run_exploration(
        patterns=test_patterns,
        goals=test_goals
    )
    assert exploration_result.success_rate > 0.7
```

#### Code Quality: ruff + mypy + Custom Analysis
**Decision Rationale**:
- **Performance**: Ruff provides extremely fast linting and formatting
- **Type Safety**: mypy ensures type correctness for autonomous operations
- **Consistency**: Automated code formatting and style enforcement
- **Security**: Static analysis for security vulnerabilities
- **Custom Rules**: Spark-specific code quality rules and patterns

**Quality Pipeline**:
```bash
# Automated quality checks in CI/CD
ruff check libs/python/spark/          # Fast linting
ruff format libs/python/spark/         # Code formatting  
mypy libs/python/spark/                # Type checking
bandit libs/python/spark/              # Security analysis
pytest tests/ --cov=spark             # Test coverage
```

### Platform Support & Distribution

#### Cross-Platform Strategy
**Decision Rationale**:
- **macOS Primary**: Development focus on macOS for initial release
- **Linux Support**: Full Linux support for server and development environments  
- **Windows Compatibility**: Windows support through WSL and native Python
- **Container Support**: Docker containers for consistent cross-platform deployment
- **CI/CD Testing**: Automated testing across all supported platforms

**Platform-Specific Optimizations**:
- **macOS**: Native fsevents for file system monitoring, integrated notifications
- **Linux**: inotify for efficient file watching, systemd integration options
- **Windows**: File system monitoring via Python watchdog, Windows notifications
- **All Platforms**: Terminal capability detection and optimization

#### Distribution & Packaging
**Decision Rationale**:
- **Python Packaging**: Standard Python package distribution via PyPI
- **Monorepo Structure**: Single repository with multiple packages
- **Console Scripts**: Easy command-line installation and execution
- **Virtual Environment**: Isolated installation to prevent dependency conflicts
- **Auto-Update**: Built-in update mechanism for seamless upgrades

**Installation Strategy**:
```bash
# Primary: Installation via PDM (development)
pdm install                           # Install all dependencies including Spark
pdm run spark                         # Run Spark in development mode

# Alternative: Traditional methods (when published)
pip install spark-ai                  # PyPI distribution
pipx install spark-ai                 # Isolated installation via pipx
```

### Performance & Scalability Architecture

#### Resource Management
**Decision Rationale**:
- **Background Efficiency**: Minimal resource usage during passive learning
- **Burst Capability**: Ability to use additional resources during exploration
- **User Configurability**: User control over resource allocation and limits
- **Monitoring**: Real-time resource usage monitoring and optimization
- **Graceful Degradation**: Maintain functionality under resource constraints

**Performance Targets**:
```python
class SparkPerformanceTargets:
    BACKGROUND_CPU_USAGE = 0.05      # <5% CPU during learning
    BACKGROUND_MEMORY = 50_000_000   # <50MB memory during learning  
    CLI_RESPONSE_TIME = 0.5          # <500ms for status commands
    EXPLORATION_SETUP = 2.0          # <2s for exploration setup
    DISCOVERY_LOADING = 2.0          # <2s for discovery loading
    FILE_MONITOR_LATENCY = 0.1       # <100ms file change detection
```

#### Caching & Optimization
**Decision Rationale**:
- **Intelligent Caching**: Cache frequently accessed patterns and discoveries
- **Lazy Loading**: Load data only when needed for responsive interface
- **Batch Processing**: Batch similar operations for efficiency
- **Database Optimization**: Proper indexing and query optimization
- **Memory Management**: Efficient memory usage with garbage collection awareness

This technology architecture provides the foundation for building Spark as a reliable, performant, and extensible AI coding platform that respects user privacy while delivering powerful autonomous exploration capabilities.