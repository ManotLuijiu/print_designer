import hashlib
import html
import json
import re
import time

import frappe
from frappe.monitor import add_data_to_monitor
from frappe.utils.error import log_error
from frappe.utils.jinja_globals import is_rtl
from frappe.utils.pdf import pdf_body_html as fw_pdf_body_html

# Import cint with fallback
try:
	from frappe.utils import cint
except ImportError:
	def cint(value, default=0):
		try:
			return int(value) if value else default
		except (ValueError, TypeError):
			return default


def clean_css_for_wkhtmltopdf(css_content):
	"""Remove CSS custom properties and problematic styles that wkhtmltopdf doesn't support"""
	if not css_content:
		return css_content
	
	# First, aggressively remove all CSS custom property declarations
	# Remove any line containing --print- or other CSS custom properties
	lines = css_content.split('\n')
	cleaned_lines = []
	
	for line in lines:
		# Skip lines with CSS custom properties
		if '--' in line and ':' in line:
			continue
		cleaned_lines.append(line)
	
	css_content = '\n'.join(cleaned_lines)
	
	# Remove entire blocks containing CSS custom properties
	css_content = re.sub(r':root[^{]*\{[^}]*\}', '', css_content, flags=re.DOTALL | re.MULTILINE)
	css_content = re.sub(r'::before[^{]*\{[^}]*\}', '', css_content, flags=re.DOTALL | re.MULTILINE)
	css_content = re.sub(r'::after[^{]*\{[^}]*\}', '', css_content, flags=re.DOTALL | re.MULTILINE)
	
	# More aggressive CSS custom property removal
	css_content = re.sub(r'--[a-zA-Z0-9_-]+\s*:\s*[^;}]+[;}]', '', css_content, flags=re.MULTILINE)
	
	# Remove @page rules completely
	css_content = re.sub(r'@page[^{]*\{[^}]*\}', '', css_content, flags=re.DOTALL)
	
	# Remove problematic CSS properties
	problematic_properties = [
		r'dpi\s*:\s*[^;]+;?',
		r'page-width\s*:\s*[^;]+;?',
		r'page-height\s*:\s*[^;]+;?',
		r'flex\s*:\s*[^;]+;?',
		r'flex-direction\s*:\s*[^;]+;?',
		r'display\s*:\s*-webkit-box\s*;?',
		r'display\s*:\s*-webkit-flex\s*;?',
		r'display\s*:\s*flex\s*;?',
		r'-webkit-box-sizing\s*:\s*[^;]+;?',
		r'object-fit\s*:\s*[^;]+;?',
		r'object-position\s*:\s*[^;]+;?',
		r'user-select\s*:\s*[^;]+;?',
		r'overflow-wrap\s*:\s*[^;]+;?',
		r'border-radius\s*:\s*[^;]+;?',
		r'box-shadow\s*:\s*[^;]+;?',
		r'text-overflow\s*:\s*[^;]+;?',
		r'white-space\s*:\s*nowrap\s*;?'
	]
	
	for prop in problematic_properties:
		css_content = re.sub(prop, '', css_content, flags=re.IGNORECASE | re.MULTILINE)
	
	# Remove Vue.js specific selectors and data attributes
	css_content = re.sub(r'[^{]*\[data-v-[^\]]*\][^{]*\{[^}]*\}', '', css_content, flags=re.DOTALL)
	
	# Remove any remaining CSS custom property references
	css_content = re.sub(r'var\([^)]*\)', 'inherit', css_content)
	
	# Clean up malformed CSS and empty blocks
	css_content = re.sub(r'\{[^}]*--[^}]*\}', '{}', css_content)  # Remove blocks with remaining custom props
	css_content = re.sub(r'[^{}]*\{\s*\}', '', css_content)  # Remove empty selectors
	css_content = re.sub(r'\s+', ' ', css_content)  # Normalize whitespace
	css_content = re.sub(r';\s*;+', ';', css_content)  # Remove multiple semicolons
	css_content = re.sub(r'^\s*;\s*', '', css_content, flags=re.MULTILINE)  # Remove leading semicolons
	
	# Final cleanup
	css_content = css_content.strip()
	
	return css_content


