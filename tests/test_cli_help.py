import io
import sys
import unittest
from unittest import mock
import importlib.util
from pathlib import Path

import track
import report
import preview_category

def load_generator():
    path = Path(__file__).resolve().parents[1] / "scripts" / "generate_demo_data.py"
    spec = importlib.util.spec_from_file_location("generate_demo_data", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class TestCleanHelpExecution(unittest.TestCase):
    
    def test_track_help_executes_without_error(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        
        with (
            mock.patch("sys.argv", ["track.py", "--help"]),
            mock.patch("sys.stdout", stdout),
            mock.patch("sys.stderr", stderr),
            mock.patch("track.WindowsActivityProvider") as provider,
            mock.patch("track.ActivityDatabase") as database,
            mock.patch("track.ActivityTracker") as tracker,
        ):
            with self.assertRaises(SystemExit) as raised:
                track.main()
                
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue().lower()
        self.assertIn("usage", output)
        self.assertIn("--database", output)
        self.assertIn("--interval", output)
        
        provider.assert_not_called()
        database.assert_not_called()
        tracker.assert_not_called()

    def test_report_help_executes_without_error(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        
        with (
            mock.patch("sys.argv", ["report.py", "--help"]),
            mock.patch("sys.stdout", stdout),
            mock.patch("sys.stderr", stderr),
            mock.patch("report.load_categorizer") as load_cat,
            mock.patch("report.generate_report") as gen_rep,
        ):
            with self.assertRaises(SystemExit) as raised:
                report.main()
                
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue().lower()
        self.assertIn("usage", output)
        self.assertIn("--date", output)
        self.assertIn("--from", output)
        self.assertIn("--to", output)
        self.assertIn("--output", output)
        
        load_cat.assert_not_called()
        gen_rep.assert_not_called()

    def test_preview_category_help_ignores_missing_args(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        
        with (
            mock.patch("sys.stdout", stdout),
            mock.patch("sys.stderr", stderr),
            mock.patch("preview_category.load_categorizer") as load_cat,
        ):
            with self.assertRaises(SystemExit) as raised:
                preview_category.main(["--help"])
                
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        
        output = stdout.getvalue().lower()
        self.assertIn("usage", output)
        self.assertIn("--config", output)
        self.assertIn("--application", output)
        
        load_cat.assert_not_called()

    def test_generate_demo_data_help_ignores_missing_args(self):
        generator_module = load_generator()
        
        stdout = io.StringIO()
        stderr = io.StringIO()
        
        with (
            mock.patch("sys.stdout", stdout),
            mock.patch("sys.stderr", stderr),
            mock.patch.object(generator_module, "generate_demo_database") as mock_generate,
            mock.patch.object(generator_module, "ActivityDatabase") as mock_db,
        ):
            with self.assertRaises(SystemExit) as raised:
                generator_module.main(["--help"])
                
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        
        output = stdout.getvalue().lower()
        self.assertIn("usage", output)
        self.assertIn("--output", output)
        
        mock_generate.assert_not_called()
        mock_db.assert_not_called()