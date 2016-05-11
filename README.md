# magdalena
Magdalena is a little town between the VLA and Socorro, New Mexico.

This repository contains scripts creating some summarized JSONs of data pulled from [Socorro](https://github.com/mozilla/socorro) (which was originally named this way because it collects and analyzes crash data from "out there", similar to the VLA that has its operations center in Socorro, NM).

Some of that JSON data is being used in dashboards and graphs of [Datil](https://github.com/KaiRo-at/datil), serving the JSON files to the web so a Datil install can consume them.

Currently, the following scripts are part of Magdalena:

* apiuse.py: An example script on how to use the Socorro API with python.
* datautils.py: Utility functions and general variables to be used in the other scripts.
* get-dailydata.py: Assembles per-day crash data for all active Firefox versions.
* get-bytypedata.py: Gets per-process-type (also separating out plugin hangs and crashes) crash data on every channel of Firefox desktop and Android, to be used by Datil dashboard and longtermgraph.
* get-categorydata.py: Gets crash data for several crash categories on every channel of Firefox desktop and Android, to be used by Datil dashboard and longtermgraph.

The bytypedata and categorydata scripts sum up multiple recent versions on all channels to smoothen over the fact that usually the crash rate curves start high right after a release while rates for older versions drop equally when a new version gets released. This makes the resulting graphs more easily available to detect abnormal spikes and give a general impression of what the state of a channel is and how it changes with history.
