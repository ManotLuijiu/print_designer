"""The assets of the templates of this app.

A template of this app is printed on a site that may not install every app
of the bench.  An asset that is loaded from the assets of another app is
therefore missing on such a site: a font falls back to a font that has no
Thai glyphs, and an image of the form is not shown at all.

The templates of this app load every asset from the path of this app, and
the guard proves that every asset of every source of this app is a file
that this app ships.  The path of the framework is allowed as well,
because the framework is installed on every site.
"""

import re
from pathlib import Path
from urllib.parse import unquote

from frappe.tests.utils import FrappeTestCase

APP_ROOT = Path(__file__).resolve().parents[2]
APP_PATH = APP_ROOT / "print_designer"
PUBLIC_PATH = APP_PATH / "public"

# The extensions of a font file.
FONT_SUFFIXES = (".ttf", ".otf", ".woff", ".woff2", ".eot")

# The sources that may carry a reference to an asset.
SOURCE_SUFFIXES = (".html", ".css", ".scss", ".js", ".py", ".json")

# The parts of the tree that are generated, that belong to another tool
# or that are not a source of the app at runtime.
SKIPPED_PARTS = ("node_modules", "dist", "__pycache__", ".git", "tests")

# The prefix of an asset of this app, and the prefix of an asset of the
# framework, which is installed on every site.
OWN_ASSET_PREFIX = "/assets/print_designer/"
FRAMEWORK_ASSET_PREFIX = "/assets/frappe/"

# The reference to an asset in a font face.  The name of a font file may
# carry a space, so the reference is read from the call of ``url()``.
FONT_URL = re.compile(r"""url\(\s*['"]?(/assets/[^'")]+)['"]?\s*\)""")

# The reference to an asset in any source.  A file name may carry a space,
# so the reference is read up to the quote or the bracket that closes it.
ANY_ASSET = re.compile(r"""["'(](/assets/[^"'()]+)""")

# The block of a font face, with the references it carries.
FONT_FACE = re.compile(r"@font-face\s*\{(.*?)\}", re.DOTALL)
# The prefixes of a line that carries no runtime code.  A reference in a
# comment is a note, not a dependency of the app at runtime.
COMMENT_PREFIXES = ("#", "//", "/*", "*", "<!--", "*/")


class TestTheAssetsOfTheTemplates(FrappeTestCase):
    """Every asset of this app is a file that this app ships."""

    def _sources(self):
        """Every source of the app that may carry an asset reference."""
        for path in sorted(APP_PATH.rglob("*")):
            if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
                continue

            if any(part in SKIPPED_PARTS for part in path.parts):
                continue

            if ".bundle." in path.name:
                continue

            yield path

    def _runtime_text(self, text):
        """The text of a source without its comment lines.

        A reference that is commented out is not loaded by the browser, so
        it is not a dependency of the app on a site.
        """
        lines = []
        for line in text.splitlines():
            if line.strip().startswith(COMMENT_PREFIXES):
                continue
            lines.append(line)
        return "\n".join(lines)

    def _font_references(self):
        """The font references of every source of the app."""
        for path in self._sources():
            text = self._runtime_text(path.read_text(errors="ignore"))

            for block in FONT_FACE.findall(text):
                for match in FONT_URL.finditer(block):
                    yield path, match.group(1)

    def _all_asset_references(self):
        """Every asset reference of every source of the app."""
        for path in self._sources():
            text = self._runtime_text(path.read_text(errors="ignore"))

            for match in ANY_ASSET.finditer(text):
                # A JSON source escapes the quote that closes the reference.
                yield path, match.group(1).rstrip("\\")

    def test_the_app_loads_a_font(self):
        """The guard sees the fonts of the app.

        Without a font the guard would pass without proving anything.
        """
        self.assertTrue(list(self._font_references()))

    def test_no_font_of_the_app_comes_from_another_app(self):
        """A font is loaded from the assets of this app."""
        for path, reference in self._font_references():
            self.assertTrue(
                reference.startswith(OWN_ASSET_PREFIX),
                f"{path.relative_to(APP_ROOT)} loads the font {reference}",
            )

    def test_every_font_of_the_app_is_shipped_by_the_app(self):
        """The file of every font reference exists in this app."""
        for path, reference in self._font_references():
            relative = unquote(reference.removeprefix(OWN_ASSET_PREFIX))

            self.assertTrue(
                relative.lower().endswith(FONT_SUFFIXES),
                f"{path.relative_to(APP_ROOT)} loads {relative}, which is not a font",
            )

            self.assertTrue(
                (PUBLIC_PATH / relative).is_file(),
                f"{path.relative_to(APP_ROOT)} loads {relative}, which this app does not ship",
            )

    def test_no_asset_of_the_app_comes_from_another_app(self):
        """An asset is loaded from the assets of this app or of the framework."""
        for path, reference in self._all_asset_references():
            self.assertTrue(
                reference.startswith(OWN_ASSET_PREFIX)
                or reference.startswith(FRAMEWORK_ASSET_PREFIX),
                f"{path.relative_to(APP_ROOT)} loads the asset {reference}",
            )

    def test_every_asset_of_the_app_is_shipped_by_the_app(self):
        """The file of every asset of this app exists in this app."""
        for path, reference in self._all_asset_references():
            if not reference.startswith(OWN_ASSET_PREFIX):
                continue

            relative = unquote(reference.removeprefix(OWN_ASSET_PREFIX))

            if ".bundle." in relative:
                # The build writes the bundle of a source of the app under a
                # hashed name, and the framework resolves the logical name.
                continue

            self.assertTrue(
                (PUBLIC_PATH / relative).is_file(),
                f"{path.relative_to(APP_ROOT)} loads {relative}, which this app does not ship",
            )
