from datetime import datetime

from PyQt6.QtCore import QThread, pyqtSignal

from utils.cancellation import ConversionCancelled


class ConversionWorker(QThread):
    finished = pyqtSignal(object)
    progress = pyqtSignal(str)

    def __init__(self, controller, options):
        super().__init__()
        self.controller = controller
        self.options = options

    def run(self):
        start_time = datetime.now()

        try:
            result = self.controller.run(self.options)

            end_time = datetime.now()
            duration = end_time - start_time

            if isinstance(result, dict):
                result['output_folder'] = self.options.output_folder
                result['duration'] = duration
                result['success'] = True
            else:
                result = {
                    'data': result,
                    'output_folder': self.options.output_folder,
                    'duration': duration,
                    'success': True
                }

            self.finished.emit(result)

        except ConversionCancelled:
            cancelled_result = {
                'cancelled': True,
                'output_folder': self.options.output_folder,
                'success': False,
                'duration': datetime.now() - start_time
            }
            self.finished.emit(cancelled_result)

        except Exception as e:
            error_result = {
                'error': str(e),
                'output_folder': self.options.output_folder,
                'success': False,
                'duration': datetime.now() - start_time
            }
            self.finished.emit(error_result)
