import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import launcher


class LauncherTests(unittest.TestCase):
    @patch.dict(os.environ, {"OFN_HOST": "127.0.0.2", "OFN_PORT": "6789"})
    @patch("launcher.threading.Timer")
    @patch("launcher.create_server")
    def test_starts_server_and_opens_browser(self, create_server, timer):
        server = MagicMock()
        server.run.side_effect = KeyboardInterrupt
        create_server.return_value = server

        launcher.main()

        create_server.assert_called_once_with(
            launcher.app, host="127.0.0.2", port=6789, threads=4
        )
        timer.assert_called_once_with(
            0.5, launcher.webbrowser.open, args=("http://127.0.0.2:6789",)
        )
        timer.return_value.start.assert_called_once_with()
        server.run.assert_called_once_with()
        server.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
