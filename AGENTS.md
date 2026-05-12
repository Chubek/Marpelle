# To The LLM Agent

## Basic Additions/Changes

1. Create a `--help` for the CLI. This help must be modular, for example `marpelle manifest --help`. Colorize the outputs, using `termcolors` library;
2. Make a `setup.py` as well as `pyproject.toml`;
3. Expand the help, make each help file in `docs/` at least 150 lines;
4. Create a `docs/Makefile` with targets such as `build-pdf`, `build-html`, `build-docbook`;
5. Create `Makefile` in root with targets such as `clean` and `build` and `install`;
6. Allow the user to choose the C compiler in MANIFEST.json, default, GCC;

## More IPC Backends

Turn `src/marpelle/ipc.py` into an interface, and people define IPCs in colon-seprated driectories pointed to by `MARPELLE_PATH`. By default, this directory is `~/.marpelle`.

An IPC implementation looks like this:

```python
from marpelle.ipc import IPCManager, IPCSender, IPCReceiver, IPCTypes
from marpelle.serde import Serializer, Deserializer
from marpelle.module import LoadSharedLibrary
from marpelle.transport import publisher, subscriber, unsubscriber

import lmdb

manager = IPCManager(name="my_pubsub_ipc")

manager.add_query_param("TaskID", manager.process.id)
manager.add_query_param("MessageID", manager.message.id)

# this is perhaps a C file that implements `include/marpelle-module.h`
handle = LoadSharedLibrary("my_pubsub_ipc.so")

class MySerializer(Serializer):
    pass
    # will implent

class MyDeserializer(Deserializer):
    pass
    # will implement

class MySender(IPCSender):
    pass

class MyReceiver(IPCReceiver):
     pass


@subscriber("foo://subscribe/{TaskID}")
def subscribe(ctx):
     pass

@unsubscribe("foo://unsubscribe/{TaskID}")
def unsubscribe(ctx):
     pass


@pulish("foo://message/{MessageID}")
def publish(ctx):
    pass


manager.registery.add({ 
    "serializer": MySerializer,
    "deserializer": MyDeserializer,
    "sender": MySender,
    "receiver": MyReceiver,
    "type": IPCTypes.PubSub,
    "functions": {
        "subscribe": subscribe,
        "unsubscribe": unsubscribe,
        "publish": publish
    },
    external_handle: handle,
})

```

I want you to *improve upon this concept* and give me a much better IPC module interface. Plus, you need to add several new libraries: `src/marpelle/{serde, module, transport, ipc}.py`

## The `DAEMON.lua` File

We use the Python library `lupa` to communicate with Lua. `DAEMON.lua` is a file that we put next to `MANIFESTS.json`, direct to it in the aforementioned file, or pass via CLI.

This file defines how daemonization and IPC is done. These files run on a sandboxed Lua environment.

This file is handled in `src/marpelle/luaspec-daemon.py`. We need to updathe the CLI to add this. Please add this, the add help to CLI and colorize it.

For this section of the library, we use `lupa` and `python-daemon`.

*Note*: Don't be afraid of changing old files, or even removing them.