def pdf_header_footer_html(soup, head, content, styles, html_id, css):
	if soup.find(id="__print_designer"):
		# Always use old header/footer template (chrome support removed)
		path = "print_designer/page/print_designer/jinja/header_footer_old.html"
		try:
			return frappe.render_template(
				path,
				{
					"head": head,
					"content": content,
					"styles": styles,
					"html_id": html_id,
					"css": css,
					"headerFonts": soup.find(id="headerFontsLinkTag"),
					"footerFonts": soup.find(id="footerFontsLinkTag"),
					"lang": frappe.local.lang,
					"layout_direction": "rtl" if is_rtl() else "ltr",
				},
			)
		except Exception as e:
			error = log_error(title=e, reference_doctype="Print Format")
			frappe.throw(
				msg=f"Something went wrong ( Error ) : If you don't know what just happened, and wish to file a ticket or issue on github, please copy the error from <b>Error Log {error.name}</b> or ask Administrator.",
				exc=e,
			)
	else:
		from frappe.utils.pdf import pdf_footer_html, pdf_header_html

		# same default path is defined in fw pdf_header_html function if no path is passed it will use default path
		path = "templates/print_formats/pdf_header_footer.html"
		# Chrome PDF generation is disabled - always use default path

		if html_id == "header-html":
			return pdf_header_html(
				soup=soup,
				head=head,
				content=content,
				styles=styles,
				html_id=html_id,
				css=css,
				path=path,
			)
		elif html_id == "footer-html":
			return pdf_footer_html(
				soup=soup,
				head=head,
				content=content,
				styles=styles,
				html_id=html_id,
				css=css,
				path=path,
			)


