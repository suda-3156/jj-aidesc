# jj-aidesc

A tool for generating commit messages for [jj (Jujutsu)](https://github.com/jj-vcs/jj) using the Gemini API.  
Provides better descriptions than just including the date, time, or author.  
By default, `jj-aidesc` scans your repository for commits without descriptions and generates commit messages for all of them.

## Installation

```bash
pip install git+https://github.com/suda-3156/jj-aidesc.git
```

## Configuration

### API Key Setup

Google AI API key is resolved in the following priority order:

1. **CLI option**: `--api-key`
2. **Config file**: `api_key` in `.jj-aidesc.yaml`
3. **Environment file**: `GOOGLE_GENAI_API_KEY` in `.env` or `.env.local`
4. **Environment variable**: `GOOGLE_GENAI_API_KEY`

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

```sh
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

| Option                            | Short | Description                                                  | Default            |
| --------------------------------- | ----- | ------------------------------------------------------------ | ------------------ |
| `--revisions`                     | `-r`  | Target revset                                                | `mutable()`        |
| `--revise`, `--include-described` |       | Include revisions for targets that already have descriptions | `false`            |
| `--style`                         | `-s`  | Description style                                            | `conventional`     |
| `--apply`                         | `-a`  | Apply all without confirmation                               | `false`            |
| `--dry-run`                       | `-n`  | Generate only, don't apply                                   | `false`            |
| `--model`                         |       | Gemini model to use                                          | `gemini-2.5-flash` |
| `--language`                      | `-l`  | Output language                                              | `en`               |

### Styles (`--style`)

| Style          | Description                                                         |
| -------------- | ------------------------------------------------------------------- |
| `conventional` | [Conventional Commits](https://www.conventionalcommits.org/) format |
| `follow`       | Follow existing description style in the repository                 |
| `simple`       | Simple, concise format                                              |

## Subcommands

### `jj-aidesc init`

Generate a config file template:

```bash
jj-aidesc init
jj-aidesc init --config path/to/config.yaml
jj-aidesc init --force  # Overwrite existing file
```

### Config File

You can specify default settings in `.jj-aidesc.yaml` (searches current directory or repository root):

```yaml
# .jj-aidesc.yaml
google-genai:
  # API key (can also be set via GOOGLE_GENAI_API_KEY env var)
  # api_key: "your-api-key"

  # Model to use
  model: "gemini-2.5-flash"

  # Temperature (0.0 - 1.0)
  temperature: 0.0

  # Output language
  language: English

  # Style: conventional, follow, simple
  style: conventional
```
