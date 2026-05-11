(.venv) PS C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6> ruff check "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; pylint "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; mypy "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; bandit -q -r "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; radon cc -s -a "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; radon mi -s "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"
E701 Multiple statements on one line (colon)
--> main.py:209:27
|
208 |     def insert(self, agent):
209 |         if not agent.alive: return
|                           ^
210 |         cx = int(agent.x / self.cell_size)
211 |         cy = int(agent.y / self.cell_size)
|

E701 Multiple statements on one line (colon)
--> main.py:908:33
|
906 |         while self._running:
907 |             self._paused.wait()
908 |             if not self._running: break
|                                 ^
909 |             self._step()
910 |             self._send_payload()
|

E701 Multiple statements on one line (colon)
--> main.py:1251:28
|
1250 |     def toggle_pause(self):
1251 |         if self.sim is None: return
|                            ^
1252 |         if self.sim.is_paused:
1253 |             self.sim.resume()
|

Found 3 errors.
************* Module main
main.py:85:0: C0301: Line too long (106/100) (line-too-long)
main.py:87:0: C0301: Line too long (105/100) (line-too-long)
main.py:89:0: C0301: Line too long (105/100) (line-too-long)
main.py:91:0: C0301: Line too long (105/100) (line-too-long)
main.py:93:0: C0301: Line too long (105/100) (line-too-long)
main.py:95:0: C0301: Line too long (106/100) (line-too-long)
main.py:441:0: C0301: Line too long (103/100) (line-too-long)
main.py:515:0: C0301: Line too long (117/100) (line-too-long)
main.py:870:0: C0301: Line too long (105/100) (line-too-long)
main.py:1096:0: C0301: Line too long (112/100) (line-too-long)
main.py:1099:0: C0301: Line too long (103/100) (line-too-long)
main.py:1143:0: C0301: Line too long (118/100) (line-too-long)
main.py:1285:0: C0301: Line too long (106/100) (line-too-long)
main.py:1403:0: C0325: Unnecessary parens after '=' keyword (superfluous-parens)
main.py:1412:0: C0301: Line too long (118/100) (line-too-long)
main.py:1413:0: C0301: Line too long (107/100) (line-too-long)
main.py:1414:0: C0301: Line too long (110/100) (line-too-long)
main.py:1415:0: C0301: Line too long (107/100) (line-too-long)
main.py:1416:0: C0301: Line too long (110/100) (line-too-long)
main.py:1417:0: C0301: Line too long (105/100) (line-too-long)
main.py:1476:0: C0301: Line too long (144/100) (line-too-long)
main.py:1:0: C0302: Too many lines in module (1481/1000) (too-many-lines)
main.py:1:0: C0114: Missing module docstring (missing-module-docstring)
main.py:51:0: C0115: Missing class docstring (missing-class-docstring)
main.py:58:0: C0115: Missing class docstring (missing-class-docstring)
main.py:65:0: C0115: Missing class docstring (missing-class-docstring)
main.py:82:0: C0115: Missing class docstring (missing-class-docstring)
main.py:82:0: R0902: Too many instance attributes (8/7) (too-many-instance-attributes)
main.py:116:13: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)
main.py:123:19: E1123: Unexpected keyword argument 't_water' in function call (unexpected-keyword-arg)
main.py:123:19: E1123: Unexpected keyword argument 't_sand' in function call (unexpected-keyword-arg)
main.py:123:19: E1123: Unexpected keyword argument 't_grass' in function call (unexpected-keyword-arg)
main.py:123:19: E1123: Unexpected keyword argument 't_forest' in function call (unexpected-keyword-arg)
main.py:123:19: E1123: Unexpected keyword argument 't_mount' in function call (unexpected-keyword-arg)
main.py:123:19: E1120: No value for argument 'water_threshold' in function call (no-value-for-parameter)
main.py:123:19: E1120: No value for argument 'sand_threshold' in function call (no-value-for-parameter)
main.py:123:19: E1120: No value for argument 'grass_threshold' in function call (no-value-for-parameter)
main.py:123:19: E1120: No value for argument 'forest_threshold' in function call (no-value-for-parameter)
main.py:123:19: E1120: No value for argument 'mountain_threshold' in function call (no-value-for-parameter)
main.py:178:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:187:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:191:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:195:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:200:0: C0115: Missing class docstring (missing-class-docstring)
main.py:205:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:208:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:209:28: C0321: More than one statement on a single line (multiple-statements)
main.py:216:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:230:0: C0115: Missing class docstring (missing-class-docstring)
main.py:230:0: R0902: Too many instance attributes (16/7) (too-many-instance-attributes)
main.py:246:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:246:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:271:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:274:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:302:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:328:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:367:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:413:8: W0212: Access to a protected member _apply_reproduction_cost of a client class (protected-access)
main.py:418:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:433:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:441:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:445:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:469:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:515:4: R0913: Too many arguments (7/5) (too-many-arguments)
main.py:515:4: R0917: Too many positional arguments (7/5) (too-many-positional-arguments)
main.py:540:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:540:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:540:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:574:33: W0613: Unused argument 'entities' (unused-argument)
main.py:574:43: W0613: Unused argument 'sense_sq' (unused-argument)
main.py:574:53: W0613: Unused argument 'terrain' (unused-argument)
main.py:581:0: C0115: Missing class docstring (missing-class-docstring)
main.py:593:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:593:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:667:0: C0115: Missing class docstring (missing-class-docstring)
main.py:679:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:679:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:735:0: C0115: Missing class docstring (missing-class-docstring)
main.py:735:0: R0902: Too many instance attributes (9/7) (too-many-instance-attributes)
main.py:767:4: W0221: Number of parameters was 2 in 'Agent.update_needs' and is now 1 in overriding 'Clover.update_needs' method (arguments-differ)
main.py:839:4: W0221: Number of parameters was 6 in 'Agent.act' and is now 5 in overriding 'Clover.act' method (arguments-differ)
main.py:869:0: C0115: Missing class docstring (missing-class-docstring)
main.py:869:0: R0902: Too many instance attributes (13/7) (too-many-instance-attributes)
main.py:870:4: R0913: Too many arguments (8/5) (too-many-arguments)
main.py:870:4: R0917: Too many positional arguments (8/5) (too-many-positional-arguments)
main.py:890:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:894:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:897:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:901:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:908:34: C0321: More than one statement on a single line (multiple-statements)
main.py:918:32: C0103: Argument name "AgentClass" doesn't conform to snake_case naming style (invalid-name)
main.py:1013:0: C0115: Missing class docstring (missing-class-docstring)
main.py:1022:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1025:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1029:0: C0115: Missing class docstring (missing-class-docstring)
main.py:1029:0: R0902: Too many instance attributes (29/7) (too-many-instance-attributes)
main.py:1085:8: C0104: Disallowed name "bar" (disallowed-name)
main.py:1199:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1250:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1251:29: C0321: More than one statement on a single line (multiple-statements)
main.py:1260:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1368:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:1368:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:1423:4: R0913: Too many arguments (9/5) (too-many-arguments)
main.py:1423:4: R0917: Too many positional arguments (9/5) (too-many-positional-arguments)
main.py:1447:4: R0913: Too many arguments (10/5) (too-many-arguments)
main.py:1447:4: R0917: Too many positional arguments (10/5) (too-many-positional-arguments)
main.py:1062:8: W0201: Attribute 'sim_canvas' defined outside __init__ (attribute-defined-outside-init)
main.py:1070:8: W0201: Attribute 'ctrl' defined outside __init__ (attribute-defined-outside-init)
main.py:1077:8: W0201: Attribute 'lbl_info' defined outside __init__ (attribute-defined-outside-init)
main.py:1093:8: W0201: Attribute 'btn_start' defined outside __init__ (attribute-defined-outside-init)
main.py:1096:8: W0201: Attribute 'btn_pause' defined outside __init__ (attribute-defined-outside-init)
main.py:1099:8: W0201: Attribute 'btn_restart' defined outside __init__ (attribute-defined-outside-init)
main.py:1105:8: W0201: Attribute 'entry_simulation_delay' defined outside __init__ (attribute-defined-outside-init)
main.py:1110:8: W0201: Attribute 'entry_ui_refresh_ms' defined outside __init__ (attribute-defined-outside-init)
main.py:1115:8: W0201: Attribute 'show_debug_overlay' defined outside __init__ (attribute-defined-outside-init)
main.py:1133:8: W0201: Attribute 'input_prey_count' defined outside __init__ (attribute-defined-outside-init)
main.py:1134:8: W0201: Attribute 'input_predator_count' defined outside __init__ (attribute-defined-outside-init)
main.py:1135:8: W0201: Attribute 'input_clover_capacity' defined outside __init__ (attribute-defined-outside-init)
main.py:1137:8: W0201: Attribute 'input_initial_speed' defined outside __init__ (attribute-defined-outside-init)
main.py:1138:8: W0201: Attribute 'input_initial_size' defined outside __init__ (attribute-defined-outside-init)
main.py:1139:8: W0201: Attribute 'input_initial_sense' defined outside __init__ (attribute-defined-outside-init)
main.py:1141:8: W0201: Attribute 'input_mutation_probability' defined outside __init__ (attribute-defined-outside-init)
main.py:1143:8: W0201: Attribute 'input_mutation_strength' defined outside __init__ (attribute-defined-outside-init)
main.py:1155:8: W0201: Attribute 'selected_terrain_name' defined outside __init__ (attribute-defined-outside-init)
main.py:1156:8: W0201: Attribute 'terrain_option_menu' defined outside __init__ (attribute-defined-outside-init)

