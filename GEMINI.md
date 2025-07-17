# Gemini Code Assistant Project Context

This document provides context for the Gemini Code Assistant to understand the Print Designer project.

## Project Overview

Print Designer is a Frappe app that provides an interactive UI for designing and creating print formats. It allows for a high degree of customization, similar to tools like Figma or Adobe Illustrator, but within the Frappe ecosystem. The goal is to enable users to create complex print formats without writing code.

## Technologies

- **Backend:** Frappe Framework (Python)
- **Frontend:** Vue.js, HTML, CSS, Javascript
- **Dependencies:**
    - **Python:** PyQRCode, pypng, python-barcode, websockets, distro, weasyprint
    - **JS:** @interactjs, html2canvas, qrcode

## Project Structure

- `print_designer/`: Main Frappe app directory.
    - `public/`: Frontend assets (JS, CSS, images).
        - `js/print_designer/`: Vue.js application source.
    - `www/`: Web pages.
    - `doctype/`: Frappe DocTypes.
    - `patches/`: Database schema patches.
    - `templates/`: Jinja2 templates.
- `package.json`: Lists frontend dependencies.
- `pyproject.toml`: Lists backend dependencies and project metadata.
- `README.md`: Project description, setup instructions, and FAQ.

## Development Setup

The recommended development setup uses Docker.

1.  Create a directory and `cd` into it.
2.  Download `docker-compose.yml` and `init.sh` from the project repository.
3.  Run `docker compose up`.
4.  The site will be available at `http://print-designer.localhost:8000`.

## Key Files

- `print_designer/public/js/print_designer/App.vue`: The main Vue.js component for the print designer interface.
- `print_designer/print_designer/page/print_designer/print_designer.js`: The Javascript file that initializes the Vue app.
- `print_designer/pdf.py`: Contains server-side logic for PDF generation.
- `print_designer/hooks.py`: Defines Frappe hooks for the app.
- `pyproject.toml`: Defines python dependencies.
- `package.json`: Defines JS dependencies.

## How to Run Tests

The project does not appear to have a dedicated test suite configured in the provided file listing. However, individual test files exist, such as `test_logging.py` and `test_safe_pdf_solution.py`. These are likely run using the Frappe Bench CLI.

To run a specific test file, you would typically use a command like:

```bash
bench --site print-designer.localhost execute print_designer.test_logging.run_tests
```
