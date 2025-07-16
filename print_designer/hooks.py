from . import __version__ as app_version

app_name = "print_designer"
app_title = "Print Designer"
app_publisher = "Frappe Technologies Pvt Ltd."
app_description = "Frappe App to Design Print Formats using interactive UI."
app_email = "hello@frappe.io"
app_license = "AGPLv3"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_js = ""

# app_include_css = ["/assets/print_designer/css/thai_fonts.css"]


# include js, css files in header of web template
# web_include_css = "/assets/print_designer/css/print_designer.css"
# web_include_js = "/assets/print_designer/js/print_designer.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "print_designer/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
page_js = {
    "print": "print_designer/client_scripts/print.js",
    "point-of-sale": "print_designer/client_scripts/point_of_sale.js",
}

# include js in doctype views
doctype_js = {"Print Format": "print_designer/client_scripts/print_format.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
    "methods": [
        "print_designer.print_designer.page.print_designer.print_designer.render_user_text",
        "print_designer.print_designer.page.print_designer.print_designer.convert_css",
        "print_designer.print_designer.page.print_designer.print_designer.convert_uom",
        "print_designer.print_designer.page.print_designer.print_designer.get_barcode",
    ]
}

# Installation
# ------------

before_install = "print_designer.install.before_install"
after_install = "print_designer.install.after_install"
after_app_install = "print_designer.install.after_app_install"

# Uninstallation
# ------------

before_uninstall = "print_designer.uninstall.before_uninstall"
# after_uninstall = "print_designer.uninstall.after_uninstall"

# ------------
# PDF
# ------------

pdf_header_html = "print_designer.pdf.pdf_header_footer_html"
pdf_body_html = "print_designer.pdf.pdf_body_html"
pdf_footer_html = "print_designer.pdf.pdf_header_footer_html"

get_print_format_template = "print_designer.pdf.get_print_format_template"


pdf_generator = "print_designer.pdf_generator.pdf.get_pdf"

override_doctype_class = {
    "Print Format": "print_designer.print_designer.overrides.print_format.PDPrintFormat",
}

# Path Relative to the app folder where default templates should be stored
pd_standard_format_folder = "default_templates"

doc_events = {
	"Print Format": {
		"before_save": "print_designer.install.set_wkhtmltopdf_for_print_designer_format",
	}
}
