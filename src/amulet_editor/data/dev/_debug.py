def enable_trace():
    """
    Enable debugging support.
    This must be called to allow debugging python function run in a QThreadPool.
    """
    try:
        # This enables debugging in PyCharm
        from _pydev_bundle.pydev_monkey_qt import set_trace_in_qt

        set_trace_in_qt()
    except Exception:
        pass
