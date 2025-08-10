# Designation Signature Sync System

## 🎯 Overview

This system enables comprehensive signature management across your organization by syncing signatures between **Designation**, **Employee**, and **User** DocTypes. It provides role-based signature management where employees can inherit signatures from their designations.

## ✨ Features

### 🏢 Designation-Level Signatures
- **Designation Signature**: Upload signature image for each role/position
- **Signature Authority Level**: Set approval authority (None/Low/Medium/High/Executive)
- **Maximum Approval Amount**: Set spending limits for signature authority
- **Automatic Inheritance**: Employees inherit designation signatures when personal signatures are missing

### 🔄 Smart Signature Sync
- **Priority Hierarchy**: Employee Signature → User Signature → Designation Signature
- **Automatic Propagation**: Signatures sync across related DocTypes
- **Coverage Tracking**: Monitor signature coverage across your organization
- **Bulk Operations**: Upload multiple designation signatures at once

### 📊 Management Dashboard
- **Coverage Reports**: See signature coverage percentages by designation
- **Sync Status**: Real-time status of signature synchronization
- **Employee Tracking**: Track which employees have signatures
- **Authority Management**: Manage approval limits and authority levels

## 🚀 Quick Setup

### Step 1: Run Setup Script
```bash
cd /home/frappe/frappe-bench/apps/print_designer
python3 setup_designation_signatures.py
```

**OR** use the API method:
```javascript
frappe.call({
    method: 'print_designer.api.designation_signature_sync.setup_designation_signature_sync',
    callback: (r) => console.log(r.message)
});
```

### Step 2: Configure Designations
1. Go to **Designation** DocType: http://erpnext-dev-server.bunchee.online:8000/app/designation
2. Open each designation (Consultant, Manager, etc.)
3. Upload signature image to **"Designation Signature"** field
4. Set **"Signature Authority Level"** (Low/Medium/High/Executive)
5. Set **"Maximum Approval Amount"** for spending limits

### Step 3: Sync Signatures
Run the sync to propagate signatures to employees:
```javascript
frappe.call({
    method: 'print_designer.api.designation_signature_sync.sync_designation_signatures',
    callback: (r) => console.log('Sync result:', r.message)
});
```

## 🎨 User Interface Features

### Enhanced Designation Form
When you open any Designation record, you'll see:

#### ✅ Signature Status Display
- **Designation Signature**: Upload status and preview
- **Authority Level**: Current authority level setting
- **Employee Coverage**: Shows how many employees have signatures

#### 🔧 Signature Management Buttons
- **Sync Signatures**: Manually trigger signature sync
- **Signature Report**: View comprehensive coverage report  
- **View Employee Signatures**: Jump to related employees
- **Bulk Upload**: Upload multiple signatures at once

#### 📊 Real-time Coverage Tracking
- Employee coverage percentage
- Total employees vs. employees with signatures
- Authority level and approval limits

## 🔄 How Signature Sync Works

### Priority Order
1. **Employee Signature** (highest priority)
2. **User Signature** (medium priority)  
3. **Designation Signature** (fallback)

### Sync Logic
```
IF Employee has signature:
    Use Employee signature
ELSE IF User has signature:
    Use User signature  
ELSE IF Designation has signature:
    Use Designation signature
ELSE:
    No signature available
```

### Auto-Population
When creating documents with signature fields, the system automatically:
1. Checks if document has employee/user/designation fields
2. Looks up signature hierarchy for that person
3. Populates empty signature fields with best available signature

## 🛠️ API Reference

### Core Functions

#### 1. Setup System
```javascript
frappe.call({
    method: 'print_designer.api.designation_signature_sync.setup_designation_signature_sync'
});
```

#### 2. Sync Signatures
```javascript
frappe.call({
    method: 'print_designer.api.designation_signature_sync.sync_designation_signatures'
});
```

#### 3. Get Signature Hierarchy
```javascript
frappe.call({
    method: 'print_designer.api.designation_signature_sync.get_signature_hierarchy',
    args: {
        employee_name: 'EMP-001'  // or user_id or designation
    }
});
```

#### 4. Coverage Report
```javascript
frappe.call({
    method: 'print_designer.api.designation_signature_sync.get_designation_signature_report'
});
```

#### 5. Bulk Update
```javascript
frappe.call({
    method: 'print_designer.api.designation_signature_sync.bulk_update_designation_signatures',
    args: {
        designation_mappings: JSON.stringify([
            {
                designation: 'Consultant',
                signature_url: '/files/consultant_signature.png',
                authority_level: 'Medium',
                max_approval_amount: 50000
            }
        ])
    }
});
```

