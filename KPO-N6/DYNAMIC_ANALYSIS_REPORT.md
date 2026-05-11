# Dynamic Analysis Report

## Overview
Dynamic analysis was performed on the `main.py` simulation application to identify performance bottlenecks and runtime behavior. The profiling was primarily conducted using Python's built-in `cProfile` to analyze execution times and function call frequencies.

## Profiling Methodology
The application was launched under `cProfile`, capturing approximately 44 seconds of standard execution time. Data was extracted primarily focusing on cumulative time (`cumtime`) and total time (`tottime`) across the execution. The raw output from the profiler was saved to `profile_stats.prof` and extracted using the `pstats` module.

### Raw Data Extraction
Here is the concrete data sampled globally from top cumulated functions:

```text
         832118 function calls (831748 primitive calls) in 44.079 seconds

   Ordered by: cumulative time
   List reduced from 675 to 30 due to restriction <30>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     28/1    0.001    0.000   44.084   44.084 {built-in method builtins.exec}
        1    0.000    0.000   44.084   44.084 main.py:1(<module>)
        1    0.000    0.000   43.881   43.881 __init__.py:1502(mainloop)
        1   42.073   42.073   43.881   43.881 {method 'mainloop' of '_tkinter.tkapp' objects}
      563    0.004    0.000    1.808    0.003 __init__.py:1962(__call__)
      560    0.007    0.000    1.639    0.003 main.py:1287(_poll_queue)
      558    0.003    0.000    1.550    0.003 __init__.py:859(callit)
      559    0.012    0.000    1.533    0.003 main.py:1323(_process_payload)
      559    0.004    0.000    1.410    0.003 main.py:1333(_draw_sim)
      559    0.094    0.000    1.322    0.002 main.py:1380(_draw_agents)
    56769    0.240    0.000    1.203    0.000 main.py:1394(_update_agent_graphic)
    77331    0.743    0.000    0.743    0.000 {method 'call' of '_tkinter.tkapp' objects}
    64809    0.152    0.000    0.600    0.000 __init__.py:2834(coords)
     1340    0.009    0.000    0.221    0.000 main.py:1423(_show_agent_debug)
```

## Observations (GUI Thread)

The application separates execution between a Tkinter UI thread and a background simulation thread (`SimThread`). The profiling primarily captured the Tkinter main loop and the methods that communicate with the simulation thread via a queue. These insights are extracted directly from the cProfile tabular data shown above.

### 1. Tkinter Event Loop `mainloop`
- **Finding:** The largest block of time (43.8s cumtime) was bound by the `_tkinter.tkapp.mainloop()`.
- **Explanation:** This behaves as expected for GUI applications. It shows that overall program activity is tethered to the Tkinter UI event cycle over the 44-second run.
- **Data Source:** Line showing `1   42.073   42.073   43.881   43.881 {method 'mainloop' of '_tkinter.tkapp' objects}`.

### 2. High Frequency UI Methods
The visualization processing accounts for the most significant CPU usage on the main thread:
- **Finding:** The method `_update_agent_graphic` was called **56,769 times**, resulting in `1.203s` of cumulative time and `0.240s` of internal (tottime) processing.
- **Explanation:** At a low level, this function updates individual agent positions on the graphical canvas. Tkinter's `coords` method (`__init__.py:2834(coords)`) was called **64,809 times**, consuming `0.600s`. The frequent calling implies each visible agent has its graphical objects relocated frame by frame.
- **Data Source:** Rows showcasing `1394(_update_agent_graphic)` and `2834(coords)`.

### 3. Queue Polling (`_poll_queue`)
- **Finding:** `_poll_queue` was called exactly **560 times** (roughly equating to processing UI updates every `~78ms` on average over 44 seconds).
- **Explanation:** Each payload extraction (`_process_payload` called **559 times**) unloads extensive data mapping the simulation state which the UI then redraws (`_draw_agents` takes `1.322s` cumulatively). This reflects an intensely decoupled but data-heavy bridge between the worker calculation thread and the main UI queue.
- **Data Source:** Rows showcasing corresponding counts for `1287(_poll_queue)`, `1323(_process_payload)`, and `1380(_draw_agents)`.

## Simulation Thread Considerations
While the background thread effectively unblocks the Tkinter UI to keep it responsive, the architecture requires frequent serialization/copying of object states (agent locations, statuses) into the Tkinter main thread.

## Recommendations for Optimization
1. **Batch Canvas Updates:** Given the high frequency of `coords` and `itemconfigure` calls, reducing GUI element updates (e.g., only updating changed pixels or batching draw calls) can significantly improve visual framing rates.
2. **Optimize Inter-Thread Communication:** Ensure only strictly necessary data per frame is pushed to the Tkinter payload queue. Delta-updates (only sending moved/changed agents) instead of full state dumps could reduce UI side parsing.
3. **Targeted Thread Profiling:** To further optimize the math/physics engine, a specialized profiler (like `pyinstrument`) should be attached solely within the `SimThread.run()` loop to evaluate collision detection loops and pathfinding.

## Conclusion
The simulation performs adequately but is visibly tethered by Tkinter's rendering capabilities. Relocating logic is correct, but rendering loops remain the primary scaling bottleneck for larger simulations.


python -m cProfile -o profile_stats.prof main.py
python -c "import pstats; p = pstats.Stats('profile_stats.prof'); p.strip_dirs().sort_stats('cumulative').print_stats(30)" > profile_output.txt