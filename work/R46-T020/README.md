# Task R46-T020: Realistic Usage Example for Phalcon.gitignore

## Focus Patterns
- `/cache/`
- `/config/development/`

## Realistic Project Tree Structure

In a Phalcon PHP MVC application, the project repository contains tracked application source code, base configuration, and public entrypoints, while local caching systems and developer-specific environment overrides are ignored:

```text
my-phalcon-app/
├── app/
│   ├── controllers/
│   │   └── IndexController.php          [TRACKED INPUT  - Application controller]
│   ├── models/
│   │   └── Users.php                    [TRACKED INPUT  - Database entity model]
│   └── views/
│       └── index.volt                   [TRACKED INPUT  - Volt template view]
├── cache/                               [IGNORED OUTPUT - line 2: /cache/]
│   ├── volt/
│   │   └── %%view%%.php                 [IGNORED OUTPUT - line 2: /cache/ (compiled template)]
│   └── data/
│       └── models_metadata.php          [IGNORED OUTPUT - line 2: /cache/ (schema cache)]
├── config/
│   ├── config.php                       [TRACKED INPUT  - Base framework config]
│   ├── production/
│   │   └── config.json                  [TRACKED INPUT  - Production baseline config]
│   └── development/                     [IGNORED OUTPUT - line 4: /config/development/]
│       ├── config.json                  [IGNORED OUTPUT - line 4: /config/development/ (local DB)]
│       └── database.php                 [IGNORED OUTPUT - line 4: /config/development/ (local secret)]
└── public/
    ├── index.php                        [TRACKED INPUT  - Front controller bootstrap]
    └── assets/
        └── cache/
            └── logo.min.css             [TRACKED INPUT  - Web asset preserved; not ignored]
```

## Pattern Analysis & Root Anchoring

1. `/cache/` (Line 2):
   - **Anchored**: The leading slash `/` restricts matching strictly to the root `cache/` directory.
   - **Directory restricted**: The trailing slash `/` matches only directories, leaving regular files named `cache` visible.
   - Preserves public web asset caching directories located at subpaths such as `public/assets/cache/`.

2. `/config/development/` (Line 4):
   - **Anchored**: Prevents accidental tracking of developer machine-specific database credentials and debug toggles in `/config/development/`.
   - Leaves standard configuration files like `config/config.php` and production settings in `config/production/` visible and tracked.

## Fixture Verification

### Ignored Outputs
- `cache/volt/compiled_view.php`: Volt template compiled PHP output (matches `/cache/` on line 2).
- `cache/data/models_metadata.php`: Phalcon ORM schema metadata cache (matches `/cache/` on line 2).
- `config/development/config.json`: Local development configuration override (matches `/config/development/` on line 4).
- `config/development/database.php`: Local database credentials (matches `/config/development/` on line 4).

### Tracked Inputs & Preserved Files
- `app/controllers/IndexController.php`: MVC source code.
- `app/views/index.volt`: Template source.
- `config/config.php`: Base configuration.
- `config/production/config.json`: Production configuration.
- `public/index.php`: Public front controller.
- `public/assets/cache/logo.min.css`: Preserved public web assets (not matched because `/cache/` is anchored).
- `config/development_notes.txt`: Regular file near-miss (not matched by `/config/development/`).

## Tracked Files Behavior
Files committed before ignore patterns are applied remain tracked by Git. Modifications are reported by `git status --porcelain`.

## Automated Verification
Run the verification check:
```bash
python3 work/R46-T020/check.py
```
To verify non-zero exit on failure:
```bash
R46_T020_FORCE_FAIL=1 python3 work/R46-T020/check.py
```
