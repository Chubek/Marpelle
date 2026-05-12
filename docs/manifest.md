# Manifest

Supported files:
- `MARPELLE.json`
- `MARPELLE.yaml`
- `MARPELLE.yml`

Required fields:
- `name` (string)
- `version` (string)
- `socket` (string)
- `commands` (non-empty list of strings)
- `register` (boolean)

Optional fields:
- `pid_file`, `daemonize`, `working_directory`, `umask`, `user`, `group`
