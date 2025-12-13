# Details about this cli

## How It Works

```plain
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
              │  │ [3] @ (working copy, empty)   │  │ ← Skip by default
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

> If `--include-described` or `--reivse` option is set, the detection pattern includes revisions that already has descriptions

### Revset Expressions (`--revisions`)

The `--revisions` option uses jj's [revset language](https://martinvonz.github.io/jj/latest/revsets/) to specify which commits to target. Default is `mutable()`.

#### Common Revset Patterns

| Revset       | Description                               |
| ------------ | ----------------------------------------- |
| `mutable()`  | All mutable (editable) commits (default)  |
| `@`          | Current working copy commit               |
| `@-`         | Parent of current commit                  |
| `@--`        | Grandparent of current commit             |
| `trunk()..@` | Commits from trunk to current (exclusive) |
| `@-::@`      | Parent to current (inclusive range)       |
| `abc123`     | Specific commit by change ID              |
| `branches()` | All branch heads                          |
| `mine()`     | Commits authored by you                   |

#### Revset Operators

| Operator | Description                     | Example              |
| -------- | ------------------------------- | -------------------- |
| `x & y`  | Intersection (both conditions)  | `mutable() & mine()` |
| `x \| y` | Union (either condition)        | `@- \| @`            |
| `~x`     | Negation (not matching)         | `~empty()`           |
| `x::y`   | Range from x to y (inclusive)   | `trunk()::@`         |
| `x..y`   | Range from x to y (x exclusive) | `trunk()..@`         |
| `x-`     | Parents of x                    | `@-`                 |
| `x+`     | Children of x                   | `trunk()+`           |

#### Practical Examples

```bash
# Process only the current commit
jj-aidesc -r '@'

# Process last 3 commits
jj-aidesc -r '@---::@'

# Process commits since branching from trunk
jj-aidesc -r 'trunk()..@'

# Process only your commits in mutable range
jj-aidesc -r 'mutable() & mine()'

# Process a specific commit by change ID
jj-aidesc -r 'kkmpvwqx'

# Process all commits except working copy
jj-aidesc -r 'mutable() & ~@'
```

> **Note**: `jj-aidesc` filters the revset to only include commits that:
>
> - Have no description (`description(exact:"")`) by default
> - Have changes (not `empty()`)
>
> So you don't need to specify these conditions manually.
