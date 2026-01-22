/**
 * Custom version updater for Python __init__.py files
 * Used by standard-version to sync version in print_designer/__init__.py
 */

const versionRegex = /__version__ = ['"]([^'"]+)['"]/;

module.exports.readVersion = function (contents) {
  const match = contents.match(versionRegex);
  return match ? match[1] : '0.0.0';
};

module.exports.writeVersion = function (contents, version) {
  return contents.replace(versionRegex, `__version__ = "${version}"`);
};