-----------------------------------
Your code has been rated at 8.33/10

terrain_builder.py:6: error: Skipping analyzing "noise": module is installed, but missing library stubs or py.typed marker  [import-untyped]
terrain_builder.py:6: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
main.py:871: error: Incompatible default for parameter "terrain_file" (default has type "None", parameter has type "str")  [assignment]
main.py:871: note: PEP 484 prohibits implicit Optional. Accordingly, mypy has changed its default to no_implicit_optional=True
main.py:871: note: Use https://github.com/hauntsaninja/no_implicit_optional to automatically upgrade your codebase
Found 2 errors in 2 files (checked 1 source file)
Run started:2026-05-09 15:38:42.238812+00:00

Test results:
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:122:15
121         def _generate_random_grid(self):
122             seed = random.randint(0, 999999)
123             raw_grid = generate_terrain_grid(

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:257:23
256             self.age = 0
257             self.max_age = random.randint(3000, 5000)
258

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:265:19
264             self.color = COLOR_AGENT
265             self.sex = random.choice(["M", "F"])
266

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:267:28
266     
267             self.wander_angle = random.uniform(0, 2 * math.pi)
268             self.current_action = Action.WANDER

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:307:23
306     
307             child_speed *= random.uniform(0.9, 1.1)
308             child_size *= random.uniform(0.9, 1.1)

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:308:22
307             child_speed *= random.uniform(0.9, 1.1)
308             child_size *= random.uniform(0.9, 1.1)
309             child_sense *= random.uniform(0.9, 1.1)

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:309:23
308             child_size *= random.uniform(0.9, 1.1)
309             child_sense *= random.uniform(0.9, 1.1)
310

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:311:11
310     
311             if random.random() < mutation_probability:
312                 child_speed *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:312:27
311             if random.random() < mutation_probability:
312                 child_speed *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])
313

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:314:11
313     
314             if random.random() < mutation_probability:
315                 child_size *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:315:26
314             if random.random() < mutation_probability:
315                 child_size *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])
316

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:317:11
316     
317             if random.random() < mutation_probability:
318                 child_sense *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:318:27
317             if random.random() < mutation_probability:
318                 child_sense *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])
319

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:434:29
433         def wander(self, terrain):
434             self.wander_angle += random.uniform(-0.3, 0.3)
435

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:596:23
595             self.color = COLOR_AGENT_PREY
596             self.max_age = random.randint(3000, 5000)
597

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:599:22
598         de
C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py
M 138:4 Terrain._compute_water_distance - C (13)
M 989:4 SimThread._send_payload - B (9)
M 328:4 Agent.get_priority - B (8)
M 684:4 Predator.get_priority - B (8)
M 469:4 Agent.get_closest_target - B (7)
M 604:4 Prey._special_interrupt - B (7)
M 540:4 Agent.act - B (6)
M 770:4 Clover._update_plant_needs - B (6)
M 800:4 Clover._count_neighbors - B (6)
M 839:4 Clover.act - B (6)
M 274:4 Agent.update_needs - A (5)
M 346:4 Agent._clamp_bounds - A (5)
M 367:4 Agent.move_step - A (5)
M 391:4 Agent._can_reproduce_with - A (5)
C 667:0 Predator - A (5)
C 735:0 Clover - A (5)
M 822:4 Clover._attempt_spawn - A (5)
M 1340:4 App._draw_terrain_if_needed - A (5)
C 82:0 Terrain - A (4)
M 216:4 SpatialGrid.get_nearby - A (4)
C 230:0 Agent - A (4)
M 302:4 Agent.mix_genes - A (4)
M 445:4 Agent.try_drink_from_nearest_water - A (4)
C 581:0 Prey - A (4)
M 645:4 Prey._handle_hunger - A (4)
M 702:4 Predator._handle_hunger - A (4)
M 932:4 SimThread._spawn - A (4)
M 949:4 SimThread._step - A (4)
M 1394:4 App._update_agent_graphic - A (4)
M 1457:4 App._cleanup_dead_agents - A (4)
M 109:4 Terrain._load_or_generate_grid - A (3)
M 115:4 Terrain._load_grid_from_file - A (3)
M 121:4 Terrain._generate_random_grid - A (3)
C 200:0 SpatialGrid - A (3)
M 208:4 SpatialGrid.insert - A (3)
M 501:4 Agent._handle_thirst - A (3)
M 515:4 Agent._handle_reproduction - A (3)
C 869:0 SimThread - A (3)
M 904:4 SimThread.run - A (3)
M 918:4 SimThread._spawn_agent_safe - A (3)
M 972:4 SimThread._process_single_agent - A (3)
M 1186:4 App._update_parameter_entry_states - A (3)
M 1250:4 App.toggle_pause - A (3)
M 1273:4 App._clear_queue - A (3)
M 1287:4 App._poll_queue - A (3)
M 1354:4 App._draw_terrain_row - A (3)
M 1380:4 App._draw_agents - A (3)
M 1462:4 App._remove_agent_graphics - A (3)
M 418:4 Agent.move_towards - A (2)
M 598:4 Prey._spawn_offspring - A (2)
M 744:4 Clover.__init__ - A (2)
M 913:4 SimThread._get_speed - A (2)
M 961:4 SimThread._rebuild_spatial_grid - A (2)
M 966:4 SimThread._process_agents_for_tick - A (2)
C 1013:0 ParameterEntry - A (2)
C 1029:0 App - A (2)
M 1175:4 App._update_button_states - A (2)
M 1199:4 App.start - A (2)
M 1223:4 App._parse_start_inputs - A (2)
M 1240:4 App._get_selected_terrain - A (2)
M 1244:4 App._read_simulation_delay - A (2)
M 1267:4 App._stop_simulation - A (2)
M 1299:4 App._drain_queue_latest - A (2)
M 1305:4 App._try_get_queue_item - A (2)
M 1311:4 App._read_refresh_interval_ms - A (2)
M 1317:4 App._read_runtime_simulation_delay - A (2)
M 1328:4 App._update_sim_runtime_speed - A (2)
M 1423:4 App._show_agent_debug - A (2)
M 1437:4 App._hide_agent_debug - A (2)
M 1443:4 App._set_debug_visibility - A (2)
C 51:0 EntityType - A (1)
C 58:0 Priority - A (1)
C 65:0 Action - A (1)
M 99:4 Terrain.__init__ - A (1)
M 178:4 Terrain.get_cell_coords - A (1)
M 187:4 Terrain.get_type_at - A (1)
M 191:4 Terrain.get_terrain_props_at - A (1)
M 195:4 Terrain.get_water_distance_at - A (1)
M 201:4 SpatialGrid.__init__ - A (1)
M 205:4 SpatialGrid.clear - A (1)
M 246:4 Agent.__init__ - A (1)
M 271:4 Agent.radius - A (1)
M 406:4 Agent._apply_reproduction_cost - A (1)
M 411:4 Agent._apply_reproduction_to_pair - A (1)
M 415:4 Agent._find_reproduction_partner - A (1)
M 433:4 Agent.wander - A (1)
M 441:4 Agent.is_in_interaction_range - A (1)
M 537:4 Agent._spawn_offspring - A (1)
M 574:4 Agent._special_interrupt - A (1)
M 577:4 Agent._handle_hunger - A (1)
M 593:4 Prey.__init__ - A (1)
M 679:4 Predator.__init__ - A (1)
M 764:4 Clover.radius - A (1)
M 767:4 Clover.update_needs - A (1)
M 870:4 SimThread.__init__ - A (1)
M 890:4 SimThread.stop - A (1)
M 894:4 SimThread.pause - A (1)
M 897:4 SimThread.resume - A (1)
M 901:4 SimThread.is_paused - A (1)
M 928:4 SimThread._spawn_clover - A (1)
M 1014:4 ParameterEntry.__init__ - A (1)
M 1022:4 ParameterEntry.get - A (1)
M 1025:4 ParameterEntry.set_state - A (1)
M 1031:4 App.__init__ - A (1)
M 1050:4 App._build_ui - A (1)
M 1058:4 App._create_canvas_area - A (1)
M 1069:4 App._create_control_panel - A (1)
M 1076:4 App._create_info_label - A (1)
M 1084:4 App._build_buttons - A (1)
M 1092:4 App._add_simulation_action_buttons - A (1)
M 1103:4 App._add_speed_control_inputs - A (1)
M 1114:4 App._add_debug_toggle - A (1)
M 1122:4 App._build_settings - A (1)
M 1129:4 App._add_agent_settings_row - A (1)
M 1146:4 App._add_terrain_settings_row - A (1)
M 1159:4 App._on_drag_start - A (1)
M 1163:4 App._on_drag_motion - A (1)
M 1171:4 App._set_ui_state - A (1)
M 1196:4 App._set_ui_running - A (1)
M 1260:4 App.restart - A (1)
M 1280:4 App._reset_ui_simulation_view - A (1)
M 1323:4 App._process_payload - A (1)
M 1333:4 App._draw_sim - A (1)
M 1368:4 App._create_terrain_rect - A (1)
M 1376:4 App._update_canvas_panning - A (1)
M 1410:4 App._create_agent_graphics_item - A (1)
M 1447:4 App._update_status_bar - A (1)
M 1468:4 App._update_info - A (1)

