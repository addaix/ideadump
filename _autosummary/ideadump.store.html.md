# ideadump.store

Where ideas live: a `MutableMapping` of `/`-separated path to text.

Every verb takes a `files` store, so the default local folder can be swapped for any
other `dol` store (or a plain `dict` in tests) without touching the rest. The
default is a folder, the data root:

1. the `data_dir` argument, else
2. `$IDEADUMP_DATA_DIR`, else
3. `~/.local/share/ideadump` (`$XDG_DATA_HOME` and `%LOCALAPPDATA%` honoured).

To keep ideas in a private git repository, make the data root a checkout of it with
`ideadump sync-init <owner>/<name>` (see [`ideadump.sync`](ideadump.html.md#ideadump.sync)); the store
itself does not change.

```pycon
>>> data_dir("somewhere").is_absolute()
True
```

### Functions

| [`data_dir`](#ideadump.store.data_dir)([data_dir])                 | The data root: the argument, else `$IDEADUMP_DATA_DIR`, else the user data folder.   |
|---------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`text_files`](#ideadump.store.text_files)(root)                     | A `dol` files store under `root`: `/`-separated keys, UTF-8 text values.             |
| [`resolve_files`](#ideadump.store.resolve_files)([files, data_dir_])    | `files` if given, else the text store over the data root.                            |
| [`writing`](#ideadump.store.writing)([files, data_dir_, timeout]) | The store, held exclusively while a verb reads, changes and rewrites it.             |

### ideadump.store.data_dir(data_dir=None)

The data root: the argument, else `$IDEADUMP_DATA_DIR`, else the user data folder.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### ideadump.store.resolve_files(files=None, , data_dir_=None)

`files` if given, else the text store over the data root.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### ideadump.store.text_files(root)

A `dol` files store under `root`: `/`-separated keys, UTF-8 text values.

Folders are made on write and never on read; a delete is permanent.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### ideadump.store.writing(files=None, , data_dir_=None, timeout=30.0)

The store, held exclusively while a verb reads, changes and rewrites it.

Several sessions may capture ideas at the same moment; each write verb reads every
record, picks a free id, and rewrites the index, so two of them interleaving would
lose an idea. For the default folder store this takes a lock file in the data root
(created exclusively, so it works on every platform); a store passed in by the
caller is the caller’s to serialise.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]
