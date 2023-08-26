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
import sys
from typing import Any, Callable, Sequence, Mapping, TypeVar, Optional
from uuid import uuid4
import pickle
from weakref import WeakValueDictionary
import traceback
import subprocess
import struct

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalSocket, QLocalServer

from amulet_editor.data.project import get_level
from amulet_editor.models.widgets.traceback_dialog import (
    DisplayException,
    display_exception,
)
from amulet_editor.application._cli import spawn_process, BROKER
from amulet_editor.data.paths._application import logging_directory

log = logging.getLogger(__name__)

CallableT = TypeVar("CallableT", bound=Callable)
UUID = bytes
SuccessCallbackT = Callable[[Any], Any]
ErrorCallbackT = Callable[[Exception], Any]
# The function address and args to pass
CallDataT = tuple[str, Sequence, Mapping]
CallDataStorage = dict[UUID, tuple[CallDataT, tuple[SuccessCallbackT, ErrorCallbackT]]]


_is_broker = False
server_uuid = str(uuid4())
BrokerAddress = "com.amuletmc.broker"
_remote_functions: WeakValueDictionary[str, Callable] = WeakValueDictionary()


def _get_func_address(func: CallableT) -> str:
    try:
        modname = getattr(func, "__module__")
        qualname = getattr(func, "__qualname__")
    except AttributeError:
        raise ValueError(
            "func must be a static function with __module__ and __qualname__ attributes"
        )
    else:
        return f"{modname}.{qualname}"


def register_remote_procedure(func: CallableT) -> CallableT:
    """Register the callable to allow calling from a remote process."""
    _remote_functions[_get_func_address(func)] = func
    return func


@register_remote_procedure
def get_server_uuid() -> str:
    """Get the unique identifier for the server."""
    return server_uuid


@register_remote_procedure
def is_landing_process() -> Optional[bool]:
    """
    Is this process a landing process (i.e. no level associated with it)
    :return: None if this is the broker process, False if this process has a level otherwise True
    """
    if _is_broker:
        return None
    return get_level() is None


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


# class register_global_remote_procedure:
#     """A decorator that enables a function to be called in all processes."""
#     def __init__(self, func: Callable):
#         if not callable(func):
#             raise TypeError("func must be callable")
#         self._func = register_remote_procedure(func)
#
#     def __call__(self, *args, **kwargs):
#         if _is_broker:
#             # Call in all child processes
#             raise NotImplementedError
#         else:
#             # Call in broker
#             raise NotImplementedError


_remote_call_listener = QLocalServer()
# A dictionary mapping connections to an optional bool storing if the connection is a landing process.
# This allows us to open the landing window or exit the broker process when a connection is closed.
_listener_connections: dict[RemoteProcedureCallingConnection, Optional[bool]] = {}


def _on_listener_connect():
    with DisplayException("Error initialising socket", suppress=True, log=log):
        socket = _remote_call_listener.nextPendingConnection()
        connection = RemoteProcedureCallingConnection(socket)
        _listener_connections[connection] = None
        log.debug(f"New listener connection {socket}")

        if _is_broker:

            def is_landing_success(response: bool):
                log.debug(f"New connection is_landing {response}")
                _listener_connections[connection] = response

            def is_landing_err(tb_str):
                logging.exception(tb_str)

            connection.call(
                is_landing_success,
                is_landing_err,
                is_landing_process,
            )

        def on_disconnect():
            with DisplayException("Error on socket disconnect", suppress=True, log=log):
                is_landing = _listener_connections.pop(connection, None)
                log.debug(f"Listener connection disconnected {socket}. {is_landing}")
                if _is_broker and not any(
                    map(lambda x: x is not None, _listener_connections.copy().values())
                ):
                    # If this is the broker
                    # There are no more boolean connections
                    if is_landing is None:
                        # If the closed process is the broker process or some other error
                        pass
                    elif is_landing:
                        # If the closed process was a landing page. Exit
                        QApplication.quit()
                    else:
                        # The last process closed was not a landing process so open a landing process
                        subprocess.Popen(
                            [sys.executable, sys.argv[0]],
                            start_new_session=True,
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )

        socket.disconnected.connect(on_disconnect)