128 blocks (classes, functions, methods) analyzed.
Average complexity: A (2.5)
C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py - C (0.00)
(.venv) PS C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6> ruff check "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; ruff check "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"; pylint "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; pylint "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"; mypy "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py" "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"; bandit -q -r "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; bandit -q -r "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"; radon cc -s -a "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; radon cc -s -a "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"; radon mi -s "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py"; radon mi -s "C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py"
E701 Multiple statements on one line (colon)
--> main.py:209:27
|
208 |     def insert(self, agent):
209 |         if not agent.alive: return
|                           ^
210 |         cx = int(agent.x / self.cell_size)
211 |         cy = int(agent.y / self.cell_size)
|

E701 Multiple statements on one line (colon)
--> main.py:908:33
|
906 |         while self._running:
907 |             self._paused.wait()
908 |             if not self._running: break
|                                 ^
909 |             self._step()
910 |             self._send_payload()
|

E701 Multiple statements on one line (colon)
--> main.py:1251:28
|
1250 |     def toggle_pause(self):
1251 |         if self.sim is None: return
|                            ^
1252 |         if self.sim.is_paused:
1253 |             self.sim.resume()
|

Found 3 errors.
All checks passed!
************* Module main
main.py:85:0: C0301: Line too long (106/100) (line-too-long)
main.py:87:0: C0301: Line too long (105/100) (line-too-long)
main.py:89:0: C0301: Line too long (105/100) (line-too-long)
main.py:91:0: C0301: Line too long (105/100) (line-too-long)
main.py:93:0: C0301: Line too long (105/100) (line-too-long)
main.py:95:0: C0301: Line too long (106/100) (line-too-long)
main.py:441:0: C0301: Line too long (103/100) (line-too-long)
main.py:515:0: C0301: Line too long (117/100) (line-too-long)
main.py:870:0: C0301: Line too long (105/100) (line-too-long)
main.py:1096:0: C0301: Line too long (112/100) (line-too-long)
main.py:1099:0: C0301: Line too long (103/100) (line-too-long)
main.py:1143:0: C0301: Line too long (118/100) (line-too-long)
main.py:1285:0: C0301: Line too long (106/100) (line-too-long)
main.py:1403:0: C0325: Unnecessary parens after '=' keyword (superfluous-parens)
main.py:1412:0: C0301: Line too long (118/100) (line-too-long)
main.py:1413:0: C0301: Line too long (107/100) (line-too-long)
main.py:1414:0: C0301: Line too long (110/100) (line-too-long)
main.py:1415:0: C0301: Line too long (107/100) (line-too-long)
main.py:1416:0: C0301: Line too long (110/100) (line-too-long)
main.py:1417:0: C0301: Line too long (105/100) (line-too-long)
main.py:1476:0: C0301: Line too long (144/100) (line-too-long)
main.py:1:0: C0302: Too many lines in module (1481/1000) (too-many-lines)
main.py:1:0: C0114: Missing module docstring (missing-module-docstring)
main.py:51:0: C0115: Missing class docstring (missing-class-docstring)
main.py:58:0: C0115: Missing class docstring (missing-class-docstring)
main.py:65:0: C0115: Missing class docstring (missing-class-docstring)
main.py:82:0: C0115: Missing class docstring (missing-class-docstring)
main.py:82:0: R0902: Too many instance attributes (8/7) (too-many-instance-attributes)
main.py:116:13: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)
main.py:123:19: E1123: Unexpected keyword argument 't_water' in function call (unexpected-keyword-arg)
main.py:123:19: E1123: Unexpected keyword argument 't_sand' in function call (unexpected-keyword-arg)
main.py:123:19: E1123: Unexpected keyword argument 't_grass' in function call (unexpected-keyword-arg)
main.py:123:19: E1123: Unexpected keyword argument 't_forest' in function call (unexpected-keyword-arg)
main.py:123:19: E1123: Unexpected keyword argument 't_mount' in function call (unexpected-keyword-arg)
main.py:123:19: E1120: No value for argument 'water_threshold' in function call (no-value-for-parameter)
main.py:123:19: E1120: No value for argument 'sand_threshold' in function call (no-value-for-parameter)
main.py:123:19: E1120: No value for argument 'grass_threshold' in function call (no-value-for-parameter)
main.py:123:19: E1120: No value for argument 'forest_threshold' in function call (no-value-for-parameter)
main.py:123:19: E1120: No value for argument 'mountain_threshold' in function call (no-value-for-parameter)
main.py:178:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:187:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:191:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:195:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:200:0: C0115: Missing class docstring (missing-class-docstring)
main.py:205:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:208:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:209:28: C0321: More than one statement on a single line (multiple-statements)
main.py:216:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:230:0: C0115: Missing class docstring (missing-class-docstring)
main.py:230:0: R0902: Too many instance attributes (16/7) (too-many-instance-attributes)
main.py:246:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:246:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:271:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:274:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:302:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:328:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:367:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:413:8: W0212: Access to a protected member _apply_reproduction_cost of a client class (protected-access)
main.py:418:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:433:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:441:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:445:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:469:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:515:4: R0913: Too many arguments (7/5) (too-many-arguments)
main.py:515:4: R0917: Too many positional arguments (7/5) (too-many-positional-arguments)
main.py:540:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:540:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:540:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:574:33: W0613: Unused argument 'entities' (unused-argument)
main.py:574:43: W0613: Unused argument 'sense_sq' (unused-argument)
main.py:574:53: W0613: Unused argument 'terrain' (unused-argument)
main.py:581:0: C0115: Missing class docstring (missing-class-docstring)
main.py:593:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:593:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:667:0: C0115: Missing class docstring (missing-class-docstring)
main.py:679:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:679:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:735:0: C0115: Missing class docstring (missing-class-docstring)
main.py:735:0: R0902: Too many instance attributes (9/7) (too-many-instance-attributes)
main.py:767:4: W0221: Number of parameters was 2 in 'Agent.update_needs' and is now 1 in overriding 'Clover.update_needs' method (arguments-differ)
main.py:839:4: W0221: Number of parameters was 6 in 'Agent.act' and is now 5 in overriding 'Clover.act' method (arguments-differ)
main.py:869:0: C0115: Missing class docstring (missing-class-docstring)
main.py:869:0: R0902: Too many instance attributes (13/7) (too-many-instance-attributes)
main.py:870:4: R0913: Too many arguments (8/5) (too-many-arguments)
main.py:870:4: R0917: Too many positional arguments (8/5) (too-many-positional-arguments)
main.py:890:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:894:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:897:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:901:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:908:34: C0321: More than one statement on a single line (multiple-statements)
main.py:918:32: C0103: Argument name "AgentClass" doesn't conform to snake_case naming style (invalid-name)
main.py:1013:0: C0115: Missing class docstring (missing-class-docstring)
main.py:1022:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1025:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1029:0: C0115: Missing class docstring (missing-class-docstring)
main.py:1029:0: R0902: Too many instance attributes (29/7) (too-many-instance-attributes)
main.py:1085:8: C0104: Disallowed name "bar" (disallowed-name)
main.py:1199:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1250:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1251:29: C0321: More than one statement on a single line (multiple-statements)
main.py:1260:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1368:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:1368:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:1423:4: R0913: Too many arguments (9/5) (too-many-arguments)
main.py:1423:4: R0917: Too many positional arguments (9/5) (too-many-positional-arguments)
main.py:1447:4: R0913: Too many arguments (10/5) (too-many-arguments)
main.py:1447:4: R0917: Too many positional arguments (10/5) (too-many-positional-arguments)
main.py:1062:8: W0201: Attribute 'sim_canvas' defined outside __init__ (attribute-defined-outside-init)
main.py:1070:8: W0201: Attribute 'ctrl' defined outside __init__ (attribute-defined-outside-init)
main.py:1077:8: W0201: Attribute 'lbl_info' defined outside __init__ (attribute-defined-outside-init)
main.py:1093:8: W0201: Attribute 'btn_start' defined outside __init__ (attribute-defined-outside-init)
main.py:1096:8: W0201: Attribute 'btn_pause' defined outside __init__ (attribute-defined-outside-init)
main.py:1099:8: W0201: Attribute 'btn_restart' defined outside __init__ (attribute-defined-outside-init)
main.py:1105:8: W0201: Attribute 'entry_simulation_delay' defined outside __init__ (attribute-defined-outside-init)
main.py:1110:8: W0201: Attribute 'entry_ui_refresh_ms' defined outside __init__ (attribute-defined-outside-init)
main.py:1115:8: W0201: Attribute 'show_debug_overlay' defined outside __init__ (attribute-defined-outside-init)
main.py:1133:8: W0201: Attribute 'input_prey_count' defined outside __init__ (attribute-defined-outside-init)
main.py:1134:8: W0201: Attribute 'input_predator_count' defined outside __init__ (attribute-defined-outside-init)
main.py:1135:8: W0201: Attribute 'input_clover_capacity' defined outside __init__ (attribute-defined-outside-init)
main.py:1137:8: W0201: Attribute 'input_initial_speed' defined outside __init__ (attribute-defined-outside-init)
main.py:1138:8: W0201: Attribute 'input_initial_size' defined outside __init__ (attribute-defined-outside-init)
main.py:1139:8: W0201: Attribute 'input_initial_sense' defined outside __init__ (attribute-defined-outside-init)
main.py:1141:8: W0201: Attribute 'input_mutation_probability' defined outside __init__ (attribute-defined-outside-init)
main.py:1143:8: W0201: Attribute 'input_mutation_strength' defined outside __init__ (attribute-defined-outside-init)
main.py:1155:8: W0201: Attribute 'selected_terrain_name' defined outside __init__ (attribute-defined-outside-init)
main.py:1156:8: W0201: Attribute 'terrain_option_menu' defined outside __init__ (attribute-defined-outside-init)

