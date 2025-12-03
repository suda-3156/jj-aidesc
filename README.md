# jj-aidesc

AI-powered commit description generator for [jj (Jujutsu)](https://github.com/jj-vcs/jj)

## Overview

`jj-aidesc` detects **commits without descriptions** in your jj repository and automatically generates commit descriptions using AI.

### Use Cases

- Generate descriptions for multiple commits after `jj split`
- Generate descriptions for commits created with `jj new`
- Batch-fill descriptions for commits you forgot to describe

### How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                           jj-aidesc                                 │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │ Detect commits without desc  │
                 │ via jj log                   │
                 │ (empty description & has     │
                 │  changes)                    │
                 └──────────────┬───────────────┘
                                │
                                ▼
              ┌─────────────────────────────────────┐
              │  Target commits                     │
              │  ┌───────────────────────────────┐  │
              │  │ [1] kkmpvw  M src/auth.py     │  │
              │  │ [2] xylqrz  A src/models.py   │  │
              │  │ [3] @ (working copy, empty)   │  │ ← Skip
              │  └───────────────────────────────┘  │
              └─────────────────┬───────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
         ┌─────────────────┐     ┌─────────────────┐
         │ jj diff -r kkmpvw│     │ jj diff -r xylqrz│
         └────────┬────────┘     └────────┬────────┘
                  │                       │
                  ▼                       ▼
         ┌─────────────────┐     ┌─────────────────┐
         │   AI Generate   │     │   AI Generate   │
         │   (Gemini)      │     │   (Gemini)      │
         └────────┬────────┘     └────────┬────────┘
                  │                       │
                  ▼                       ▼
         ┌─────────────────┐     ┌─────────────────┐
         │ jj describe     │     │ jj describe     │
         │ -r kkmpvw       │     │ -r xylqrz       │
         │ -m "feat:..."   │     │ -m "feat:..."   │
         └─────────────────┘     └─────────────────┘
```

### Detection Logic

Commits matching the following conditions are targeted:

| Condition           | Description                                 |
| ------------------- | ------------------------------------------- |
| Empty `description` | "no description set" state                  |
| Not `empty`         | Has changes (empty working copy is skipped) |
| Mutable             | Immutable commits are excluded              |

```bash
# Internal command (conceptual)
jj log --no-graph -T '...' -r 'mutable() & description(exact:"") & ~empty()'
```

## Installation

```bash
pip install git+https://github.com/suda3156/jj-aidesc.git
```

## Configuration

### API Key Setup

Google AI API key is resolved in the following priority order:

1. **CLI option**: `--api-key`
2. **Config file**: `api_key` in `.jj-aidesc.yaml`
3. **Environment file**: `GOOGLE_GENAI_API_KEY` in `.env` or `.env.local`
4. **Environment variable**: `GOOGLE_GENAI_API_KEY`

```bash
# Set via environment variable
export GOOGLE_GENAI_API_KEY="your-api-key"

# Or set via .env file
echo 'GOOGLE_GENAI_API_KEY=your-api-key' >> .env
```

## Usage

### Basic Command

```bash
# Detect commits without description and generate
jj-aidesc
```

### Typical Workflows

#### 1. With `jj split`

```bash
# 1. Run jj split as usual (leave description empty)
jj split --interactive

# 2. After split, generate descriptions for all commits at once
jj-aidesc
```

#### 2. Batch generation after multiple commits

```bash
# Working...
jj new
# ... edit ...
jj new
# ... edit ...

# Generate descriptions for all at once
jj-aidesc
```

### Example Output

```
$ jj-aidesc

Scanning for commits without description...

Found 2 commits:

  [1] kkmpvwqx  src/auth.py, src/utils/crypto.py
  [2] xylqrzmt  src/models/user.py

Generating descriptions...

  [1] kkmpvwqx
      ────────────────────────────────
      feat(auth): add password hashing utility

      - Implement bcrypt-based password hashing
      - Add crypto utility module for secure operations
      ────────────────────────────────
      Apply? [y(apply)/n(skip)/e(dit)/q(uit)]: y
      ✓ Applied

  [2] xylqrzmt
      ────────────────────────────────
      feat(models): add User model with authentication fields

      - Add User dataclass with email and password_hash
      - Implement password verification method
      ────────────────────────────────
      Apply? [y(apply)/n(skip)/e(dit)/q(uit)]: y
      ✓ Applied

Done! 2 commits updated.
```

### Options

| Option        | Short | Description                    | Default            |
| ------------- | ----- | ------------------------------ | ------------------ |
| `--revisions` | `-r`  | Target revset                  | `mutable()`        |
| `--style`     | `-s`  | Description style              | `conventional`     |
| `--apply`     | `-a`  | Apply all without confirmation | `false`            |
| `--dry-run`   | `-n`  | Generate only, don't apply     | `false`            |
| `--model`     |       | Gemini model to use            | `gemini-2.0-flash` |
| `--language`  | `-l`  | Output language                | `en`               |

### Styles (`--style`)

| Style          | Description                                                         |
| -------------- | ------------------------------------------------------------------- |
| `conventional` | [Conventional Commits](https://www.conventionalcommits.org/) format |
| `follow`       | Follow existing description style in the repository                 |
| `simple`       | Simple, concise format                                              |

#### Conventional Commits Example

```
feat(auth): add OAuth2 login support

- Implement Google OAuth2 provider
- Add token refresh mechanism
- Update user model with OAuth fields
```

#### Follow Style

When `--style follow` is specified, the tool analyzes existing commits (with descriptions) in the repository and generates descriptions in the same style.

```bash
# Match existing commit style
jj-aidesc --style follow
```

### Usage Examples

```bash
# Basic (Conventional Commits format)
jj-aidesc

# Generate in Japanese
jj-aidesc --language ja

# Apply all without confirmation
jj-aidesc --apply

# Dry-run only
jj-aidesc --dry-run

# Target specific range
jj-aidesc -r '@-::@'

# Follow existing style
jj-aidesc --style follow
```

## Config File

You can specify default settings in `.jj-aidesc.yaml` (searches current directory or repository root):

```yaml
# .jj-aidesc.yaml
google-genai:
  # API key (can also be set via GOOGLE_GENAI_API_KEY env var)
  # api_key: "your-api-key"

  # Model to use
  model: "gemini-2.0-flash"

  # Temperature (0.0 - 1.0)
  temperature: 0.0

  # Output language
  language: English

  # Style: conventional, follow, simple
  style: conventional
```

### Subcommands

#### `jj-aidesc init`

Generate a config file template:

```bash
jj-aidesc init
jj-aidesc init --config .jj-aidesc.yaml
jj-aidesc init --force  # Overwrite existing file
```
