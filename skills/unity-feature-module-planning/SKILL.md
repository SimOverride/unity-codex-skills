---
name: unity-feature-module-planning
description: Use when a user wants to design, plan, scope, or clarify a new Unity game feature module before implementation, or asks how to structure a gameplay/UI/system module. Produces a module plan by analyzing requirements, boundaries, data ownership, runtime state, entities, APIs, dependencies, events, randomness, MVP scope, risks, and questions without prescribing a specific domain design.
---

# Unity Feature Module Planning

## Purpose

Use this skill to turn a rough Unity game feature request into an implementable module plan. Do not jump to concrete class designs too early. First derive the module boundary, data ownership, runtime flow, and open questions from the user's requirements.

## 1. Clarify the module goal

Identify:

- player-facing purpose;
- gameplay/system purpose;
- trigger conditions;
- who calls or uses the module;
- what this iteration explicitly will not do.

Produce a short boundary statement:

```text
This module is responsible for X.
It does not own Y.
This iteration includes A/B/C and excludes D/E.
```

If the boundary is ambiguous, ask concrete questions before designing.

## 2. List inputs, outputs, and state

Separate the feature into:

- inputs: config, player actions, time ticks, combat events, save data, random results, scene references;
- outputs: runtime state changes, presentation events, UI data, spawned objects, saved results;
- state: authored config, mutable runtime state, view-only state, persistent save state, temporary calculation results.

Use this rule of thumb:

```text
Config is read-only input.
Runtime owns cross-frame gameplay state.
Views own visual-only state.
UI and animation should not hide gameplay state.
```

## 3. Separate static config from runtime instances

For every important value, decide whether it belongs to config or runtime.

Config usually contains:

- base parameters;
- display text;
- authoring references;
- rule parameters;
- links to other configs.

Runtime usually contains:

- current values;
- timers;
- progress;
- ownership;
- generated instance IDs;
- temporary effects;
- lifecycle flags.

Call out whether stable config IDs, runtime instance IDs, or save IDs are needed.

## 4. Identify core entities

Extract candidate entities from the requirements, then keep only entities that need at least one of:

- independent lifecycle;
- independent state;
- references from other systems;
- configuration;
- one-to-many relationships;
- cleanup rules.

Classify likely pieces as:

- config entity;
- runtime instance;
- service or rule resolver;
- presentation/view bridge;
- editor or authoring tool;
- UI adapter.

Do not create an entity for a process that can remain a simple method or service operation.

## 5. Define state-changing entry points

List the commands that may mutate state, such as:

```text
Create / Add / Remove / Move / Use / Trigger / Tick / Resolve / Clear
```

Each state-changing entry point should follow:

```text
validate
→ mutate runtime state
→ recompute derived state
→ emit facts or mark snapshots dirty
```

Avoid duplicated rules in UI, views, animation callbacks, editor tools, or multiple controllers.

## 6. Map dependencies and ownership

Write what the module reads, calls, and is called by.

Check dependency direction:

- rules should not depend on concrete views, prefabs, animations, or UI widgets;
- presentation may depend on runtime snapshots and facts;
- config should not depend on runtime instances;
- save data should store stable IDs and values, not scene object identity;
- infrastructure adapters should wrap Unity APIs when gameplay needs physics, time, or scene queries.

If a dependency would create a cycle, redesign the boundary.

## 7. Choose event and synchronization strategy

Classify changes:

- instantaneous facts: spawn, death, damage, pickup, combine, trigger animation;
- continuous state: position, health bar, cooldown, selected state, level display;
- initial state: startup, load, rebind.

Use events for instantaneous facts, snapshots or centralized sync for continuous state, and one-time snapshot binding for initial state.

Avoid both extremes:

- event spam for every continuously changing number;
- polling everywhere for one-time events.

## 8. Decide randomness and reproducibility

If the module uses randomness, define:

- random source owner;
- seed source;
- whether results must be replayable;
- whether this module needs an independent random stream;
- whether visual randomness must be separated from gameplay randomness.

Do not let adding a new random call accidentally change unrelated systems.

## 9. Scope the minimum useful version

Divide work into:

- must implement now;
- should be easy to change later;
- deliberately not implemented;
- explicitly rejected.

Reserve extension points only when they reduce likely future cost. Do not create empty interfaces, unused abstractions, or compatibility layers without a concrete reason.

## 10. Ask only blocking questions

Ask before implementation when uncertainty affects:

- gameplay rules;
- data ownership;
- lifecycle and cleanup;
- timing;
- persistence;
- presentation structure;
- Inspector/resource setup;
- compatibility with existing systems.

Make questions specific and answerable:

```text
Should the effect stack or refresh?
When the source object disappears, should active effects end immediately?
Do newly spawned objects receive existing global bonuses?
```

## 11. Output the plan

A useful module plan should include:

- module responsibility;
- non-goals for this iteration;
- core data structures or entity categories;
- config/runtime/presentation ownership;
- state-changing entry points;
- runtime flow;
- event/sync strategy;
- dependency map;
- randomness and lifecycle notes;
- MVP scope;
- blocking questions, if any.

If questions remain blocking, stop at the plan and ask them. If enough is known, state the implementation approach before editing.

## 12. Implementation handoff checklist

Before moving from plan to implementation, confirm:

- the user has accepted or clarified the plan when needed;
- project-specific architecture rules have been read;
- existing code paths and old mechanisms have been inspected;
- docs and validation expectations are known;
- any Inspector/manual setup impact is identified.

When implementation finishes, report what was built, what was not built, how to configure it, validation results, and unverified areas.
