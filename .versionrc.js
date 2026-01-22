/**
 * standard-version configuration for print_designer
 * Automatically syncs version across package.json and Python __init__.py
 */

module.exports = {
  types: [
    { type: 'feat', section: '✨ Features' },
    { type: 'fix', section: '🐛 Bug Fixes' },
    { type: 'chore', section: '🔧 Maintenance', hidden: false },
    { type: 'docs', section: '📚 Documentation' },
    { type: 'ci', section: '👷 CI/CD' },
    { type: 'refactor', section: '♻️ Refactoring' },
    { type: 'perf', section: '⚡ Performance' },
    { type: 'test', section: '🧪 Tests' }
  ],
  bumpFiles: [
    { filename: 'package.json', type: 'json' },
    {
      filename: 'print_designer/__init__.py',
      updater: './scripts/python-version-updater.js'
    }
  ],
  tagPrefix: 'v',
  commitUrlFormat: 'https://github.com/ManotLuijiu/print_designer/commit/{{hash}}',
  compareUrlFormat: 'https://github.com/ManotLuijiu/print_designer/compare/{{previousTag}}...{{currentTag}}'
};
