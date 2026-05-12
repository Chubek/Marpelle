# Build

`marpelle build` wraps Nuitka and includes:
- manifest data file
- `marpelle` runtime package
- `marpelle_hooks` module

Example:
- `marpelle build examples/example_service/app.py --manifest examples/example_service/MARPELLE.json --onefile`
