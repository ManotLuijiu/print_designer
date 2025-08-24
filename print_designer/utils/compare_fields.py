import frappe
import json
import os

def compare_quotation_fields():
    """Compare Quotation custom fields between database and fixtures"""
    print("=== DATABASE vs FIXTURES COMPARISON ===")
    
    # Get database fields
    db_fields = frappe.get_all(
        "Custom Field",
        filters={"dt": "Quotation"},
        fields=["fieldname", "fieldtype", "label", "insert_after", "depends_on", "default", "options"],
        order_by="idx asc, modified asc"
    )
    
    print(f"Database fields: {len(db_fields)}")
    
    # Load fixtures file
    fixtures_path = frappe.get_app_path("print_designer", "fixtures", "custom_field.json")
    
    try:
        with open(fixtures_path, "r") as f:
            fixture_data = json.load(f)
        
        # Filter for Quotation fields only
        fixture_fields = [field for field in fixture_data if field.get("dt") == "Quotation"]
        print(f"Fixture fields: {len(fixture_fields)}")
        
        # Create name sets
        db_names = {field['fieldname'] for field in db_fields}
        fixture_names = {field['fieldname'] for field in fixture_fields}
        
        # Find differences
        missing_in_db = fixture_names - db_names
        missing_in_fixtures = db_names - fixture_names
        common_fields = db_names & fixture_names
        
        print(f"\nCommon fields: {len(common_fields)}")
        print(f"Missing in Database: {len(missing_in_db)}")
        print(f"Missing in Fixtures: {len(missing_in_fixtures)}")
        
        if missing_in_db:
            print(f"\nFields in fixtures but NOT in database:")
            for field in sorted(missing_in_db):
                print(f"  ❌ {field}")
        
        if missing_in_fixtures:
            print(f"\nFields in database but NOT in fixtures:")
            for field in sorted(missing_in_fixtures):
                print(f"  ⚠️  {field}")
        
        # Create lookup for property comparison
        db_lookup = {field['fieldname']: field for field in db_fields}
        fixture_lookup = {field['fieldname']: field for field in fixture_fields}
        
        print(f"\n=== PROPERTY DIFFERENCES ===")
        differences_found = False
        for fieldname in sorted(common_fields):
            db_field = db_lookup[fieldname]
            fixture_field = fixture_lookup[fieldname]
            
            # Compare key properties
            key_props = ['fieldtype', 'label', 'insert_after', 'depends_on', 'default']
            field_diffs = []
            
            for prop in key_props:
                db_val = db_field.get(prop)
                fixture_val = fixture_field.get(prop)
                if db_val != fixture_val:
                    field_diffs.append(f"{prop}: DB='{db_val}' <-> FIX='{fixture_val}'")
            
            if field_diffs:
                differences_found = True
                print(f"\n⚠️  {fieldname}:")
                for diff in field_diffs:
                    print(f"    {diff}")
        
        if not differences_found:
            print("✅ All common fields have matching properties!")
        
        print(f"\n=== CURRENT FIELD ORDER (Database) ===")
        for i, field in enumerate(db_fields, 1):
            depends = f" | depends: {field['depends_on'][:50]}..." if field['depends_on'] and len(field['depends_on']) > 50 else f" | depends: {field['depends_on']}" if field['depends_on'] else ""
            print(f"{i:2d}. {field['fieldname']:<35} | {field['fieldtype']:<15} | after: {field['insert_after']}{depends}")
        
        return {
            'db_fields': db_fields,
            'fixture_fields': fixture_fields,
            'missing_in_db': missing_in_db,
            'missing_in_fixtures': missing_in_fixtures,
            'common_fields': common_fields,
            'differences_found': differences_found
        }
            
    except Exception as e:
        print(f"Error: {e}")
        return None