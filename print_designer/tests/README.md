# Print Designer Test System

This document explains the reorganized Print Designer test system following ERPNext standards from `Documentation/rules.md`.

## Test Structure

Following the ERPNext pattern from `apps/erpnext/erpnext/tests/`, all tests are organized in:

```
print_designer/print_designer/tests/
├── __init__.py                           # Global test dependencies
├── README.md                            # This documentation
├── test_init.py                         # Main initialization tests (ERPNext pattern)
├── test_print_format_export_import.py   # Export/Import functionality tests
├── utils.py                             # Test utilities and helpers
├── test_company_preview.py              # Existing company preview tests
├── test_company_tab_installation.py     # Existing installation tests
└── test_watermark_system.py             # Existing watermark tests
```

## Test Categories

### 1. Core Framework Tests (`test_init.py`)
- App installation verification
- Hook system validation
- DocType installation checks
- Custom field validation
- PDF generator availability
- API endpoint accessibility

### 2. Feature-Specific Tests
- **Export/Import**: `test_print_format_export_import.py` - Comprehensive test for backup/restore functionality
- **Company Preview**: `test_company_preview.py` - Company logo and branding tests
- **Watermark System**: `test_watermark_system.py` - Watermark functionality tests
- **Installation**: `test_company_tab_installation.py` - Field installation tests

### 3. Test Utilities (`utils.py`)
Helper functions for creating test data:
- `create_test_print_format()` - Create test Print Designer formats
- `create_test_digital_signature()` - Create test signatures
- `create_test_company_stamp()` - Create test stamps
- `cleanup_test_data()` - Clean up after tests
- `PrintDesignerTestCase` - Base test class with common setup

## Running Tests

### Individual Test Methods
```bash
# Run specific test method (RECOMMENDED)
bench run-tests --module print_designer.tests.test_print_format_export_import.TestPrintFormatExportImport.test_export_print_format_success
```

### Test Files
```bash
# Run entire test file
bench run-tests --module print_designer.tests.test_init
bench run-tests --module print_designer.tests.test_print_format_export_import
```

### App-wide Tests
```bash
# Run all Print Designer tests (slower)
bench run-tests --app print_designer
```

### With Coverage
```bash
bench run-tests --module print_designer.tests.test_init --coverage
```

## Test Dependencies

Global test dependencies are defined in `__init__.py`:
- User
- Company 
- Item
- Print Format
- Digital Signature
- Company Stamp

## Test Data Management

### Using Test Utilities
```python
from print_designer.tests.utils import PrintDesignerTestCase

class TestMyFeature(PrintDesignerTestCase):
    def test_something(self):
        # Create test print format
        print_format = self.create_test_print_format(
            name="My Test Format",
            doctype="Sales Invoice"
        )
        
        # Test your functionality
        # ...
        
        # Cleanup is handled automatically by base class
```

### Manual Data Management
```python
from print_designer.tests.utils import cleanup_test_data

# After tests
cleanup_test_data(
    print_formats=["Test Format 1", "Test Format 2"],
    signatures=["Test Signature"],
    stamps=["Test Stamp"]
)
```

## Best Practices

### Test Naming
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Test Organization
1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **Feature Tests**: Test complete user workflows

### Test Data
- Create minimal test data needed for each test
- Use setUp/tearDown for test-specific data
- Use setUpClass/tearDownClass for expensive shared data
- Always clean up test data

### Assertions
- Use descriptive assertion messages
- Test both success and failure cases
- Use subTests for testing multiple similar scenarios

## Migration from Old Test Structure

The following test files were scattered throughout the app and should be migrated to the standard structure:

### Currently Scattered Tests
- Root level: `test_*.py` files should be moved to `print_designer/tests/`
- Command tests: `commands/test_*.py` should integrate with main test suite
- Utility tests: `utils/test_*.py` should integrate with main test suite
- API tests: `api/test_*.py` should integrate with main test suite

### Migration Steps
1. Review existing test files for useful test cases
2. Integrate valuable tests into the new structure
3. Remove duplicate or obsolete test files
4. Update imports and references
5. Ensure all tests pass in the new structure

## Custom Field Testing

Following `Documentation/rules.md`, Print Designer custom fields should use `pd_custom_` prefix:

### Current Status
Many existing custom fields don't follow the naming convention:
- `subject_to_wht` → should be `pd_custom_subject_to_wht`
- `wht_income_type` → should be `pd_custom_wht_income_type`
- `net_total_after_wht` → should be `pd_custom_net_total_after_wht`

### Testing Custom Fields
```python
def test_custom_fields_naming_convention(self):
    """Test that all Print Designer custom fields follow pd_custom_ convention"""
    custom_fields = frappe.get_all("Custom Field", 
        filters={"module": "Print Designer"}, 
        fields=["fieldname", "dt"]
    )
    
    for field in custom_fields:
        self.assertTrue(
            field.fieldname.startswith("pd_custom_"),
            f"Field {field.fieldname} in {field.dt} doesn't follow pd_custom_ convention"
        )
```

## Future Improvements

1. **Performance Tests**: Add performance benchmarks for PDF generation
2. **Visual Tests**: Add visual regression tests for print outputs
3. **Integration Tests**: Test with different ERPNext versions
4. **Load Tests**: Test with large datasets and concurrent users
5. **Security Tests**: Test permission systems and data access

## Documentation References

- [Frappe Testing Documentation](https://docs.frappe.io/framework/user/en/testing)
- [Unit Testing Guide](https://docs.frappe.io/framework/user/en/guides/automated-testing/unit-testing)
- [ERPNext Custom Field Guidelines](Documentation/rules.md)
- [Print Designer CLAUDE.md](CLAUDE.md) - Development guidelines