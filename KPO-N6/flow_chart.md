# EcoSim Code Flow Charts

This document maps out the logical flows, loops, and behaviors of the `main.py` ecosystem simulator. It provides separated and visually enhanced charts for the various distinct systems.

---

## 1. High-Level Architecture & Thread Communication

The simulation relies on a producer-consumer relationship between the Simulation Thread and the Main UI Thread. 

```text
 ┌──────────────────────────────────┐        ┌───────────────────────────────────┐
 │       UI THREAD (Tkinter)        │        │      SIMULATION THREAD            │
 │                                  │        │                                   │
 │  ┌────────────────────────────┐  │        │  ┌─────────────────────────────┐  │
 │  │        User Clicks         │  │        │  │       SimThread.run()       │  │
 │  │      btn_start.invoke()    │  │        │  └──────┬──────────────────────┘  │
 │  └──────┬─────────────────────┘  │        │         │                         │
 │         │ Parameters             │        │         ▼                         │
 │  ┌──────▼─────────────────────┐  │        │  ┌─────────────────────────────┐  │
 │  │    App.start()             │──┼───────►│  │ _spawn() / Init Terrain     │  │
 │  │    (spawns SimThread)      │  │        │  └──────┬──────────────────────┘  │
 │  └──────┬─────────────────────┘  │        │         │                         │
 │         │                        │        │         ▼ ◄──────────────────┐  │
 │  ┌──────▼─────────────────────┐  │        │  ┌─────────────────────────────┐  │
 │  │ App._poll_queue()          │◄─┼─┐      │  │ Wait for unpause            │  │
 │  │ Scheduled by after()       │  │ │      │  └──────┬──────────────────────┘  │
 │  └──────┬─────────────────────┘  │ │      │         │                         │
 │         │                        │ │      │         ▼                         │
 │  ┌──────▼─────────────────────┐  │ │      │  ┌─────────────────────────────┐  │
 │  │ App._drain_queue_latest()  │  │ │      │  │ _step() (Calculate Tick)    │  │
 │  └──────┬─────────────────────┘  │ │      │  └──────┬──────────────────────┘  │
 │         │                        │ │      │         │                         │
 │  ┌──────▼─────────────────────┐  │ │      │         ▼                         │
 │  │ app._process_payload()     │  │ ├──────┼──┌─────────────────────────────┐  │
 │  │  - _draw_sim()             │  │ │ Data │  │ _send_payload() / data.put()│  │
 │  │  - _update_info()          │  │ └──────┼──└──────┬──────────────────────┘  │
 │  └────────────────────────────┘  │        │         │                         │
 └──────────────────────────────────┘        │         ▼                         │
                                             │  ┌─────────────────────────────┐  │
                                             │  │ time.sleep(sim_delay)       │──┘
                                             │  └─────────────────────────────┘  │
                                             └───────────────────────────────────┘
```

---

## 2. Simulation Tick Loop (`SimThread._step`)

Every simulation tick, the biological engine recalculates the spatial index, processes logic for all entities, filters dead entities, and spawns ambient food.

```text
       ┌────────────────────────────────────────────────────────┐
       │                       _step()                          │
       └──────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
       ┌────────────────────────────────────────────────────────┐
       │               _rebuild_spatial_grid()                  │
       │ (Clears SpatialGrid and inserts all living agents)     │
       └──────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
       ┌────────────────────────────────────────────────────────┐
       │             _process_agents_for_tick()                 │
       │   [For each 'ag' in active agents list:]               │
       └──────────────────────────┬─────────────────────────────┘
                                  │
┌─────────────────────────────────┼──────────────────────────────┐
│                                 ▼                              │
│      ┌──────────────────────────────────────────────────┐      │
│      │               _process_single_agent()            │      │
│      └──────────────────────────┬───────────────────────┘      │
│                                 ▼                              │
│      ┌──────────────────────────────────────────────────┐      │
│      │                 Is agent alive?                  │      │
│      │             (If No ──► Skip to next)             │      │
│      └──────────────────────────┬───────────────────────┘      │
│                                 ▼                              │
│      ┌──────────────────────────────────────────────────┐      │
│      │                   Is it Plant?                   │      │
│      │        Yes ──► Clover.act()                      │      │
│      │         No ──► Agent.update_needs() & act()      │      │
│      └──────────────────────────┬───────────────────────┘      │
│                                 │                              │
└─────────────────────────────────┼──────────────────────────────┘
                                  ▼
       ┌────────────────────────────────────────────────────────┐
       │          Merge newly spawned agents / clones           │
       │          Filter self.agents (keep only alive = True)   │
       └──────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
       ┌────────────────────────────────────────────────────────┐
       │        Random chance to spawn extra ambient Clover     │
       └────────────────────────────────────────────────────────┘
```

---

## 3. Mobile Agent Action Flow (`Agent.act`)

For non-plant agents (Prey, Predator), decision-making uses local grid awareness to evaluate interruptions (like threats) or standard physiological needs.

