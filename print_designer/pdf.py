import hashlib
import html
import json
import time

import frappe
from frappe.monitor import add_data_to_monitor
from frappe.utils.error import log_error
from frappe.utils.jinja_globals import is_rtl
from frappe.utils.pdf import pdf_body_html as fw_pdf_body_html


def get_effective_language(print_format_name=None):
    """
    Get the effective language for PDF generation with proper priority:
    1. _lang parameter from URL (highest priority)
    2. Print Format language field
    3. frappe.local.lang (fallback)

    Args:
        print_format_name: Name of the print format to check for language setting

    Returns:
        str: The effective language code/name to use
    """
    print(f"[DEBUG] get_effective_language called with print_format_name: {print_format_name}")
    
    # Priority 1: Check _lang parameter from URL
    url_lang = frappe.form_dict.get("_lang")
    print(f"[DEBUG] URL _lang parameter: {url_lang}")
    if url_lang and str(url_lang).strip():
        print(f"[LANGUAGE] Using language from URL parameter: {url_lang}")
        return url_lang

    # Priority 2: Check Print Format default_print_language field
    if print_format_name:
        try:
            print(f"[DEBUG] Fetching Print Format doc: {print_format_name}")
            print_format_doc = frappe.get_doc("Print Format", print_format_name)
            
            # Try default_print_language field first (standard field)
            format_lang = (
                print_format_doc.get("default_print_language")
                if hasattr(print_format_doc, "get")
                else getattr(print_format_doc, "default_print_language", None)
            )
            print(f"[DEBUG] Print Format default_print_language field: {format_lang}")
            
            # Fallback to language field if default_print_language is not set
            if not format_lang:
                format_lang = (
                    print_format_doc.get("language")
                    if hasattr(print_format_doc, "get")
                    else getattr(print_format_doc, "language", None)
                )
                print(f"[DEBUG] Print Format language field (fallback): {format_lang}")
                
            if format_lang and str(format_lang).strip():
                print(f"[LANGUAGE] Using language from Print Format: {format_lang}")
                return format_lang
            else:
                print(f"[DEBUG] No valid language found in Print Format fields")
        except Exception as e:
            print(f"[ERROR] Error getting Print Format language: {str(e)}")

    # Priority 3: Fallback to local language
    local_lang = frappe.local.lang
    print(f"[DEBUG] frappe.local.lang: {local_lang}")
    
    # Priority 4: If no language is set anywhere, default to Thai ('th')
    # This is specific to this implementation where Thai is the primary language
    if not local_lang or local_lang == "en":
        local_lang = "th"
        print(f"[LANGUAGE] Using Thai as default language (overriding '{frappe.local.lang}')")
    else:
        print(f"[LANGUAGE] Using fallback language: {local_lang}")
    
    return local_lang


def is_thai_language(language):
    """
    Check if the given language indicates Thai language.

    Args:
        language: Language string to check

    Returns:
        bool: True if the language is Thai
    """
    print(f"[DEBUG] is_thai_language called with: '{language}' (type: {type(language)})")
    
    if not language:
        print(f"[DEBUG] is_thai_language: Empty language, returning False")
        return False

    language_str = str(language).strip()
    language_lower = language_str.lower()
    
    print(f"[DEBUG] is_thai_language: language_str='{language_str}', language_lower='{language_lower}'")
    
    # Check for Thai language indicators
    # Note: "ไทย" should be checked as-is, not lowercased
    thai_indicators_exact = ["ไทย", "th", "th-th"]
    thai_indicators_lower = ["thai", "thai-th", "th", "th-th"]
    
    is_thai = language_str in thai_indicators_exact or language_lower in thai_indicators_lower
    print(f"[DEBUG] is_thai_language result: {is_thai}")
    
    return is_thai