## 📋 Usage Examples

### Example 1: Setup for "Consultant" Designation
1. Go to: http://erpnext-dev-server.bunchee.online:8000/app/designation/Consultant
2. Upload signature image
3. Set Authority Level: "Medium"
4. Set Max Approval Amount: $50,000
5. Click "Sync Signatures" button

### Example 2: Bulk Upload Multiple Signatures
```javascript
// Prepare signature mappings
let signatures = [
    {
        designation: 'Consultant',
        signature_url: '/files/signatures/consultant.png',
        authority_level: 'Medium',
        max_approval_amount: 50000
    },
    {
        designation: 'Senior Consultant', 
        signature_url: '/files/signatures/senior_consultant.png',
        authority_level: 'High',
        max_approval_amount: 100000
    },
    {
        designation: 'Manager',
        signature_url: '/files/signatures/manager.png', 
        authority_level: 'High',
        max_approval_amount: 200000
    },
    {
        designation: 'Director',
        signature_url: '/files/signatures/director.png',
        authority_level: 'Executive', 
        max_approval_amount: 500000
    }
];

// Execute bulk update
frappe.call({
    method: 'print_designer.api.designation_signature_sync.bulk_update_designation_signatures',
    args: {
        designation_mappings: JSON.stringify(signatures)
    },
    callback: (r) => {
        console.log(`Updated ${r.message.updated_count} designations`);
    }
});
```

### Example 3: Generate Coverage Report
```javascript
frappe.call({
    method: 'print_designer.api.designation_signature_sync.get_designation_signature_report',
    callback: (r) => {
        let report = r.message;
        console.log(`Coverage: ${report.summary.coverage_percentage}%`);
        console.log(`Designations with signatures: ${report.summary.designations_with_signatures}/${report.summary.total_designations}`);
    }
});
```

## 🔧 Troubleshooting

### Issue: Signatures Not Syncing
**Solution**:
```bash
# 1. Check if designation fields are installed
bench --site [site] execute print_designer.api.signature_field_installer.check_signature_fields_status

# 2. Manual sync
bench --site [site] execute print_designer.api.designation_signature_sync.sync_designation_signatures

# 3. Clear cache
bench --site [site] clear-cache
```

### Issue: Designation Fields Missing
**Solution**:
```bash
# Install designation signature fields
bench --site [site] execute print_designer.api.signature_field_installer.install_signature_fields_for_doctype --kwargs '{"doctype": "Designation"}'
```

### Issue: Client Script Not Loading
**Solution**:
1. Clear browser cache (Ctrl+F5)
2. Check browser console for JavaScript errors
3. Verify client script is properly installed

## 🎯 Best Practices

### 1. Signature Organization
- **Consistent Format**: Use same image format (PNG recommended)
- **Proper Size**: Keep signatures reasonably sized (200x100px ideal)
- **Transparent Background**: Use transparent PNG for better integration

### 2. Authority Levels
- **Low**: Junior staff, small approvals (<$10K)
- **Medium**: Middle management, moderate approvals ($10K-$50K)
- **High**: Senior management, large approvals ($50K-$200K)  
- **Executive**: C-level, unlimited or very high approvals (>$200K)

### 3. Regular Maintenance
- **Weekly Sync**: Run signature sync weekly
- **Monthly Reports**: Generate coverage reports monthly
- **Quarterly Review**: Review authority levels and approval limits quarterly

### 4. Security Considerations
- **Role Permissions**: Ensure only HR/Admin can modify designation signatures
- **Audit Trail**: Monitor signature changes through Frappe's audit logs
- **Backup**: Regular backup of signature files

## 📈 Benefits

### For HR/Admin
- **Centralized Management**: Manage signatures at designation level
- **Automatic Inheritance**: Employees inherit role-based signatures
- **Coverage Tracking**: Monitor signature adoption across organization

### For Employees
- **Automatic Population**: Signatures auto-populate in documents
- **Hierarchy Fallback**: Always have a signature available through designation
- **Consistent Branding**: Organization-wide signature consistency

### For Management
- **Authority Control**: Set approval limits by role
- **Audit Trail**: Track signature usage and approvals
- **Scalability**: Easy to add new roles and signatures

## 🚀 Next Steps

1. **Complete Setup**: Run setup script and configure all designations
2. **Train Users**: Show employees how signatures work in documents
3. **Monitor Coverage**: Use reports to track signature adoption
4. **Integrate Workflows**: Use signatures in approval workflows
5. **Custom Enhancement**: Add signature requirements to custom DocTypes

This system provides a robust foundation for organization-wide signature management that scales with your business needs!