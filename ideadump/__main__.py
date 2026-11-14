# PYTHON_ARGCOMPLETE_OK
"""``ideadump`` on the command line: every verb of :data:`ideadump.tools.TOOLS`.

    ideadump add "the owner's words, verbatim" --title "Short title" --tags "a, b" --source my-session
    ideadump note <id> --file research.md --depth light
    ideadump find "offline speech to text"          # or --file recent-work.md
    ideadump ls --status promising
    ideadump show <id>
    ideadump sync

``--json`` as the last argument prints the whole result instead of its text. Exit status is 0 on
success and 1 on an error, whose message says what to do next.
"""

from __future__ import annotations

import functools
import json
import sys

import cw

from ideadump import tools
from ideadump.base import IdeadumpError


def _command(func):
    func = tools.without(func)

    @functools.wraps(func)
    def command(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IdeadumpError as error:
            raise cw.CommandError(str(error)) from error

    return command


def _egress(as_json):
    def egress(result, *, out, err):
        if as_json or not isinstance(result, dict):
            print(
                json.dumps(result, indent=2, ensure_ascii=False, default=str), file=out
            )
        else:
            print(result.get("text", ""), file=out)
        return 0

    return egress


def main(argv=None):
    """Run the command line. The ``ideadump`` console script."""
    for stream in (sys.stdout, sys.stderr):
        getattr(stream, "reconfigure", lambda **_: None)(errors="backslashreplace")
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = bool(argv) and argv[-1] == "--json"
    if as_json:
        argv = argv[:-1]
    commands = {f.__name__.replace("_", "-"): _command(f) for f in tools.TOOLS}
    code = cw.dispatch(
        commands,
        argv,
        prog="ideadump",
        convention=cw.MODERN,
        egress=_egress(as_json),
    )
    raise SystemExit(code)


if __name__ == "__main__":
    main()
