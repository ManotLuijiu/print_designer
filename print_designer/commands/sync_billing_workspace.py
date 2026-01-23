"""
Sync Billing Workspace from JSON to Database

This module ensures the Billing workspace is properly synced to the database
with all its links, shortcuts, and content.

Based on workspace_knowledge.md - uses delete + reinsert pattern.
"""

import frappe
import json
import os


def sync_billing_workspace():
    """
    Sync the Billing workspace from JSON file to database.

    Uses delete + reinsert pattern as workspaces don't auto-update on migrate.
    """
    workspace_name = "Billing"

    # Get the workspace JSON path
    app_path = frappe.get_app_path("print_designer")
    ws_json_path = os.path.join(
        app_path, "print_designer", "workspace", "billing", "billing.json"
    )

    if not os.path.exists(ws_json_path):
        print(f"   ⚠️  Billing workspace JSON not found at {ws_json_path}")
        return False

    try:
        # Read the workspace JSON
        with open(ws_json_path, "r") as f:
            ws_data = json.load(f)

        # Delete existing workspace and child tables
        if frappe.db.exists("Workspace", workspace_name):
            print(f"   🗑️  Removing existing {workspace_name} workspace...")
            frappe.db.delete("Workspace", {"name": workspace_name})
            frappe.db.delete("Workspace Link", {"parent": workspace_name})
            frappe.db.delete("Workspace Shortcut", {"parent": workspace_name})
            frappe.db.delete("Workspace Chart", {"parent": workspace_name})
            frappe.db.delete("Workspace Number Card", {"parent": workspace_name})
            frappe.db.delete("Workspace Custom Block", {"parent": workspace_name})
            frappe.db.delete("Workspace Quick List", {"parent": workspace_name})
            frappe.db.commit()

        # Insert fresh workspace from JSON
        print(f"   ✨ Creating {workspace_name} workspace from JSON...")
        doc = frappe.get_doc(ws_data)
        doc.flags.ignore_permissions = True
        doc.flags.ignore_links = True
        doc.insert(ignore_permissions=True)

        frappe.db.commit()

        # Clear all workspace-related caches
        frappe.clear_cache()
        frappe.cache().delete_key("workspace_sidebar_items")

        print(f"   ✅ {workspace_name} workspace synced successfully!")
        print(f"      - Links: {len(ws_data.get('links', []))}")
        print(f"      - Shortcuts: {len(ws_data.get('shortcuts', []))}")

        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"   ❌ Error syncing {workspace_name} workspace: {str(e)}")
        frappe.log_error(f"Billing Workspace Sync Error: {str(e)}")
        return False


def execute():
    """Execute function for after_migrate hook."""
    print("🔄 Syncing Billing workspace...")
    sync_billing_workspace()


def remove_billing_workspace():
    """
    Remove the Billing workspace from database on uninstall.
    """
    workspace_name = "Billing"

    try:
        if frappe.db.exists("Workspace", workspace_name):
            print(f"   🗑️  Removing {workspace_name} workspace...")
            frappe.db.delete("Workspace", {"name": workspace_name})
            frappe.db.delete("Workspace Link", {"parent": workspace_name})
            frappe.db.delete("Workspace Shortcut", {"parent": workspace_name})
            frappe.db.delete("Workspace Chart", {"parent": workspace_name})
            frappe.db.delete("Workspace Number Card", {"parent": workspace_name})
            frappe.db.delete("Workspace Custom Block", {"parent": workspace_name})
            frappe.db.delete("Workspace Quick List", {"parent": workspace_name})
            frappe.db.commit()
            print(f"   ✅ {workspace_name} workspace removed successfully!")
        else:
            print(f"   ℹ️  {workspace_name} workspace not found, skipping removal.")

        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"   ❌ Error removing {workspace_name} workspace: {str(e)}")
        return False


if __name__ == "__main__":
    execute()