def pdf_header_footer_html(soup, head, content, styles, html_id, css):
    print(f"[DEBUG] pdf_header_footer_html called with html_id: {html_id}")
    
    if soup.find(id="__print_designer"):
        pdf_generator = frappe.form_dict.get("pdf_generator", "wkhtmltopdf")
        print(f"[DEBUG] PDF generator: {pdf_generator}")
        
        if pdf_generator == "chrome":
            path = "print_designer/page/print_designer/jinja/header_footer.html"
        else:
            path = "print_designer/page/print_designer/jinja/header_footer_old.html"
        
        print(f"[DEBUG] Using template path: {path}")
        
        try:
            # Get effective language using centralized function
            print_format_name = frappe.form_dict.get("format")
            print(f"[DEBUG] Print format name from form_dict: {print_format_name}")
            effective_lang = get_effective_language(print_format_name)
            print(f"[PDF] Effective language for PDF header/footer: {effective_lang}")

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
                    "lang": effective_lang,
                    "is_thai": is_thai_language(effective_lang),
                    "layout_direction": "rtl" if is_rtl() else "ltr",
                },
            )
        except Exception as e:
            error = log_error(title=e, reference_doctype="Print Format")
            error_name = error.name if error and hasattr(error, "name") else "Unknown"
            frappe.throw(
                msg=f"Something went wrong ( Error ) : If you don't know what just happened, and wish to file a ticket or issue on github, please copy the error from <b>Error Log {error_name}</b> or ask Administrator.",
                exc=e,
            )
    else:
        from frappe.utils.pdf import pdf_footer_html, pdf_header_html

        # same default path is defined in fw pdf_header_html function if no path is passed it will use default path
        path = "templates/print_formats/pdf_header_footer.html"
        if frappe.local.form_dict.get("pdf_generator", "wkhtmltopdf") == "chrome":
            path = "print_designer/pdf_generator/framework_formats/pdf_header_footer_chrome.html"

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
    print(f"[DEBUG] pdf_body_html called for print_format: {print_format.name if print_format else 'None'}")
    
    if (
        print_format
        and print_format.print_designer
        and print_format.print_designer_body
    ):
        print(f"[DEBUG] Processing Print Designer format: {print_format.name}")
        
        print_format_name = hashlib.md5(
            print_format.name.encode(), usedforsecurity=False
        ).hexdigest()
        add_data_to_monitor(
            print_designer=print_format_name, print_designer_action="download_pdf"
        )

        # Handle None or empty print_designer_settings
        if print_format.print_designer_settings:
            settings = json.loads(print_format.print_designer_settings)
            print(f"[DEBUG] Settings loaded with schema_version: {settings.get('schema_version', 'not set')}")
        else:
            settings = {}
            print(f"[DEBUG] No settings found, using empty dict")

        # Get effective language for this print format
        effective_lang = get_effective_language(print_format.name)
        print(f"[PDF BODY] Using language: {effective_lang}")

        args.update(
            {
                "headerElement": json.loads(print_format.print_designer_header or "[]"),
                "bodyElement": json.loads(print_format.print_designer_body or "[]"),
                "footerElement": json.loads(print_format.print_designer_footer or "[]"),
                "settings": settings,
                "pdf_generator": frappe.form_dict.get("pdf_generator", "wkhtmltopdf"),
                "effective_lang": effective_lang,
                "is_thai": is_thai_language(effective_lang),
            }
        )

        if not is_older_schema(settings=settings, current_version="1.1.0"):
            # Check if print_designer_print_format has valid data
            # For Thai WHT certificates, only apply if payment has withholding tax
            if print_format.print_designer_print_format:
                args.update(
                    {"pd_format": json.loads(print_format.print_designer_print_format)}
                )
            else:
                # For Payment Entry WHT forms without designer format, check if WHT applies
                # Parse doc from args if it's a string (as it comes from printview)
                doc_data = args.get("doc", {})
                if isinstance(doc_data, str):
                    try:
                        doc_data = json.loads(doc_data)
                    except (json.JSONDecodeError, TypeError):
                        doc_data = {}
                
                if doc_data.get("doctype") == "Payment Entry":
                    # In Thailand, WHT only applies to services, not goods
                    # Check if this payment entry has withholding tax fields
                    has_wht = (
                        doc_data.get("pd_custom_has_thai_taxes") or
                        doc_data.get("pd_custom_total_wht_amount", 0) > 0 or
                        doc_data.get("apply_tax_withholding_amount", 0) > 0
                    )
                    
                    if has_wht:
                        # If WHT applies but no designer format, use a basic template
                        args.update({"pd_format": {"elements": [], "sections": []}})
                    else:
                        # No WHT, use empty format (will fall back to standard template)
                        args.update({"pd_format": {}})
                else:
                    args.update({"pd_format": {}})
        else:
            # Handle older schema with null checks
            after_table_data = print_format.print_designer_after_table or "[]"
            args.update(
                {
                    "afterTableElement": json.loads(after_table_data)
                }
            )

        # replace placeholder comment with user provided jinja code
        template_source = template.replace(
            "<!-- user_generated_jinja_code -->",
            args["settings"].get("userProvidedJinja", ""),
        )
        try:
            template = jenv.from_string(template_source)
            return template.render(args, filters={"len": len})

        except Exception as e:
            error = log_error(
                title=e,
                reference_doctype="Print Format",
                reference_name=print_format.name,
            )
            if frappe.conf.developer_mode:
                if error:
                    return f"<h1><b>Something went wrong while rendering the print format.</b> <hr/> If you don't know what just happened, and wish to file a ticket or issue on Github <hr /> Please copy the error from <code>Error Log {error.name}</code> or ask Administrator.<hr /><h3>Error rendering print format: {getattr(error, 'reference_name', '')}</h3><pre>{html.escape(str(error))}</pre>"
                else:
                    return "<h1><b>Something went wrong while rendering the print format.</b> <hr/> Error logging failed. Please contact Administrator.</h1>"
            else:
                if error:
                    return f"<h1><b>Something went wrong while rendering the print format.</b> <hr/> If you don't know what just happened, and wish to file a ticket or issue on Github <hr /> Please copy the error from <code>Error Log {error.name}</code> or ask Administrator.</h1>"
                else:
                    return "<h1><b>Something went wrong while rendering the print format.</b> <hr/> Error logging failed. Please contact Administrator.</h1>"
    return fw_pdf_body_html(template, args)


