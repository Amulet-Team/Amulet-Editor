"""
Amulet needs a mechanism to send data between processes (e.g. copied structures) as well as calling functions in remote processes (e.g. requesting chunk data when converting).
This means we need a Remote Procedure Calling (RPC) mechanism. Qt has QDBus but this is linux only.

We need an implementation of pier to pier communication so that processes can directly interact (e.g. during conversion)
We also need a mechanism to call a function in all processes (e.g. notifying of plugin state change)
The former must be implemented in a way that the sender can get the response. The latter can be a blind call.



Global function calls are implemented via the @Global decorator
                which replaces the function with one that calls


This module handles communication between the multiple different processes.

When Amulet starts it will verify the existence of the broker process or create it if it does not exist.
The broker process manages which processes own which worlds and informs processes how to connect to other processes.

All processes have a listener to receive incoming connections and a connection to the broker process.

When the last child connection is closed, the broker will spawn a process with no world attached. If this is closed the broker will exit.

If the broker connection is lost by the child (process crashed or killed by user) the child processes will respawn it.
"""

from __future__ import annotations

import logging
from typing import Optional, Any, Callable, Sequence, Mapping, TypeVar
from uuid import uuid4
import pickle
from weakref import WeakValueDictionary
import traceback

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalSocket, QLocalServer

from amulet_editor.models.widgets import DisplayException, AmuletTracebackDialog

server_address = str(uuid4())
BrokerAddress = "com.amuletmc.broker"

_is_broker = False
_listener: Optional[RemoteProcedureCallingListener] = None
_broker_connection: Optional[RemoteProcedureCallingConnection] = None
_remote_functions: WeakValueDictionary[str, Callable] = WeakValueDictionary()


UUID = bytes
SuccessCallbackT = Callable[[Any], Any]
ErrorCallbackT = Callable[[Exception], Any]
# The function address and args to pass
CallDataT = tuple[str, Sequence, Mapping]
CallDataStorage = dict[UUID, tuple[CallDataT, tuple[SuccessCallbackT, ErrorCallbackT]]]
T = TypeVar("T", bound=Callable)


def register_remote_procedure(func: T) -> T:
    """Register the callable to allow calling from a remote process."""
    name = f"{func.__module__}.{func.__qualname__}"
    _remote_functions[name] = func
    return func


@register_remote_procedure
def call_global(address, args, kwargs):
    """
    Call a procedure in all child processes.
    The return values are discarded.

    :param address: The address of the procedure to call.
    :param args: The arguments to pass to the procedure.
    :param kwargs: The keyword arguments to pass to the procedure.
    """
    if not _is_broker:
        raise RuntimeError("This function is not valid in this context.")
    # TODO: call the function in all child processes
    raise NotImplementedError


@register_remote_procedure
def get_server_address():
    """Get the unique identifier for the QLocalServer in this process"""
    return server_address


class register_global_remote_procedure:
    """A decorator that enables a function to be called in all processes."""
    def __init__(self, func: Callable):
        if not callable(func):
            raise TypeError("func must be callable")
        self._func = register_remote_procedure(func)

    def __call__(self, *args, **kwargs):
        if _is_broker:
            # Call in all child processes
            raise NotImplementedError
        else:
            # Call in broker
            raise NotImplementedError


