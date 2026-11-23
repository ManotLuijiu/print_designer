# Translation System Integration Roadmap

## TODO: Future translation_tools Integration

### Current State
- ✅ Account Name translations ready in `utils/account_glossary.py` (88 translations, 100% coverage)
- ✅ Custom field `account_name_th` installed and visible in list view
- ⏳ Need simple way to apply translations to existing accounts

### Future Enhancement: translation_tools Integration
**Priority:** Medium (after core functionality works)
**Effort:** 1-2 weeks

#### Proposed Hybrid Architecture:
```
translation_tools (existing) + Field Translation Extension
├── Translation Glossary Term (reuse existing)
├── Field Translation Manager (NEW)
├── DocType Field Integration (NEW)
├── Bulk Field Update API (NEW)
└── GitHub Integration (enhance existing)
```

#### Benefits When Implemented:
- 🎯 Single Translation Dashboard for all translations
- 🤖 AI-Powered translation suggestions for new accounts
- 📊 Unified reporting (app translations + field translations)
- 🔄 Collaborative GitHub workflow
- ✅ Approval workflow for translation quality
- 📈 Scalable to other DocTypes (Customer, Item, etc.)

#### Implementation Phases:
1. **Phase 1:** Extend Translation Glossary Term with field-specific metadata
2. **Phase 2:** Create Field Translation Manager for bulk field updates
3. **Phase 3:** Integrate with existing GitHub workflow
4. **Phase 4:** Add UI integration to translation dashboard

#### Files to Modify (Future):
- `translation_tools/api/field_translation.py` (NEW)
- `translation_tools/doctype/translation_glossary_term/` (extend)
- Translation dashboard integration

### Current Priority: Basic Field Population
For now, focus on simple approach to populate `account_name_th` field from existing glossary.