def is_older_schema(settings, current_version):
    format_version = settings.get("schema_version", "1.0.0")
    format_version = format_version.split(".")
    current_version = current_version.split(".")
    if int(format_version[0]) < int(current_version[0]):
        return True
    elif int(format_version[0]) == int(current_version[0]) and int(
        format_version[1]
    ) < int(current_version[1]):
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
    print(f"[DEBUG] get_print_format_template called with print_format: {print_format}")
    # if print format is created using print designer, then use print designer template
    if (
        print_format
        and print_format.print_designer
        and print_format.print_designer_body
    ):
        print(f"[DEBUG] Print format '{print_format.name}' is using Print Designer")
        
        # Handle None or empty print_designer_settings
        if print_format.print_designer_settings:
            settings = json.loads(print_format.print_designer_settings)
            print(f"[DEBUG] Loaded settings: schema_version = {settings.get('schema_version', 'not set')}")
        else:
            settings = {}
            print(f"[DEBUG] No settings found, using empty dict")
        
        if is_older_schema(settings, "1.1.0"):
            template_path = "print_designer/page/print_designer/jinja/old_print_format.html"
            print(f"[DEBUG] Using old template: {template_path}")
            return jenv.loader.get_source(jenv, template_path)[0]
        else:
            template_path = "print_designer/page/print_designer/jinja/print_format.html"
            print(f"[DEBUG] Using new template: {template_path}")
            return jenv.loader.get_source(jenv, template_path)[0]


def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Function {func.__name__} took {end_time - start_time:.4f} seconds")
        return result

    return wrapper


