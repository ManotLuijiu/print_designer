Before writing code, first explore the project structure,
then invoke the nextjs-doc skill for documentation.

## Print Designer Theme

**CSS Variables (defined in `App.vue` `.main-layout`):**

```css
--primary: #7b4b57;      /* Burgundy/wine color - NOT blue! */
--primary-color: #7b4b57;
```

**IMPORTANT:** Do NOT assume `--primary` is blue (#2490ef) like Frappe default. Print Designer overrides it to burgundy (#7b4b57).

**Toolbar icon colors:**

- Use `white` for active icons (white on burgundy background = visible)
- Use `var(--text-muted)` for inactive icons
- When passing `color` prop to `IconsUse`, use `'white'` when active, `'var(--text-muted)'` otherwise

**CSS files location:** `print_designer/public/css/*.scss`

- `print_designer.bundle.scss` - main wrapper styles
- `global_typography_override.bundle.scss` - Thai font overrides
- `signature_stamp.bundle.scss` - signature/stamp styles
- `watermark.bundle.scss` - watermark settings styles

## Frontend dependency policy

- Treat Vue and Pinia versions as a compatibility pair. Do not upgrade either independently or rely on undeclared versions inherited from Frappe.
- Keep supported versions explicitly pinned in this app package.json. Current verified pair: Vue `3.5.12` and Pinia `2.3.1`.
- Do not perform blanket dependency upgrades. Upgrade one related dependency group at a time and review peer requirements first.
- Any Vue, Pinia, build-tool, or lockfile change must include an updated `yarn.lock`, the frontend dependency regression test, `bench build --app print_designer`, target-site cache clearing, and authenticated Playwright verification of `/desk/print-designer/Receipt`.
- A successful build alone is insufficient. Vue `3.5.12` with inherited Pinia `2.1.7` loaded saved data into Pinia but did not trigger Vue component rerenders, leaving the canvas blank without a runtime exception.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:

   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```

5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**

- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->

## Test Credentials

**Location:** `apps/print_designer/.env`

Contains:

- `SITE_USERNAME`
- `SITE_PASSWORD`

**Note:** Actual credentials are stored in this file - do NOT commit to git or share.

---

## WHT DocType Naming (Tier 2)

### Tier 2.1: Tax Withholding Category — IMPLEMENTED

- **Doc name (ID)** = `category_name_en` — already has full English format (e.g. `Transport 1% (PND3)`)
- **`title_field`** = `category_name` — Thai display (e.g. `ค่าขนส่ง 1% (ภงด.3)`)
- **No uniqueness issues** — 34 records, all `category_name_en` values are unique
- **PND54** — uses `Oversea` as recipient_type in doc name (already in `category_name_en`)
- **Migration** — rename via DB UPDATE, update all cross-links (TWI.tax_withholding_category, TWC.pd_custom_thai_wht_income_type) in same transaction

### Tier 2.2: Thai WHT Income Type — IMPLEMENTING

**Schema changes:**

- Keep `conditions` + `conditions_th` as-is (nuanced details beyond recipient_type)
- Add `recipient_type_th` (Select) — Thai options matching `recipient_type`:
  - `Individual` → `บุคคลธรรมดา`, `Corporation` → `นิติบุคคล`, `Foundation/Association` → `มูลนิธิ/สมาคม`, `Oversea` → `ต่างประเทศ`, `Government` → `รัฐบาล`
- Add `doc_title_th` (Data) — compound Thai display: `{income_category_th} {recipient_type_th} {tax_rate} {form_type_th}`

**Doc name format:** `{income_category} {recipient_type} {tax_rate} {form_type}`

- Example: `Advertising Income Corporation 2 PND53`

**`title_field`** = `doc_title_th` — compound Thai display

e.g. `ค่าโฆษณา นิติบุคคล 2 ภงด.53`

## E2E Testing

### Credentials

Credentials for testing are stored in `print_designer/.env`:

```bash
SITE_URL="https://digisoft-erp.bunchee.online"
SITE_USERNAME="Administrator"
SITE_PASSWORD="manlucha"
```

Load credentials in Python tests:

```python
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/frappe/frappe-bench/apps/print_designer/.env")

site_url = os.getenv("SITE_URL")
username = os.getenv("SITE_USERNAME")
password = os.getenv("SITE_PASSWORD")
```

### Test Location

All E2E tests are in `print_designer/print_designer/tests/`:

```
print_designer/print_designer/tests/
├── test_page_orientation.py       # Page orientation feature tests
├── test_watermark_system.py       # Watermark functionality tests
├── test_company_preview.py        # Company logo/branding tests
└── ...
```

### Running Tests

```bash
# Run specific test
cd /home/frappe/frappe-bench/apps/print_designer
python -m pytest print_designer/tests/test_page_orientation.py -v

# Run all tests
bench run-tests --app print_designer
```

### Test Pattern (Python Playwright)

```python
from playwright.sync_api import sync_playwright
import os
import time
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv(dotenv_path="/home/frappe/frappe-bench/apps/print_designer/.env")
site_url = os.getenv("SITE_URL")
username = os.getenv("SITE_USERNAME")
password = os.getenv("SITE_PASSWORD")

def test_page_orientation_api_fetch():
    """Test that page_orientation is auto-populated from Print Format."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/home/frappe/frappe-bench/chromium/chrome-linux/headless_shell"
        )
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        
        # Login
        page.goto(f"{site_url}/desk/login")
        page.fill("#login_email", username)
        page.fill("#login_password", password)
        page.click(".btn-login")
        page.wait_for_url(f"{site_url}/desk/**", timeout=30000)
        time.sleep(5)
        
        # Navigate to print preview
        page.goto(f"{site_url}/desk/print/Stock%20Entry/MAT-STE-2026-00004")
        page.wait_for_load_state("networkidle")
        time.sleep(5)
        
        # Check page_orientation dropdown value
        result = page.evaluate('''() => {
            const field = document.querySelector('[data-fieldname="page_orientation"]');
            if (!field) return { found: false };
            const select = field.querySelector('select');
            return { found: true, value: select ? select.value : null };
        }''')
        
        print(f"page_orientation value: {result}")
        
        # Verify it matches Print Format value (Landscape)
        assert result['found'], "page_orientation field not found"
        assert result['value'] == 'Landscape', f"Expected Landscape, got {result['value']}"
        
        browser.close()
```

### Key Test Scenarios

1. **API Fetch**: Verify `page_orientation` is auto-populated from Print Format doctype
2. **Manual Override**: User can change orientation, preview updates with `.landscape` class
3. **CSS Injection**: Landscape CSS is injected with `!important` to override defaults
4. **Print Format Change**: When print format changes, orientation resets to new format's value
