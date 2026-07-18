# Print Designer Language Toggle

## Goal

Add a Print Format Language toggle to Print Designer's toolbar (`/desk/print-designer/...`) so users can preview how the format looks in different languages while designing.

---

## Context: Two Types of Language Toggles

### 1. UI Language Toggle (Already Exists)

- **Location:** `bunchee-sidebar-controls` in Print Designer
- **Purpose:** Changes interface language (English/Thai/Lao)
- **CSS Classes:** `bunchee-lang-trigger`, `bunchee-lang-label`
- **Data Attribute:** `data-lang`

### 2. Print Format Language (What We Want to Add)

- **Location:** Left toolbar in Print Designer (next to Layer, Grid, Help icons)
- **Purpose:** Changes which language the PDF preview renders in
- **Similar to:** The Language dropdown on `/desk/print/Sales Invoice/BL6907-00001`

---

## Existing Toolbar Structure

```html
<div class="sidebar app-sections toolbar">
  <div class="toolbar-section mt-3">
    <!-- Tools: Mouse, Text, Rectangle, Image, Table, Barcode -->
    
    <!-- Divider -->
    <div class="toolbar-divider"></div>
    
    <!-- Layer, Grid icons -->
    
    <!-- Divider -->
    <div class="toolbar-divider"></div>
    
    <!-- Help button -->
  </div>
</div>
```

---

## Target: Add Language Toggle Here

Insert after Grid icon and before Help button:

```html
<div class="toolbar-divider"></div>

<!-- Language Toggle (NEW) -->
<div class="language-toggle-container">
  <select class="language-select" title="Preview Language">
    <option value="th" selected>ไทย</option>
    <option value="en">English</option>
  </select>
</div>

<div class="toolbar-divider"></div>

<!-- Help button (existing) -->
```

---

## Implementation Plan

### Step 1: Find Where Toolbar is Rendered

Look in Vue components for Print Designer:

- `AppToolbar.vue` or similar
- `components/layout/App*.vue`

### Step 2: Add Language Selector Component

```vue
<template>
  <div class="language-toggle-container">
    <select 
      v-model="previewLanguage" 
      @change="onLanguageChange"
      class="language-select"
      title="Preview Language"
    >
      <option value="th">ไทย</option>
      <option value="en">English</option>
    </select>
  </div>
</template>

<script>
export default {
  data() {
    return {
      previewLanguage: 'th'
    }
  },
  methods: {
    onLanguageChange() {
      // Trigger preview refresh with new language
      this.$emit('language-change', this.previewLanguage)
    }
  }
}
</script>
```

### Step 3: Connect to Preview System

When language changes:

1. Store the selected language
2. Refresh the print preview with `_lang` parameter
3. Show different translations in preview

### Step 4: Show Current Language in Label

- Default to Print Format's `default_print_language`
- Display Thai label: "ไทย" when value is "th"
- Display English label: "English" when value is "en"

---

## Key Difference from UI Language Toggle

| Aspect | UI Language | Print Format Language |
|--------|------------|---------------------|
| **Purpose** | Interface labels | PDF document content |
| **Location** | Right sidebar | Left toolbar |
| **Scope** | Global setting | Per-session |
| **Affects** | UI labels, buttons | Translations in preview |

---

## Related Work

1. **Already Done:** Print preview page (`/desk/print/...`) now respects Print Format's `default_print_language`
2. **Next:** Add toggle to Print Designer for real-time preview in different languages

---

## Debugging Notes

When implementing:

- Check console for `[PD PRINT]` logs
- Verify script loads on `/desk/print-designer/...` page
- Test with Print Format that has `default_print_language = "th"`

---

## Files to Modify

1. `print_designer/public/js/print_designer/components/layout/AppToolbar.vue` (or similar)
2. Add language selector component
3. Connect to store/preview system
