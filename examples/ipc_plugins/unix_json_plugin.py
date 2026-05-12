from marpelle.ipc import IPCBackendSpec, IPCTypes, UnixSocketReceiver, UnixSocketSender
from marpelle.serde import JsonSerde

serde = JsonSerde()

MARPELLE_IPC_PLUGIN = {
    "name": "unix-json",
    "type": IPCTypes.REQUEST_REPLY.value,
    "serializer": serde,
    "deserializer": serde,
    "sender_factory": UnixSocketSender,
    "receiver_factory": UnixSocketReceiver,
}


def register(manager):
    manager.register(
        IPCBackendSpec(
            name="unix-json-register",
            ipc_type=IPCTypes.REQUEST_REPLY,
            serializer=serde,
            deserializer=serde,
            sender_factory=UnixSocketSender,
            receiver_factory=UnixSocketReceiver,
        )
    )