def pdf_body_html(print_format, jenv, args, template):
	if print_format and print_format.print_designer and print_format.print_designer_body:
		# Ensure we have the necessary data for both PDF and HTML generation
		_prepare_print_designer_context(print_format, args)
		print_format_name = hashlib.md5(print_format.name.encode(), usedforsecurity=False).hexdigest()
		add_data_to_monitor(print_designer=print_format_name, print_designer_action="download_pdf")

		settings = args["settings"]  # Already set by _prepare_print_designer_context
		
		# Debug: Check if pd_format is available for HTML preview
		if frappe.conf.developer_mode:
			has_pd_format = "pd_format" in args
			frappe.logger().info(f"Print Designer HTML generation - pd_format available: {has_pd_format}, template type: {type(template)}")
		
		# Handle copy functionality with wkhtmltopdf (since Chrome is disabled)
		copy_count = cint(frappe.form_dict.get("copy_count", 0))
		copy_labels = frappe.form_dict.get("copy_labels", "")
		if copy_count > 1:
			# For wkhtmltopdf copies, we'll use template-based approach
			if copy_labels:
				copy_labels_list = copy_labels.split(",")
			else:
				# Default labels: First copy is "Original", subsequent copies are "Copy"
				copy_labels_list = []
				for i in range(copy_count):
					if i == 0:
						copy_labels_list.append(frappe._("Original"))
					else:
						copy_labels_list.append(frappe._("Copy"))
			
			args.update({
				"copy_count": copy_count,
				"copy_labels": copy_labels_list,
				"enable_copies": True
			})
		
		# Determine best PDF generator: WeasyPrint > wkhtmltopdf
		from print_designer.weasyprint_integration import should_use_weasyprint
		pdf_generator = frappe.form_dict.get("pdf_generator")
		
		if not pdf_generator:
			# Auto-select best available PDF generator
			pdf_generator = "WeasyPrint" if should_use_weasyprint() else "wkhtmltopdf"
		
		letterhead = frappe.form_dict.get("letterhead")
		no_letterhead = frappe.form_dict.get("no_letterhead")
		# Letter Head works with both wkhtmltopdf and WeasyPrint
		if not no_letterhead and letterhead:
			try:
				# Use standard Frappe Letter Head function
				from frappe.www.printview import get_letter_head
				doc = args.get("doc")
				letter_head_data = get_letter_head(doc, no_letterhead, letterhead)
				
				if letter_head_data:
					# Prepare document context for template rendering
					doc_context = {}
					if doc:
						try:
							if hasattr(doc, 'as_dict'):
								doc_context = doc.as_dict()
							elif isinstance(doc, dict):
								doc_context = doc
							else:
								doc_context = {}
						except Exception:
							doc_context = {}
					
					# Render Letter Head content with document context like standard Frappe
					if letter_head_data.get("content"):
						letter_head_data["content"] = frappe.utils.jinja.render_template(
							letter_head_data["content"], {"doc": doc_context}
						)
					if letter_head_data.get("footer"):
						letter_head_data["footer"] = frappe.utils.jinja.render_template(
							letter_head_data["footer"], {"doc": doc_context}
						)
					
					# Add Letter Head variables in standard Frappe format
					args.update({
						"letter_head": letter_head_data.get("content", ""),
						"footer": letter_head_data.get("footer", ""),
						"letter_head_data": letter_head_data,  # Full data for scripts
						"no_letterhead": False
					})
			except Exception as e:
				# Log error but don't break PDF generation
				frappe.log_error(title="Letter Head Error in Print Designer", message=f"Error processing Letter Head: {str(e)}")
				# Continue without Letter Head
				pass

		# pd_format and afterTableElement are already set by _prepare_print_designer_context

		# Clean CSS based on PDF generator BEFORE template rendering
		if "settings" in args and "css" in args["settings"]:
			original_css = args["settings"]["css"]
			
			if args["pdf_generator"] == "WeasyPrint":
				from print_designer.weasyprint_integration import clean_css_for_weasyprint
				cleaned_css = clean_css_for_weasyprint(original_css)
			else:
				# wkhtmltopdf needs more aggressive CSS cleaning
				cleaned_css = clean_css_for_wkhtmltopdf(original_css)
			
			args["settings"]["css"] = cleaned_css
			
			# Debug logging
			if frappe.conf.developer_mode:
				frappe.logger().info(f"Print Designer CSS cleaning ({args['pdf_generator']}): Original length: {len(original_css)}, Cleaned length: {len(cleaned_css)}")
		try:
			# Handle both string template and Jinja2 Template object
			if hasattr(template, 'render'):
				# Template is already a Jinja2 Template object (from HTML preview)
				rendered_html = template.render(args, filters={"len": len})
			else:
				# Template is a string (from PDF generation), process it
				template_source = template.replace(
					"<!-- user_generated_jinja_code -->", args["settings"].get("userProvidedJinja", "")
				)
				template_obj = jenv.from_string(template_source)
				rendered_html = template_obj.render(args, filters={"len": len})
			
			# Check if this is actual PDF generation or HTML preview
			# PDF generation will have as_pdf=True in form_dict or trigger_print
			is_pdf_generation = (
				frappe.form_dict.get("as_pdf") or 
				frappe.form_dict.get("trigger_print") or
				args.get("trigger_print") or
				frappe.form_dict.get("_doctype") == "PDF"
			)
			
			# Only apply CSS cleaning for actual PDF generation, not HTML preview
			if is_pdf_generation:
				if args["pdf_generator"] == "WeasyPrint":
					# WeasyPrint supports modern CSS better, minimal cleaning needed
					from print_designer.weasyprint_integration import clean_css_for_weasyprint
					rendered_html = re.sub(
						r'(<style[^>]*>)(.*?)(</style>)',
						lambda m: m.group(1) + clean_css_for_weasyprint(m.group(2)) + m.group(3),
						rendered_html,
						flags=re.DOTALL
					)
				elif args["pdf_generator"] == "wkhtmltopdf":
					# Only apply basic CSS cleaning for wkhtmltopdf, no nuclear CSS
					rendered_html = re.sub(
						r'(<style[^>]*>)(.*?)(</style>)',
						lambda m: m.group(1) + clean_css_for_wkhtmltopdf(m.group(2)) + m.group(3),
						rendered_html,
						flags=re.DOTALL
					)
					
					if frappe.conf.developer_mode:
						frappe.logger().info("Applied basic CSS cleaning for wkhtmltopdf compatibility")
			else:
				# For HTML preview, keep original CSS completely untouched
				if frappe.conf.developer_mode:
					frappe.logger().info("HTML preview mode - keeping original CSS untouched")
			
			return rendered_html

	except Exception as e:
			error = log_error(title=e, reference_doctype="Print Format", reference_name=print_format.name)
			if frappe.conf.developer_mode:
				return f"<h1><b>Something went wrong while rendering the print format.</b> <hr/> If you don't know what just happened, and wish to file a ticket or issue on Github <hr /> Please copy the error from <code>Error Log {error.name}</code> or ask Administrator.<hr /><h3>Error rendering print format: {error.reference_name}</h3><h4>{error.method}</h4><pre>{html.escape(error.error)}</pre>"
			else:
				return f"<h1><b>Something went wrong while rendering the print format.</b> <hr/> If you don't know what just happened, and wish to file a ticket or issue on Github <hr /> Please copy the error from <code>Error Log {error.name}</code> or ask Administrator.</h1>"
	return fw_pdf_body_html(template, args)


