# R46-T029 — Global/NetBeans.gitignore

**Task ID**: R46-T029 | **Issue**: #29 | **Student**: E26B07F0687

## Focus Patterns
| Pattern | Purpose |
|---------|---------|
| `**/nbproject/private/` | Ignore IDE private settings at **any** directory depth |
| `**/nbproject/Makefile-*.mk` | Ignore auto-generated build makefiles; plain `Makefile.mk` kept |
| `**/nbproject/Package-*.bash` | Ignore auto-generated packaging scripts; custom `.bash` files kept |

## Why These Exact Patterns?

### `**/nbproject/private/` vs Alternatives
- **Too broad**: `**/nbproject/` → would hide `project.xml` and other shared metadata
- **Too narrow**: `nbproject/private/` (no `**`) → misses nested sub-projects at depth > 1
- **Just right**: `**/nbproject/private/` matches the private directory at any depth without touching shared files

### `**/nbproject/Makefile-*.mk` vs Alternatives
- **Too broad**: `**/nbproject/*.mk` → catches hand-edited `.mk` files
- **Too narrow**: `**/nbproject/Makefile.mk` → misses `Makefile-Debug.mk`, `Makefile-Release.mk`

### `**/nbproject/Package-*.bash` vs Alternatives
- **Too broad**: `**/nbproject/*.bash` → catches custom user scripts
- **Too narrow**: `**/nbproject/Package.bash` → misses `Package-Debug.bash`, `Package-Release.bash`

## Results
| Check | Status |
|-------|--------|
| Total checks | 16 |
| Passed | 16 |
| Failed | 0 |

See `evidence.json` for full structured output.
