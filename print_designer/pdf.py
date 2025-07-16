import hashlib
import html
import json
<<<<<<< HEAD
=======
import re
>>>>>>> develop
import time

import frappe
from frappe.monitor import add_data_to_monitor
from frappe.utils.error import log_error
from frappe.utils.jinja_globals import is_rtl
from frappe.utils.pdf import pdf_body_html as fw_pdf_body_html

<<<<<<< HEAD

def pdf_header_footer_html(soup, head, content, styles, html_id, css):
	if soup.find(id="__print_designer"):
		if frappe.form_dict.get("pdf_generator", "wkhtmltopdf") == "chrome":
			path = "print_designer/page/print_designer/jinja/header_footer.html"
		else:
			path = "print_designer/page/print_designer/jinja/header_footer_old.html"
=======
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
>>>>>>> develop
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
<<<<<<< HEAD
		if frappe.local.form_dict.get("pdf_generator", "wkhtmltopdf") == "chrome":
			path = "print_designer/pdf_generator/framework fromats/pdf_header_footer_chrome.html"
=======
		# Chrome PDF generation is disabled - always use default path
>>>>>>> develop

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
		print_format_name = hashlib.md5(print_format.name.encode(), usedforsecurity=False).hexdigest()
		add_data_to_monitor(print_designer=print_format_name, print_designer_action="download_pdf")

		settings = json.loads(print_format.print_designer_settings)

		args.update(
			{
				"headerElement": json.loads(print_format.print_designer_header),
				"bodyElement": json.loads(print_format.print_designer_body),
				"footerElement": json.loads(print_format.print_designer_footer),
				"settings": settings,
				"pdf_generator": frappe.form_dict.get("pdf_generator", "wkhtmltopdf"),
			}
		)
<<<<<<< HEAD
=======
		
		# Handle copy functionality with wkhtmltopdf (since Chrome is disabled)
		copy_count = cint(frappe.form_dict.get("copy_count", 0))
		copy_labels = frappe.form_dict.get("copy_labels", "")
		if copy_count > 1:
			# For wkhtmltopdf copies, we'll use template-based approach
			copy_labels_list = copy_labels.split(",") if copy_labels else [frappe._("Original"), frappe._("Copy")]
			args.update({
				"copy_count": copy_count,
				"copy_labels": copy_labels_list,
				"enable_copies": True
			})
		
		# Add Letter Head using standard Frappe Letter Head system (only for wkhtmltopdf)
		pdf_generator = frappe.form_dict.get("pdf_generator", "wkhtmltopdf")
		letterhead = frappe.form_dict.get("letterhead")
		no_letterhead = frappe.form_dict.get("no_letterhead")
		# Since Chrome is disabled, this condition is always true for Print Designer
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
>>>>>>> develop

		if not is_older_schema(settings=settings, current_version="1.1.0"):
			args.update({"pd_format": json.loads(print_format.print_designer_print_format)})
		else:
			args.update({"afterTableElement": json.loads(print_format.print_designer_after_table or "[]")})

<<<<<<< HEAD
=======
		# Clean CSS for wkhtmltopdf compatibility BEFORE template rendering
		if args["pdf_generator"] == "wkhtmltopdf":
			# Clean inline CSS from the settings.css if it exists
			if "settings" in args and "css" in args["settings"]:
				original_css = args["settings"]["css"]
				cleaned_css = clean_css_for_wkhtmltopdf(original_css)
				args["settings"]["css"] = cleaned_css
				
				# Debug logging
				if frappe.conf.developer_mode:
					frappe.logger().info(f"Print Designer CSS cleaning: Original length: {len(original_css)}, Cleaned length: {len(cleaned_css)}")

>>>>>>> develop
		# replace placeholder comment with user provided jinja code
		template_source = template.replace(
			"<!-- user_generated_jinja_code -->", args["settings"].get("userProvidedJinja", "")
		)
		try:
			template = jenv.from_string(template_source)
<<<<<<< HEAD
			return template.render(args, filters={"len": len})
