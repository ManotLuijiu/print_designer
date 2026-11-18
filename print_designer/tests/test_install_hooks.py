"""Catch stale installation hook references without installing an app or using a DB."""

import ast
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]


def lifecycle_hooks():
    names = {"before_install", "after_install", "after_migrate"}
    result = {}
    tree = ast.parse((APP_ROOT / "print_designer" / "hooks.py").read_text())
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in names:
                value = ast.literal_eval(node.value)
                result[target.id] = [value] if isinstance(value, str) else value
    return result


class TestInstallHooks(unittest.TestCase):
    def test_install_and_migration_hooks_resolve_to_declared_functions(self):
        hooks = lifecycle_hooks()
        self.assertEqual(set(hooks), {"before_install", "after_install", "after_migrate"})
        for event, methods in hooks.items():
            for method in methods:
                with self.subTest(event=event, method=method):
                    module, name = method.rsplit(".", 1)
                    path = APP_ROOT.joinpath(*module.split(".")).with_suffix(".py")
                    if not path.is_file():
                        path = APP_ROOT.joinpath(*module.split("."), "__init__.py")
                    self.assertTrue(path.is_file(), f"Missing hook module: {method}")
                    tree = ast.parse(path.read_text())
                    functions = {
                        node.name for node in tree.body
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    }
                    self.assertIn(name, functions, f"Missing hook function: {method}")

    def test_consolidated_watermark_installers_remain_registered(self):
        hooks = lifecycle_hooks()
        installers = {
            "print_designer.commands.install_print_settings_fields.install_print_settings_fields",
            "print_designer.commands.install_print_format_fields.install_print_format_fields",
        }
        for event in ("after_install", "after_migrate"):
            with self.subTest(event=event):
                self.assertTrue(installers.issubset(hooks[event]))


if __name__ == "__main__":
    unittest.main()
