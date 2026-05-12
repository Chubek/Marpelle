# Runtime

Runtime runs in foreground by default. Optional daemon mode is explicit via manifest or runtime flag.

Behavior:
- create runtime/state directories
- start Unix socket server
- register service in LMDB (when `register=true`)
- write pid file when configured
- remove registration/socket/pid on shutdown
