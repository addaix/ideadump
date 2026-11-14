# ideadump.base

Errors and constants shared across ideadump.

An idea is one folder in the store, `ideas/<id>/`, holding its record
(`idea.json`, the single source of truth), a rendered `README.md` that a person
reads on GitHub or a phone, and its research notes under `research/`. Nothing here
depends on any other module.

### Module Attributes

| [`STATUSES`](#ideadump.base.STATUSES)   | Where an idea stands.          |
|-------------------------------------------------------------|--------------------------------|
| [`DEPTHS`](#ideadump.base.DEPTHS)     | How deep a research note went. |

### Functions

| [`record_key`](#ideadump.base.record_key)(idea_id)   | The store key of an idea's record.   |
|------------------------------------------------------------------------|--------------------------------------|

### Exceptions

| [`IdeadumpError`](#ideadump.base.IdeadumpError)   | An error whose message says what to do next.   |
|------------------------------------------------------------------|------------------------------------------------|

### ideadump.base.DEPTHS *= ('light', 'deep')*

How deep a research note went. `light` is the pass made at capture (minutes, a
few sources); `deep` is a full `do-research`-style report.

### *exception* ideadump.base.IdeadumpError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

An error whose message says what to do next.

### ideadump.base.STATUSES *= ('new', 'promising', 'parked', 'pursued', 'dropped')*

Where an idea stands. `new` on capture; the owner (or an agent relaying the
owner’s words) moves it on. `promising` is the cue for a deeper research pass.

### ideadump.base.record_key(idea_id)

The store key of an idea’s record.

```pycon
>>> record_key("2026-11-14-an-idea")
'ideas/2026-11-14-an-idea/idea.json'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