def before_print(doc=None, method=None, print_settings=None, **kwargs):
    """
    Consolidated before print hook to prepare Print Designer context and Thai enhancements.
    Called before both PDF and HTML generation.

    Args:
        doc: The document being printed (when called as doc method)
        method: The method name (when called as doc method)
        print_settings: Print settings (when called as doc method)
        **kwargs: Additional arguments including 'args' for template context
    """
    print(f"[DEBUG] before_print called with doc={doc}, method={method}")
    
    try:
        # Get the print format from form_dict if not provided
        print_format = kwargs.get("print_format")
        if not print_format:
            print_format_name = frappe.form_dict.get("format") or frappe.form_dict.get(
                "print_format"
            )
            print(f"[DEBUG] Print format name from form_dict: {print_format_name}")
            
            if print_format_name:
                try:
                    print_format = frappe.get_doc("Print Format", print_format_name)
                    print(f"[DEBUG] Successfully loaded Print Format: {print_format_name}")
                except Exception as e:
                    print(f"[ERROR] Could not get print format '{print_format_name}': {str(e)}")
                    print_format = None

        # Prepare the args dict if it's not passed
        args = kwargs.get("args", {})
        if not args:
            args = {}
            kwargs["args"] = args

        # Add the document to args if provided
        if doc and "doc" not in args:
            args["doc"] = doc

        # 1. Prepare Print Designer context if this is a Print Designer format
        if print_format and print_format.get("print_designer"):
            _prepare_print_designer_context(print_format, args)
            print(f"Prepared Print Designer context for format: {print_format.name}")

        # 2. Handle Thai amount enhancement for applicable documents
        if doc and print_format:
            _handle_thai_amount_enhancement(print_format, doc, args)

        # Update the kwargs with prepared args
        kwargs["args"] = args

    except (BrokenPipeError, OSError, ConnectionError) as pipe_error:
        # Handle Chrome-related pipe errors gracefully
        print(f"Chrome communication error in before_print hook: {str(pipe_error)}")
        # Don't log to database for pipe errors to avoid recursion
        # Just continue with standard processing
    except Exception as e:
        frappe.log_error(
            title="Before Print Hook Error",
            message=f"Error in before_print hook for format '{getattr(print_format, 'name', 'Unknown')}': {str(e)}",
        )
        # Don't fail the print process, just log the error

    return kwargs


def _handle_thai_amount_enhancement(print_format, doc, args):
    """
    Handle Thai amount enhancement for documents with amount fields.
    This replaces the old thai_amount_to_word.enhance_in_words_field function.
    """
    print(f"[DEBUG] _handle_thai_amount_enhancement called for doc: {doc.name if doc else 'None'}")
    
    try:
        # Check if document has amount fields that need Thai enhancement
        if not (hasattr(doc, "in_words") and hasattr(doc, "grand_total")):
            print(f"[DEBUG] Document doesn't have in_words/grand_total fields, skipping Thai enhancement")
            return

        # Get effective language
        effective_lang = get_effective_language(print_format.name)
        print(f"[THAI ENHANCEMENT] Effective language: {effective_lang}")

        # Apply Thai enhancement ONLY if effective language is Thai
        if is_thai_language(effective_lang):
            try:
                from print_designer.utils.thai_amount_to_word import thai_money_in_words

                # Set Thai amount in words
                original_in_words = doc.in_words
                doc.in_words = thai_money_in_words(doc.grand_total or 0)

                # Also add to args for template access
                args["thai_in_words"] = doc.in_words
                args["use_thai_language"] = True
                args["original_in_words"] = original_in_words

                print(
                    f"Enhanced Thai amount for {doc.doctype} {doc.name}: {doc.in_words}"
                )

            except ImportError:
                print("Thai money conversion utility not available")
        else:
            # For non-Thai languages, preserve the original in_words
            print(
                f"Preserving original in_words for non-Thai language '{effective_lang}': {doc.in_words}"
            )
            args["use_thai_language"] = False
            args["original_in_words"] = doc.in_words

    except Exception as e:
        frappe.log_error(
            title="Thai Amount Enhancement Error",
            message=f"Error enhancing Thai amount for {doc.doctype} {doc.name}: {str(e)}",
        )