------------------------------------------------------------------
Your code has been rated at 8.33/10 (previous run: 8.33/10, +0.00)

************* Module terrain_builder
terrain_builder.py:98:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:100:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:119:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:128:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:151:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:164:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:166:0: C0301: Line too long (109/100) (line-too-long)
terrain_builder.py:171:0: C0301: Line too long (108/100) (line-too-long)
terrain_builder.py:177:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:179:0: C0301: Line too long (109/100) (line-too-long)
terrain_builder.py:184:0: C0301: Line too long (110/100) (line-too-long)
terrain_builder.py:190:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:192:0: C0301: Line too long (112/100) (line-too-long)
terrain_builder.py:198:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:199:0: C0301: Line too long (124/100) (line-too-long)
terrain_builder.py:200:0: C0301: Line too long (114/100) (line-too-long)
terrain_builder.py:201:0: C0301: Line too long (109/100) (line-too-long)
terrain_builder.py:260:0: C0301: Line too long (114/100) (line-too-long)
terrain_builder.py:266:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:269:49: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:1:0: C0114: Missing module docstring (missing-module-docstring)
terrain_builder.py:10:0: C0115: Missing class docstring (missing-class-docstring)
terrain_builder.py:18:4: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:18:4: R0913: Too many arguments (6/5) (too-many-arguments)
terrain_builder.py:18:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
terrain_builder.py:25:4: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:61:0: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:61:0: R0913: Too many arguments (11/5) (too-many-arguments)
terrain_builder.py:61:0: R0917: Too many positional arguments (11/5) (too-many-positional-arguments)
terrain_builder.py:61:0: R0914: Too many local variables (24/15) (too-many-locals)
terrain_builder.py:103:0: C0115: Missing class docstring (missing-class-docstring)
terrain_builder.py:103:0: R0902: Too many instance attributes (16/7) (too-many-instance-attributes)
terrain_builder.py:116:4: R0915: Too many statements (66/50) (too-many-statements)
terrain_builder.py:203:4: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:208:4: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:262:4: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:280:17: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)