class RemoteProcedureCallingConnection(QObject):
    def __init__(self, parent=None):
        """Use one of the classmethods to construct this class."""
        super().__init__(parent)

        # A dictionary mapping the UUID for the call to the callback functions.
        self._calls: CallDataStorage = {}
        self._connection: Optional[QLocalSocket] = None

    @classmethod
    def from_address(cls, address: str) -> RemoteProcedureCallingConnection:
        """Create a connection to a QLocalServer at the given address."""
        self = cls()
        self._connection = QLocalSocket()
        self._connection.connectToServer(address)
        self._init_connection()
        return self

    @classmethod
    def from_socket(cls, socket: QLocalSocket) -> RemoteProcedureCallingConnection:
        """Create a connection with an existing QLocalSocket."""
        self = cls()
        self._connection = socket
        self._init_connection()
        return self

    def _init_connection(self):
        self._connection.readyRead.connect(self._process_response)
        self._connection.disconnected.connect(self.disconnected)

    # The connection has been disconnected
    disconnected = Signal()

    @property
    def has_pending_calls(self) -> bool:
        """Have calls been sent but a response is still pending."""
        return bool(self._calls)

    @property
    def pending_calls(self) -> CallDataStorage:
        """The data for all calls whose response is still pending."""
        return self._calls.copy()

    def call(
        self,
        address: str,
        args: Sequence,
        kwargs: Mapping,
        success_callback: SuccessCallbackT,
        error_callback: ErrorCallbackT,
    ):
        """
        Call a function in the connected process.

        :param address: The address of the function to call in the remote process.
        :param args: The arguments to pass to the remote function (Must be pickleable)
        :param kwargs: The keyword arguments to pass to the remote function (Must be pickleable)
        :param success_callback: A function to call with the return value.
        :param error_callback: A function to call if the remote function raises an exception.
        :return:
        """
        identifier = str(uuid4()).encode()
        self._calls[identifier] = ((address, args, kwargs), (success_callback, error_callback))
        payload = identifier + pickle.dumps((
            address,
            args,
            kwargs
        ))
        self._connection.write(payload)

    def _process_response(self):
        with DisplayException("Exception parsing incoming connection."):
            payload = self._connection.readAll().data()
            identifier = payload[:36]
            payload = payload[36:]
            is_exception, response = pickle.loads(payload)

        _, (success_callback, error_callback) = self._calls.pop(identifier)
        if is_exception:
            with DisplayException(f"Calling error_callback {error_callback}"):
                error_callback(response)
        else:
            with DisplayException(f"Calling success_callback {success_callback}"):
                success_callback(response)


class RemoteProcedureCallingListener(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._connections = []
        self._server: Optional[QLocalServer] = None

    @classmethod
    def from_address(cls, address: str):
        self = cls()
        self._server = QLocalServer()
        if self._server.listen(address):
            self._server.newConnection.connect(self.on_connect)
        else:
            print(self._server.errorString())
        return self

    def on_connect(self):
        print("connected")
        connection = self._server.nextPendingConnection()
        self._connections.append(connection)

        def remove():
            print("disconnected")
            self._connections.remove(connection)

        def read():
            print("reading")
            try:
                payload = connection.readAll().data()
                identifier = payload[:36]
                payload = payload[36:]
            except Exception as e:
                logging.exception(e)
                return

            try:
                address, args, kwargs = pickle.loads(payload)
                func = _remote_functions.get(address, None)
                if func is None:
                    connection.write(
                        identifier + pickle.dumps((
                            True,
                            f"Could not find function {address}"
                        ))
                    )
                    return

                response = func(*args, **kwargs)

                response_payload = identifier + pickle.dumps((
                    False,
                    response
                ))
                connection.write(response_payload)

            except Exception:
                connection.write(
                    identifier + pickle.dumps((
                        True,
                        traceback.format_exc()
                    ))
                )

        connection.disconnected.connect(remove)
        connection.readyRead.connect(read)


def init_state(broker=False):
    """Init the messaging state"""
    global _is_broker, _listener, _broker_connection
    _is_broker = bool(broker)
    _listener = RemoteProcedureCallingListener.from_address(BrokerAddress if _is_broker else server_address)
    _broker_connection = RemoteProcedureCallingConnection.from_address(BrokerAddress)

    if _is_broker:
        def success(result):
            print("success", server_address, result)
            if result != server_address:
                QApplication.quit()

        def error(tb_str):
            print("err", tb_str)
            dialog = AmuletTracebackDialog(
                title="Broker exception",
                error="Broker exception",
                traceback=tb_str,
            )
            dialog.exec()

        _broker_connection.call(
            f"{__name__}.{get_server_address.__qualname__}",
            [],
            {},
            success,
            error
        )
    else:
        pass
        # TODO: initialise the broker if it does not exist.
