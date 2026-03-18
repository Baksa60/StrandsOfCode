class ConversionCancelled(Exception):
    pass


def check_cancelled() -> None:
    from PyQt6.QtCore import QThread

    thread = QThread.currentThread()
    if thread and thread.isInterruptionRequested():
        raise ConversionCancelled()