-----------------------------------
Your code has been rated at 7.92/10

terrain_builder.py:6: error: Skipping analyzing "noise": module is installed, but missing library stubs or py.typed marker  [import-untyped]
terrain_builder.py:6: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
main.py:871: error: Incompatible default for parameter "terrain_file" (default has type "None", parameter has type "str")  [assignment]
main.py:871: note: PEP 484 prohibits implicit Optional. Accordingly, mypy has changed its default to no_implicit_optional=True
main.py:871: note: Use https://github.com/hauntsaninja/no_implicit_optional to automatically upgrade your codebase
Found 2 errors in 2 files (checked 2 source files)
Run started:2026-05-09 15:43:17.446309+00:00

Test results:
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:122:15
121         def _generate_random_grid(self):
122             seed = random.randint(0, 999999)
123             raw_grid = generate_terrain_grid(

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:257:23
256             self.age = 0
257             self.max_age = random.randint(3000, 5000)
258

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:265:19
264             self.color = COLOR_AGENT
265             self.sex = random.choice(["M", "F"])
266

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:267:28
266     
267             self.wander_angle = random.uniform(0, 2 * math.pi)
268             self.current_action = Action.WANDER

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:307:23
306     
307             child_speed *= random.uniform(0.9, 1.1)
308             child_size *= random.uniform(0.9, 1.1)

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:308:22
307             child_speed *= random.uniform(0.9, 1.1)
308             child_size *= random.uniform(0.9, 1.1)
309             child_sense *= random.uniform(0.9, 1.1)

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:309:23
308             child_size *= random.uniform(0.9, 1.1)
309             child_sense *= random.uniform(0.9, 1.1)
310

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:311:11
310     
311             if random.random() < mutation_probability:
312                 child_speed *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:312:27
311             if random.random() < mutation_probability:
312                 child_speed *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])
313

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:314:11
313     
314             if random.random() < mutation_probability:
315                 child_size *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:315:26
314             if random.random() < mutation_probability:
315                 child_size *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])
316

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:317:11
316     
317             if random.random() < mutation_probability:
318                 child_sense *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:318:27
317             if random.random() < mutation_probability:
318                 child_sense *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])
319

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:434:29
433         def wander(self, terrain):
434             self.wander_angle += random.uniform(-0.3, 0.3)
435

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:596:23
595             self.color = COLOR_AGENT_PREY
596             self.max_age = random.randint(3000, 5000)
597

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py:599:22
598         de
Run started:2026-05-09 15:43:17.983781+00:00

