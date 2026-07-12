import os
import tempfile
import unittest
from pathlib import Path

from custodian import app_shell
from custodian.config import load_app_env


class AppShellAssetTests(unittest.TestCase):
    def test_entry_point_is_importable_without_pywebview(self) -> None:
        # The module must import cleanly on machines without the app extra
        # installed; pywebview is only imported inside main().
        self.assertTrue(callable(app_shell.main))

    def test_find_web_assets_locates_operating_desk(self) -> None:
        static_root = app_shell.find_web_assets()
        self.assertTrue((static_root / "index.html").is_file())
        self.assertTrue((static_root / "app.js").is_file())
        self.assertTrue((static_root / "styles.css").is_file())


class AppEnvTests(unittest.TestCase):
    def setUp(self) -> None:
        # load_app_env can pull arbitrary keys from a real repo .env, so
        # snapshot the whole environment to keep the suite hermetic.
        self._environ = os.environ.copy()
        self._sentinel = "CUSTODIAN_TEST_APP_ENV"
        os.environ.pop(self._sentinel, None)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._environ)

    def test_load_app_env_reads_app_support_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(f"{self._sentinel}=from-app-support\n", encoding="utf-8")
            load_app_env(env_path)
        self.assertEqual(os.environ.get(self._sentinel), "from-app-support")

    def test_load_app_env_never_overrides_real_environment(self) -> None:
        os.environ[self._sentinel] = "from-environment"
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(f"{self._sentinel}=from-app-support\n", encoding="utf-8")
            load_app_env(env_path)
        self.assertEqual(os.environ.get(self._sentinel), "from-environment")

    def test_load_app_env_tolerates_missing_file(self) -> None:
        load_app_env(Path("/nonexistent/custodian/.env"))
        self.assertIsNone(os.environ.get(self._sentinel))