=======
			rendered_html = template.render(args, filters={"len": len})
			
			# Additional CSS cleaning of rendered HTML for wkhtmltopdf
			if args["pdf_generator"] == "wkhtmltopdf":
				# Extract and clean CSS from style tags in the rendered HTML
				rendered_html = re.sub(
					r'(<style[^>]*>)(.*?)(</style>)',
					lambda m: m.group(1) + clean_css_for_wkhtmltopdf(m.group(2)) + m.group(3),
					rendered_html,
					flags=re.DOTALL
				)
				
				# Nuclear option: Always use minimal CSS for wkhtmltopdf to prevent crashes
				# Replace all style tags with minimal safe CSS (no borders unless explicitly designed)
				minimal_css = """
				.print-format { 
					font-family: Arial, sans-serif; 
					font-size: 12px; 
					box-sizing: border-box;
					padding: 0;
					margin: 0;
				}
				.staticText { 
					display: inline-block; 
					font-family: Arial, sans-serif;
					font-size: 12px;
				}
				.dynamicText { 
					display: inline-block; 
					font-family: Arial, sans-serif;
					font-size: 12px;
				}
				.printTable { 
					border-collapse: collapse; 
					width: 100%; 
					font-family: Arial, sans-serif;
					font-size: 12px;
				}
				.printTable td, .printTable th { 
					padding: 5px; 
					text-align: left;
					vertical-align: top;
				}
				.rectangle { 
					display: block;
				}
				.image {
					display: block;
					max-width: 100%;
				}
				.barcode {
					display: block;
				}
				#__print_designer {
					position: relative;
				}
				/* Force remove all borders with highest specificity */
				* {
					border: none !important;
					border-width: 0 !important;
					border-style: none !important;
					border-color: transparent !important;
					outline: none !important;
				}
				"""
				rendered_html = re.sub(
					r'<style[^>]*>.*?</style>',
					f'<style>{minimal_css}</style>',
					rendered_html,
					flags=re.DOTALL
				)
				
				# Also remove border-related inline styles from HTML elements
				border_patterns = [
					r'border[^:;]*:[^;]*;?',
					r'border-[^:;]*:[^;]*;?',
					r'outline[^:;]*:[^;]*;?'
				]
				
				for pattern in border_patterns:
					# Remove border properties from style attributes
					rendered_html = re.sub(
						r'(style="[^"]*?)' + pattern + r'([^"]*")',
						r'\1\2',
						rendered_html,
						flags=re.IGNORECASE
					)
					rendered_html = re.sub(
						r"(style='[^']*?)" + pattern + r"([^']*')",
						r'\1\2',
						rendered_html,
						flags=re.IGNORECASE
					)
				
				if frappe.conf.developer_mode:
					frappe.logger().info("Applied minimal CSS for wkhtmltopdf compatibility")
				
				# Debug: Save cleaned HTML for inspection in developer mode
				if frappe.conf.developer_mode:
					import tempfile
					import os
					debug_file = os.path.join(tempfile.gettempdir(), f"print_designer_debug_{print_format.name}.html")
					with open(debug_file, 'w', encoding='utf-8') as f:
						f.write(rendered_html)
					frappe.logger().info(f"Debug HTML saved to: {debug_file}")
			
			return rendered_html
>>>>>>> develop

		except Exception as e:
			error = log_error(title=e, reference_doctype="Print Format", reference_name=print_format.name)
			if frappe.conf.developer_mode:
				return f"<h1><b>Something went wrong while rendering the print format.</b> <hr/> If you don't know what just happened, and wish to file a ticket or issue on Github <hr /> Please copy the error from <code>Error Log {error.name}</code> or ask Administrator.<hr /><h3>Error rendering print format: {error.reference_name}</h3><h4>{error.method}</h4><pre>{html.escape(error.error)}</pre>"
			else:
				return f"<h1><b>Something went wrong while rendering the print format.</b> <hr/> If you don't know what just happened, and wish to file a ticket or issue on Github <hr /> Please copy the error from <code>Error Log {error.name}</code> or ask Administrator.</h1>"
	return fw_pdf_body_html(template, args)


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