Test results:
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py:205:38
204             self.entry_seed.delete(0, tk.END)
205             self.entry_seed.insert(0, str(random.randint(0, 999999)))
206             self.generate_terrain()

--------------------------------------------------
>> Issue: [B311:blacklist] Standard pseudo-random generators are not suitable for security/cryptographic purposes.
Severity: Low   Confidence: High
CWE: CWE-330 (https://cwe.mitre.org/data/definitions/330.html)
More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b311-random
Location: C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py:215:23
214                 if seed == -1:
215                     seed = random.randint(0, 999999)
216                 scale = float(self.scale_noise_frequency.get())

--------------------------------------------------

Code scanned:
Total lines of code: 234
Total lines skipped (#nosec): 0

Run metrics:
Total issues (by severity):
Undefined: 0
Low: 2
Medium: 0
High: 0
Total issues (by confidence):
Undefined: 0
Low: 0
Medium: 0
High: 2
Files skipped (0):
C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py
M 138:4 Terrain._compute_water_distance - C (13)
M 989:4 SimThread._send_payload - B (9)
M 328:4 Agent.get_priority - B (8)
M 684:4 Predator.get_priority - B (8)
M 469:4 Agent.get_closest_target - B (7)
M 604:4 Prey._special_interrupt - B (7)
M 540:4 Agent.act - B (6)
M 770:4 Clover._update_plant_needs - B (6)
M 800:4 Clover._count_neighbors - B (6)
M 839:4 Clover.act - B (6)
M 274:4 Agent.update_needs - A (5)
M 346:4 Agent._clamp_bounds - A (5)
M 367:4 Agent.move_step - A (5)
M 391:4 Agent._can_reproduce_with - A (5)
C 667:0 Predator - A (5)
C 735:0 Clover - A (5)
M 822:4 Clover._attempt_spawn - A (5)
M 1340:4 App._draw_terrain_if_needed - A (5)
C 82:0 Terrain - A (4)
M 216:4 SpatialGrid.get_nearby - A (4)
C 230:0 Agent - A (4)
M 302:4 Agent.mix_genes - A (4)
M 445:4 Agent.try_drink_from_nearest_water - A (4)
C 581:0 Prey - A (4)
M 645:4 Prey._handle_hunger - A (4)
M 702:4 Predator._handle_hunger - A (4)
M 932:4 SimThread._spawn - A (4)
M 949:4 SimThread._step - A (4)
M 1394:4 App._update_agent_graphic - A (4)
M 1457:4 App._cleanup_dead_agents - A (4)
M 109:4 Terrain._load_or_generate_grid - A (3)
M 115:4 Terrain._load_grid_from_file - A (3)
M 121:4 Terrain._generate_random_grid - A (3)
C 200:0 SpatialGrid - A (3)
M 208:4 SpatialGrid.insert - A (3)
M 501:4 Agent._handle_thirst - A (3)
M 515:4 Agent._handle_reproduction - A (3)
C 869:0 SimThread - A (3)
M 904:4 SimThread.run - A (3)
M 918:4 SimThread._spawn_agent_safe - A (3)
M 972:4 SimThread._process_single_agent - A (3)
M 1186:4 App._update_parameter_entry_states - A (3)
M 1250:4 App.toggle_pause - A (3)
M 1273:4 App._clear_queue - A (3)
M 1287:4 App._poll_queue - A (3)
M 1354:4 App._draw_terrain_row - A (3)
M 1380:4 App._draw_agents - A (3)
M 1462:4 App._remove_agent_graphics - A (3)
M 418:4 Agent.move_towards - A (2)
M 598:4 Prey._spawn_offspring - A (2)
M 744:4 Clover.__init__ - A (2)
M 913:4 SimThread._get_speed - A (2)
M 961:4 SimThread._rebuild_spatial_grid - A (2)
M 966:4 SimThread._process_agents_for_tick - A (2)
C 1013:0 ParameterEntry - A (2)
C 1029:0 App - A (2)
M 1175:4 App._update_button_states - A (2)
M 1199:4 App.start - A (2)
M 1223:4 App._parse_start_inputs - A (2)
M 1240:4 App._get_selected_terrain - A (2)
M 1244:4 App._read_simulation_delay - A (2)
M 1267:4 App._stop_simulation - A (2)
M 1299:4 App._drain_queue_latest - A (2)
M 1305:4 App._try_get_queue_item - A (2)
M 1311:4 App._read_refresh_interval_ms - A (2)
M 1317:4 App._read_runtime_simulation_delay - A (2)
M 1328:4 App._update_sim_runtime_speed - A (2)
M 1423:4 App._show_agent_debug - A (2)
M 1437:4 App._hide_agent_debug - A (2)
M 1443:4 App._set_debug_visibility - A (2)
C 51:0 EntityType - A (1)
C 58:0 Priority - A (1)
C 65:0 Action - A (1)
M 99:4 Terrain.__init__ - A (1)
M 178:4 Terrain.get_cell_coords - A (1)
M 187:4 Terrain.get_type_at - A (1)
M 191:4 Terrain.get_terrain_props_at - A (1)
M 195:4 Terrain.get_water_distance_at - A (1)
M 201:4 SpatialGrid.__init__ - A (1)
M 205:4 SpatialGrid.clear - A (1)
M 246:4 Agent.__init__ - A (1)
M 271:4 Agent.radius - A (1)
M 406:4 Agent._apply_reproduction_cost - A (1)
M 411:4 Agent._apply_reproduction_to_pair - A (1)
M 415:4 Agent._find_reproduction_partner - A (1)
M 433:4 Agent.wander - A (1)
M 441:4 Agent.is_in_interaction_range - A (1)
M 537:4 Agent._spawn_offspring - A (1)
M 574:4 Agent._special_interrupt - A (1)
M 577:4 Agent._handle_hunger - A (1)
M 593:4 Prey.__init__ - A (1)
M 679:4 Predator.__init__ - A (1)
M 764:4 Clover.radius - A (1)
M 767:4 Clover.update_needs - A (1)
M 870:4 SimThread.__init__ - A (1)
M 890:4 SimThread.stop - A (1)
M 894:4 SimThread.pause - A (1)
M 897:4 SimThread.resume - A (1)
M 901:4 SimThread.is_paused - A (1)
M 928:4 SimThread._spawn_clover - A (1)
M 1014:4 ParameterEntry.__init__ - A (1)
M 1022:4 ParameterEntry.get - A (1)
M 1025:4 ParameterEntry.set_state - A (1)
M 1031:4 App.__init__ - A (1)
M 1050:4 App._build_ui - A (1)
M 1058:4 App._create_canvas_area - A (1)
M 1069:4 App._create_control_panel - A (1)
M 1076:4 App._create_info_label - A (1)
M 1084:4 App._build_buttons - A (1)
M 1092:4 App._add_simulation_action_buttons - A (1)
M 1103:4 App._add_speed_control_inputs - A (1)
M 1114:4 App._add_debug_toggle - A (1)
M 1122:4 App._build_settings - A (1)
M 1129:4 App._add_agent_settings_row - A (1)
M 1146:4 App._add_terrain_settings_row - A (1)
M 1159:4 App._on_drag_start - A (1)
M 1163:4 App._on_drag_motion - A (1)
M 1171:4 App._set_ui_state - A (1)
M 1196:4 App._set_ui_running - A (1)
M 1260:4 App.restart - A (1)
M 1280:4 App._reset_ui_simulation_view - A (1)
M 1323:4 App._process_payload - A (1)
M 1333:4 App._draw_sim - A (1)
M 1368:4 App._create_terrain_rect - A (1)
M 1376:4 App._update_canvas_panning - A (1)
M 1410:4 App._create_agent_graphics_item - A (1)
M 1447:4 App._update_status_bar - A (1)
M 1468:4 App._update_info - A (1)

128 blocks (classes, functions, methods) analyzed.
Average complexity: A (2.5)
C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py
M 25:4 TerrainThresholds.classify - B (6)
C 10:0 TerrainThresholds - A (5)
M 208:4 TerrainBuilder.generate_terrain - A (5)
F 39:0 _build_noise_grid - A (3)
F 61:0 generate_terrain_grid - A (3)
C 103:0 TerrainBuilder - A (3)
M 262:4 TerrainBuilder.save_terrain - A (3)
M 18:4 TerrainThresholds.normalized - A (1)
M 104:4 TerrainBuilder.__init__ - A (1)
M 116:4 TerrainBuilder._build_ui - A (1)
M 203:4 TerrainBuilder.generate_random_seed - A (1)

11 blocks (classes, functions, methods) analyzed.
Average complexity: A (2.909090909090909)
C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\main.py - C (0.00)
C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6\terrain_builder.py - A (39.11)
(.venv) PS C:\Users\simon\Desktop\KPO\Kvaliteta-Programske-Opreme\KPO-N6> 