def _prepare_print_designer_context(print_format, args):
    """
    Prepare the context variables needed for Print Designer templates.
    This ensures both PDF and HTML generation have the required variables.
    """
    if not (
        print_format
        and print_format.print_designer
        and print_format.print_designer_body
    ):
        return

    try:
        # Check if print_designer_settings exists and is not None
        if not print_format.print_designer_settings:
            frappe.log_error(
                title="Print Designer Settings Missing",
                message=f"Print Format '{print_format.name}' has print_designer enabled but print_designer_settings is None",
            )
            return

        # Handle None or empty print_designer_settings
        if print_format.print_designer_settings:
            settings = json.loads(print_format.print_designer_settings)
        else:
            settings = {}

        # Get effective language for this print format
        effective_lang = get_effective_language(print_format.name)
        print(f"effective_lang {effective_lang}")

        # Always prepare the core elements
        args.update(
            {
                "headerElement": json.loads(print_format.print_designer_header or "[]"),
                "bodyElement": json.loads(print_format.print_designer_body or "[]"),
                "footerElement": json.loads(print_format.print_designer_footer or "[]"),
                "settings": settings,
                "pdf_generator": frappe.form_dict.get("pdf_generator", "wkhtmltopdf"),
                "effective_lang": effective_lang,
                "is_thai": is_thai_language(effective_lang),
            }
        )

        # Set pd_format for newer schema
        if not is_older_schema(settings=settings, current_version="1.1.0"):
            args.update(
                {
                    "pd_format": json.loads(
                        print_format.print_designer_print_format or "{}"
                    )
                }
            )
        else:
            args.update(
                {
                    "afterTableElement": json.loads(
                        print_format.print_designer_after_table or "[]"
                    )
                }
            )

        # Set send_to_jinja flag if not already set
        if "send_to_jinja" not in args:
            args["send_to_jinja"] = True

        # Note: Thai amount enhancement is now handled in the before_print hook
        # to ensure proper language detection from URL parameters

    except Exception as e:
        frappe.log_error(
            title="Print Designer Context Preparation Error",
            message=f"Error preparing context for print format '{print_format.name}': {str(e)}",
        )


# Note: _enhance_thai_amount_in_words function removed - Thai enhancement is now handled
# in the _handle_thai_amount_enhancement function within the before_print hook


# Test function to demonstrate the refactored language handling
def test_language_detection():
    """
    Test function to demonstrate how the refactored language detection works.
    This can be called from a custom script or bench console for testing.
    """
    print("=== Testing Language Detection ===")

    # Test 1: URL parameter takes priority
    frappe.form_dict["_lang"] = "ไทย"
    frappe.form_dict["format"] = "Sales Invoice"
    lang = get_effective_language("Sales Invoice")
    print(f"Test 1 - URL lang 'ไทย': {lang} (is_thai: {is_thai_language(lang)})")

    # Test 2: Without URL parameter, uses print format language
    frappe.form_dict.pop("_lang", None)
    lang = get_effective_language("Sales Invoice")
    print(f"Test 2 - No URL lang: {lang} (is_thai: {is_thai_language(lang)})")

    # Test 3: Test various Thai language indicators
    thai_variants = ["ไทย", "thai", "th", "TH", "Thai", "THAI"]
    for variant in thai_variants:
        is_thai = is_thai_language(variant)
        print(f"Test 3 - '{variant}' is Thai: {is_thai}")

    print("=== Language Detection Test Complete ===")


# Utility function for debugging language issues
def debug_current_language_context():
    """
    Debug function to show current language context.
    Useful for troubleshooting language-related issues.
    """
    print("=== Current Language Context ===")
    print(f"frappe.local.lang: {getattr(frappe.local, 'lang', 'Not set')}")
    print(f"URL _lang parameter: {frappe.form_dict.get('_lang', 'Not set')}")
    print(f"URL format parameter: {frappe.form_dict.get('format', 'Not set')}")

    format_name = frappe.form_dict.get("format")
    if format_name:
        effective_lang = get_effective_language(format_name)
        print(f"Effective language: {effective_lang}")
        print(f"Is Thai language: {is_thai_language(effective_lang)}")

    print("=== End Language Context ===")
    return {
        "local_lang": getattr(frappe.local, "lang", None),
        "url_lang": frappe.form_dict.get("_lang"),
        "format_name": format_name,
        "effective_lang": get_effective_language(format_name) if format_name else None,
    }