_remote_call_listener.newConnection.connect(_on_listener_connect)


class RemoteProcedureCallingConnection:
    """A subclass of QLocalSocket to facilitate calling a procedure in a remote process and getting the return value."""

    def __init__(self, socket: QLocalSocket = None):
        self.socket = socket or QLocalSocket()
        # A dictionary mapping the UUID for the call to the callback functions.
        self._calls: CallDataStorage = {}
        self.socket.readyRead.connect(self._process_msg)

    def has_pending_calls(self) -> bool:
        """Have calls been sent but a response is still pending."""
        return bool(self._calls)

    def pending_calls(self) -> CallDataStorage:
        """The data for all calls whose response is still pending."""
        return self._calls.copy()

    def call(
        self,
        success_callback: SuccessCallbackT,
        error_callback: ErrorCallbackT,
        func: Callable,
        *args,
        **kwargs,
    ):
        """
        Call a function in the connected process.

        :param func: The function to call in the remote process. This must be a static function.
        :param args: The arguments to pass to the remote function (Must be pickleable)
        :param kwargs: The keyword arguments to pass to the remote function (Must be pickleable)
        :param success_callback: A function to call with the return value.
        :param error_callback: A function to call if the remote function raises an exception.
        :return:
        """
        if self.socket.state() != QLocalSocket.LocalSocketState.ConnectedState:
            raise RuntimeError("Socket is not connected")
        identifier = str(uuid4()).encode()
        address = _get_func_address(func)
        log.debug(
            f"Calling remote function {address}(*{args}, **{kwargs}) {identifier.decode()}"
        )
        self._calls[identifier] = (
            (address, args, kwargs),
            (success_callback, error_callback),
        )
        payload = self.encode_request(identifier, address, args, kwargs)
        self.socket.write(payload)

    def _process_msg(self):
        with DisplayException(
            "Exception processing remote procedure call.", suppress=True, log=log
        ):
            while self.socket.bytesAvailable():
                # It is possible for there to be more than one payload here.
                # readyRead will only be re-emitted when the buffer is empty.
                with DisplayException(
                    "Exception processing remote procedure call.",
                    suppress=True,
                    log=log,
                ):
                    payload_length_data = self.socket.read(4).data()
                    if len(payload_length_data) != 4:
                        raise RuntimeError("Error in data sent over socket.")
                    payload_length = struct.unpack(">I", payload_length_data)[0]
                    payload = self.socket.read(payload_length).data()
                    if len(payload) != payload_length:
                        raise RuntimeError("Error in data sent over socket.")
                    identifier, is_response, payload = (
                        payload[:36],
                        payload[36],
                        payload[37:],
                    )
                    if is_response:
                        log.debug(f"New response from {self.socket} {identifier}")
                        _, (success_callback, error_callback) = self._calls.pop(
                            identifier
                        )

                        is_success, response = pickle.loads(payload)

                        if is_success:
                            log.debug(
                                "Response was a success. Calling success callback."
                            )
                            success_callback(response)
                        else:
                            log.debug("Response was an error. Calling error callback.")
                            error_callback(response)
                    else:
                        log.debug(f"New request from {self.socket}")

                        try:
                            address, args, kwargs = pickle.loads(payload)
                            func = _remote_functions.get(address, None)
                            if func is None:
                                raise Exception(f"Could not find function {address}")

                            log.debug(
                                f"Calling function {address}(*{args}, **{kwargs}) as requested by {self.socket} {identifier.decode()}"
                            )
                            response = func(*args, **kwargs)
                            log.debug(f"Sending response back to caller. {response}")
                            payload = self.encode_success_response(identifier, response)
                            self.socket.write(payload)

                        except Exception:
                            log.debug(f"Exception processing request {identifier}")
                            payload = self.encode_error_response(
                                identifier, traceback.format_exc()
                            )
                            self.socket.write(payload)

    @staticmethod
    def _add_size(payload: bytes) -> bytes:
        payload_size = len(payload)
        return struct.pack(">I", payload_size) + payload

    @classmethod
    def encode_request(cls, identifier: bytes, address: str, args, kwargs):
        """
        Encode an RPC request.

        :param identifier: A UUID4 string unique to this call.
        :param address: The address of the function to call.
        :param args: The arguments to pass to the function.
        :param kwargs: The keyword arguments to pass to the function.
        :return: The encoded bytes object
        """

        return cls._add_size(
            identifier + b"\x00" + pickle.dumps((address, args, kwargs))
        )

    @classmethod
    def encode_success_response(cls, identifier: bytes, response: Any) -> bytes:
        return cls._add_size(identifier + b"\x01" + pickle.dumps((True, response)))

    @classmethod
    def encode_error_response(cls, identifier: bytes, msg: str) -> bytes:
        return cls._add_size(identifier + b"\x01" + pickle.dumps((False, msg)))