def before_print(print_format=None, **kwargs):
	"""
	Before print hook to prepare Print Designer context.
	Called before both PDF and HTML generation.
	"""
	if print_format and hasattr(print_format, 'print_designer') and print_format.print_designer:
		# Prepare the args dict if it's not passed
		args = kwargs.get('args', {})
		_prepare_print_designer_context(print_format, args)
		# Update the kwargs with prepared args
		kwargs['args'] = args
	return kwargs


def _prepare_print_designer_context(print_format, args):
	"""
	Prepare the context variables needed for Print Designer templates.
	This ensures both PDF and HTML generation have the required variables.
	"""
	if not (print_format and print_format.print_designer and print_format.print_designer_body):
		return
	
	try:
		# Check if print_designer_settings exists and is not None
		if not print_format.print_designer_settings:
			frappe.log_error(
				title="Print Designer Settings Missing",
				message=f"Print Format '{print_format.name}' has print_designer enabled but print_designer_settings is None"
			)
			return
		
		settings = json.loads(print_format.print_designer_settings)
		
		# Always prepare the core elements
		args.update({
			"headerElement": json.loads(print_format.print_designer_header or "[]"),
			"bodyElement": json.loads(print_format.print_designer_body or "[]"),
			"footerElement": json.loads(print_format.print_designer_footer or "[]"),
			"settings": settings,
			"pdf_generator": frappe.form_dict.get("pdf_generator", "wkhtmltopdf"),
		})
		
		# Set pd_format for newer schema
		if not is_older_schema(settings=settings, current_version="1.1.0"):
			args.update({"pd_format": json.loads(print_format.print_designer_print_format or "{}")})
		else:
			args.update({"afterTableElement": json.loads(print_format.print_designer_after_table or "[]")})
		
		# Set send_to_jinja flag if not already set
		if "send_to_jinja" not in args:
			args["send_to_jinja"] = True
			
	except Exception as e:
		frappe.log_error(
			title="Print Designer Context Preparation Error",
			message=f"Error preparing context for print format '{print_format.name}': {str(e)}"
		)


def is_older_schema(settings, current_version):
	format_version = settings.get("schema_version", "1.0.0")
	format_version = format_version.split(".")
	current_version = current_version.split(".")
	if int(format_version[0]) < int(current_version[0]):
		return True
	elif int(format_version[0]) == int(current_version[0]) and int(format_version[1]) < int(
		current_version[1]
	):
		return True
	elif (
		int(format_version[0]) == int(current_version[0])
		and int(format_version[1]) == int(current_version[1])
		and int(format_version[2]) < int(current_version[2])
	):
		return True
	else:
		return False


def get_print_format_template(jenv, print_format):
	# if print format is created using print designer, then use print designer template
	if print_format and print_format.print_designer and print_format.print_designer_body:
		# Check if print_designer_settings exists and is not None
		if not print_format.print_designer_settings:
			frappe.log_error(
				title="Print Designer Settings Missing",
				message=f"Print Format '{print_format.name}' has print_designer enabled but print_designer_settings is None"
			)
			return None
		
		settings = json.loads(print_format.print_designer_settings)
		if is_older_schema(settings, "1.1.0"):
			return jenv.loader.get_source(
				jenv, "print_designer/page/print_designer/jinja/old_print_format.html"
			)[0]
		else:
			return jenv.loader.get_source(
				jenv, "print_designer/page/print_designer/jinja/print_format.html"
			)[0]


def measure_time(func):
	def wrapper(*args, **kwargs):
		start_time = time.time()
		result = func(*args, **kwargs)
		end_time = time.time()
		print(f"Function {func.__name__} took {end_time - start_time:.4f} seconds")
		return result

	return wrapper