```text
                       ┌───────────────────────┐
                       │     Agent.act()       │
                       └───────────┬───────────┘
                                   │
                                   ▼
             ┌───────────────────────────────────────────┐
             │ Get nearby entities from spatial grid     │
             └─────────────────────┬─────────────────────┘
                                   │
                                   ▼
             ┌───────────────────────────────────────────┐
             │         _special_interrupt()?             │
             │ (e.g., Prey sees Predator ──► FLEE!)      │
             └─────────────────────┬─────────────────────┘
                 │ Yes                             │ No
                 ▼                                 ▼
        ┌──────────────────┐             ┌─────────────────────┐
        │   Action: FLEE   │             │   get_priority()    │
        │ Adjust angle &   │             └─────────┬───────────┘
        │   move_step()    │                       │ Determine primary need
        └──────────────────┘                       ▼
                             ┌─────────────────────────────────────────────┐
                             │               PRIORITY MATCH                │
                             └┬─────────────┬─────────────┬─────────────┬──┘
                              │             │             │             │
                    THIRST ◄──┘             │             │             └──► HUNGER
                      │          REPRODUCTION             │                 │
                      ▼             │                     │ WANDER          ▼
            ┌───────────────┐       ▼                     │      ┌────────────────────┐
            │ _handle_thirst│ ┌───────────────┐           ▼      │   _handle_hunger   │
            └───────┬───────┘ │ _handle_repro │   ┌──────────────┤   (Impl. specific) │
                    │         └───────┬───────┘   │   Action:    │           │        │
                    ▼                 │           │    WANDER    │           ▼        │
           ┌────────────────┐         ▼           └──────┬───────┘  ┌─────────────────┴────┐
           │ Seek BFS map   │ ┌────────────────┐         │          │ Prey: Seek Clover    │
           │ nearest water  │ │ Find closest   │         ▼          │ Pred: Seek Prey      │
           └───────┬────────┘ │ viable partner │  ┌──────────────┐  └────────┬─────────────┘
                   │          └───────┬────────┘  │ wander()...  │           │
           ┌───────┴────────┐         │           └──────────────┘   ┌───────┴────────┐
           │ At water edge? │ ┌───────┴───────┐                      │ In interaction │
           │ Y: Drink!      │ │ Close enough? │                      │ range of food? │
           │ N: Move to it. │ │ Y: Breed!     │                      │ Y: Eat/Kill!   │
           └────────────────┘ │ N: Move near. │                      │ N: Move to it. │
                              └───────────────┘                      └────────────────┘
```

---

## 4. Terrain Generation & Validation Loop

Terrain calculates water-availability distances on generation using a Breadth-First Search loop map expansion.

```text
                    ┌───────────────────────────────┐
                    │  _compute_water_distance()    │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Iterate whole Grid:                              │
          │   If tile == Water:                              │
          │     Set dist = 0, Append to queue_cells          │
          │   Else:                                          │
          │     Set dist = Infinity                          │
          └────────────────────────┬─────────────────────────┘
                                   │
             ┌─────────────────────▼──────────────────────┐
             │       WHILE queue_cells is not empty:      │
             │                                            │
             │   1. Pop cell (x, y) & current_dist        │
             │                                            │
             │   2. Loop 4 neighbors (Up, Down, L, R)     │
             │                                            │
             │   3. Is neighbor out of bounds?            │
             │       Yes ──► continue                     │
             │                                            │
             │   4. Is neighbor's dist <= current_dist+1? │
             │       Yes ──► continue                     │
             │                                            │
             │   5. Update neighbor dist = current_dist+1 │
             │   6. Update neighbor nearest_water pointer │
             │   7. Push neighbor to queue_cells          │
             └────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │ Water distance map Complete   │
                    └───────────────────────────────┘
```

---

## 5. Plant Needs & Growth Loop (`Clover.act`)

Unlike mobile agents, `Clover` processes crowding logic and moisture to survive or breed stationary instances.

```text
                        ┌──────────────────────────────┐
                        │        Clover.act()          │
                        └──────────────┬───────────────┘
                                       │
                                       ▼
                 ┌────────────────────────────────────────────┐
                 │ _count_neighbors(radius=30)                │
                 │ Returns count of nearby plants             │
                 └─────────────────────┬──────────────────────┘
                                       │
                                       ▼
                 ┌────────────────────────────────────────────┐
                 │ _update_plant_needs(...)                   │
                 │ Factor in crowding_penalty and limits      │
                 └─────────────────────┬──────────────────────┘
                                       │
                                       ▼
                 ┌────────────────────────────────────────────┐
                 │   Is plant still alive & urge == 100?      │
                 └─┬────────────────────────────────────────┬─┘
                   │ Yes                                    │ No
                   ▼                                        ▼
      ┌─────────────────────────┐             ┌─────────────────────────┐
      │  Is thirst < 5 and      │             │        Do Nothing       │
      │  neighbors < 8?         │             └─────────────────────────┘
      └─┬─────────────────────┬─┘
        │ Yes                 │ No
        ▼                     ▼
┌──────────────────┐  ┌───────────────┐
│ _attempt_spawn() │  │   Wait for    │
│ Roll 5x random & │  │ better env.   │
│ try to find a    │  └───────────────┘
│ Walkable nearby  │
│ spot to multiply │
└──────────────────┘

```
