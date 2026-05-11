# Static Analysis Report

Date: 2026-05-09
Scope:
- main.py
- terrain_builder.py

Tools:
- ruff 0.15.12
- pylint 4.0.5
- mypy 2.0.0
- bandit 1.9.4
- radon 6.0.1

## 1) Potential errors / correctness

### main.py
- pylint E1123/E1120: unexpected keyword args in call to generate_terrain_grid and missing required args.
  - Location: main.py:123
  - Details:
    - unexpected keyword arg: t_water
    - unexpected keyword arg: t_sand
    - unexpected keyword arg: t_grass
    - unexpected keyword arg: t_forest
    - unexpected keyword arg: t_mount
    - missing required args: water_threshold, sand_threshold, grass_threshold, forest_threshold, mountain_threshold
  - This suggests a mismatch between the expected parameters in main.py and the actual signature of generate_terrain_grid in terrain_builder.py.

## 2) Interface / type contract warnings

### main.py
- pylint W0221: overriding methods with different parameter counts
  - Clover.update_needs vs Agent.update_needs (main.py:767)
  - Clover.act vs Agent.act (main.py:839)

## 3) Security notes (bandit)

### main.py
- B311: use of random for non-crypto randomness (low severity). Locations:
  - main.py:122, 257, 265, 267, 307, 308, 309, 311, 312, 314, 315, 317, 318, 434, 596

### terrain_builder.py
- B311: use of random for non-crypto randomness (low severity). Locations:
  - terrain_builder.py:205, 215

## 4) Performance / complexity hotspots (radon)

### main.py (cc)
- C (13): Terrain._compute_water_distance (line 138)
- B (9): SimThread._send_payload (line 989)
- B (8): Agent.get_priority (line 328)
- B (8): Predator.get_priority (line 684)
- B (7): Agent.get_closest_target (line 469)
- B (7): Prey._special_interrupt (line 604)
- B (6): Agent.act (line 540)
- B (6): Clover._update_plant_needs (line 770)
- B (6): Clover._count_neighbors (line 800)
- B (6): Clover.act (line 839)

### terrain_builder.py (cc)
- B (6): TerrainThresholds.classify (line 25)
- A (5): TerrainThresholds (class)
- A (5): TerrainBuilder.generate_terrain (line 208)
- A (3): _build_noise_grid (line 39)
- A (3): generate_terrain_grid (line 61)

### Maintainability index (radon mi)
- main.py: C (0.00)
- terrain_builder.py: A (39.11)

## 5) Style / maintainability findings

### ruff
- main.py: E701 multiple statements on one line at lines 209, 908, 1251
- terrain_builder.py: no findings (ruff checks passed)

### pylint (selected findings, full list below)

#### main.py
- C0302: too many lines in module (1481/1000)
- C0114/C0115/C0116: missing module/class/method docstrings (many locations)
- C0301: line too long (multiple lines)
- C0325: unnecessary parens after '=' (line 1403)
- R0902: too many instance attributes (classes at lines 82, 230, 735, 869, 1029)
- R0913/R0917: too many arguments (various methods, see full list)
- W1514: open() without explicit encoding (line 116)
- W0212: protected-access (_apply_reproduction_cost) (line 413)
- W0613: unused arguments in Agent._special_interrupt (line 574)
- W0201: attributes defined outside __init__ (several in App)
- C0103: AgentClass argument name not snake_case (line 918)

#### terrain_builder.py
- C0114/C0115/C0116: missing module/class/method docstrings (various)
- C0303: trailing whitespace (lines 98, 100, 119, 128, 151, 164, 177, 190, 198, 266, 269)
- C0301: line too long (lines 166, 171, 179, 184, 192, 199, 200, 201, 260)
- R0913/R0917: too many arguments (TerrainThresholds.normalized, generate_terrain_grid)
- R0914: too many local variables in generate_terrain_grid (line 61)
- R0915: too many statements in TerrainBuilder._build_ui (line 116)
- R0902: too many instance attributes in TerrainBuilder (line 103)
- W1514: open() without explicit encoding (line 280)

## 6) Full pylint list (verbatim)

### main.py
- C0301: line too long (85, 87, 89, 91, 93, 95, 441, 515, 870, 1096, 1099, 1143, 1285, 1412, 1413, 1414, 1415, 1416, 1417, 1476)
- C0325: unnecessary parens after '=' (1403)
- C0302: too many lines in module (1)
- C0114: missing module docstring (1)
- C0115: missing class docstring (51, 58, 65, 82, 200, 230, 581, 667, 735, 869, 1013, 1029)
- R0902: too many instance attributes (82, 230, 735, 869, 1029)
- W1514: open without encoding (116)
- E1123/E1120: generate_terrain_grid arg mismatch (123)
- C0116: missing function/method docstring (178, 187, 191, 195, 205, 208, 216, 271, 274, 302, 328, 367, 418, 433, 441, 445, 469, 540, 890, 894, 897, 901, 1022, 1025, 1199, 1250, 1260)
- C0321: multiple statements on one line (209, 908, 1251)
- R0913/R0917: too many args (246, 515, 540, 593, 679, 870, 1368, 1423, 1447)
- W0212: protected-access (413)
- W0613: unused-argument (574)
- W0221: arguments-differ (767, 839)
- C0103: invalid-name AgentClass (918)
- R0902: too many instance attributes (repeated above)
- W0201: attribute-defined-outside-init (1062, 1070, 1077, 1093, 1096, 1099, 1105, 1110, 1115, 1133, 1134, 1135, 1137, 1138, 1139, 1141, 1143, 1155, 1156)
- C0104: disallowed name bar (1085)

### terrain_builder.py
- C0303: trailing whitespace (98, 100, 119, 128, 151, 164, 177, 190, 198, 266, 269)
- C0301: line too long (166, 171, 179, 184, 192, 199, 200, 201, 260)
- C0114: missing module docstring (1)
- C0115: missing class docstring (10, 103)
- C0116: missing function/method docstring (18, 25, 61, 203, 208, 262)
- R0913/R0917: too many arguments (18, 61)
- R0914: too many locals (61)
- R0902: too many instance attributes (103)
- R0915: too many statements (116)
- W1514: open without encoding (280)

## 7) Notes / suggested follow-ups
- Align generate_terrain_grid call in main.py with its actual signature in terrain_builder.py (threshold argument names).
- Decide whether to keep implicit Optional or update type hints and defaults for terrain_file.
- Consider splitting main.py into modules to reduce file size and improve maintainability.
- If non-crypto randomness is fine, suppress bandit B311 for these locations.

ruff check "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; ruff check "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"; pylint "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; pylint "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"; mypy "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py" "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"; bandit -q -r "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; bandit -q -r "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"; radon cc -s -a "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; radon cc -s -a "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"; radon mi -s "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; radon mi -s "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"
