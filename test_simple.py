import erpnext.setup.install
func = erpnext.setup.install.create_print_setting_custom_fields
print(f"Function module: {func.__module__}")
print(f"Function name: {func.__name__}")
if "print_designer" in func.__module__:
    print("✅ SUCCESS: Function overridden by print_designer")
else:
    print("❌ FAIL: Function not overridden")