_broker_connection = RemoteProcedureCallingConnection()


def init_rpc(broker=False):
    """Init the messaging state"""
    global _is_broker
    log.debug("Initialising RPC.")
    _is_broker = bool(broker)
    failed_connections = 0

    address = BrokerAddress if _is_broker else server_uuid
    log.debug(f"Connecting listener to address {address}")
    if not _remote_call_listener.listen(address):
        msg = _remote_call_listener.errorString()
        log.exception(msg)
        if _is_broker:
            sys.exit()
        else:
            raise Exception(msg)

    def on_connect():
        with DisplayException("Error on socket connect", suppress=True, log=log):
            nonlocal failed_connections
            failed_connections = 0
            log.debug("Connected to broker process.")

            if _is_broker:

                def on_success_response(result):
                    if result == server_uuid:
                        log.debug("I am the broker")
                        _broker_connection.socket.close()
                    else:
                        log.debug("Exiting because a broker already exists.")
                        QApplication.quit()

                def on_error_response(tb_str):
                    log.exception(tb_str)
                    display_exception(
                        title="Broker exception",
                        error="Broker exception",
                        traceback=tb_str,
                    )

                _broker_connection.call(
                    on_success_response, on_error_response, get_server_uuid
                )

    def on_error():
        with DisplayException(
            "Error on socket connection error", suppress=True, log=log
        ):
            nonlocal failed_connections
            if _is_broker:
                err = _broker_connection.socket.errorString()
                log.critical(err)
                display_exception(
                    title="Could not connect to broker from broker.",
                    error="Could not connect to broker from broker.",
                    traceback=err,
                )
            else:
                failed_connections += 1
                if failed_connections > 20:
                    display_exception(
                        title="Failed to connect to the broker process.",
                        error="Failed to connect to the broker process.",
                        traceback=f"Please report this to a developer with the log files found in {logging_directory()}",
                    )
                    log.error("Gave up connecting to the broker")
                    return
                log.debug(
                    "Error connecting to broker process. Initialising broker process."
                )
                # If it could not connect, try booting the broker process and try again.
                # TODO: pass in logging arguments.
                # TODO: Make this work for PyInstaller builds.
                spawn_process(BROKER)
                # Give the broker a chance to load
                QTimer.singleShot(
                    1000,
                    lambda: _broker_connection.socket.connectToServer(BrokerAddress),
                )

    log.debug("Connecting to broker.")
    _broker_connection.socket.connected.connect(on_connect)
    _broker_connection.socket.errorOccurred.connect(on_error)
    _broker_connection.socket.connectToServer(BrokerAddress)
