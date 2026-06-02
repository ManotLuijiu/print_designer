# -*- coding: utf-8 -*-
"""
Address Utilities API for Thai Address Parsing

Provides smart extraction of address components from Address Line 1 and Line 2.
Uses dual-approach: keyword-based extraction + token analysis.

Usage:
    from print_designer.api.address_utils import extract_address_components
    result = extract_address_components("111/200 ถนนพุทธสาคร", "")
"""

import re
import frappe


@frappe.whitelist()
def extract_address_components(address_line1: str = "", address_line2: str = "") -> dict:
    """
    Extract address components from Address Line 1 and Line 2 fields.
    
    Combines two extraction approaches:
    1. Keyword-based extraction (primary) - recognizes Thai address keywords
    2. Token analysis (fallback) - parses remaining tokens
    
    Args:
        address_line1 (str): First address line (contains เลขที่, ถนน, etc.)
        address_line2 (str): Second address line (contains ซอย, หมู่, etc.)
    
    Returns:
        dict: Structured address components
            - house_no: เลขที่ (e.g., "111/200")
            - road: ถนน (e.g., "พุทธสาคร")
            - soi: ตรอก/ซอย (e.g., "10")
            - moo: หมู่ที่ (e.g., "5")
            - village: หมู่บ้าน (e.g., "สวนสยาม")
            - raw_remainder: unparsed text for debugging
    """
    # Initialize result dict
    result = {
        "house_no": "",
        "road": "",
        "soi": "",
        "moo": "",
        "village": "",
        "raw_remainder": ""
    }
    
    # Combine both lines for comprehensive parsing
    combined_text = f"{address_line1 or ''} {address_line2 or ''}".strip()
    
    if not combined_text:
        return result
    
    # ===== Layer 1: Keyword-Based Extraction =====
    
    # Extract เลขที่ (house number) - usually at start
    # Pattern: number with optional slash (e.g., "111/200", "99", "111-5")
    house_match = re.match(r'^(\d+[\/\d\-]*)\s*', combined_text)
    if house_match:
        result["house_no"] = house_match.group(1).strip()
    
    # Extract ถนน (road) - keyword "ถนน"
    road_match = re.search(r'ถนน\s+(.+?)(?=\s*(?:ซอย|ตรอก|หมู่\s*[0-9]|หมู่บ้าน)|$)', combined_text, re.IGNORECASE)
    if road_match:
        result["road"] = road_match.group(1).strip()
    
    # Extract ซอย/ตรอก (soi/lane)
    soi_match = re.search(r'(?:ซอย|ตรอก)\s+(.+?)(?=\s*(?:ถนน|หมู่\s*[0-9]|หมู่บ้าน)|$)', combined_text, re.IGNORECASE)
    if soi_match:
        result["soi"] = soi_match.group(1).strip()
    
    # Extract หมู่ที่ (moo/village number)
    moo_match = re.search(r'หมู่\s+(\d+)', combined_text, re.IGNORECASE)
    if moo_match:
        result["moo"] = moo_match.group(1).strip()
    
    # Extract หมู่บ้าน (village name)
    village_match = re.search(r'หมู่บ้าน\s+(.+?)(?:,|$)', combined_text, re.IGNORECASE)
    if village_match:
        result["village"] = village_match.group(1).strip()
    
    # ===== Layer 2: Token Analysis Fallback =====
    
    # If road not found via keyword, try to extract from remaining text
    if not result["road"]:
        # Remove house number from text
        remaining = combined_text
        if result["house_no"]:
            remaining = re.sub(r'^' + re.escape(result["house_no"]) + r'\s*', '', remaining)
        
        # Remove known keywords
        remaining = re.sub(r'(?:ถนน|ซอย|ตรอก|หมู่\s*\d+|หมู่บ้าน)\s*', '', remaining)
        remaining = remaining.strip()
        
        # If something remains and looks like a road name, use it
        if remaining and len(remaining) > 1:
            # Check if it's likely a road (no numbers, proper Thai chars)
            if not re.match(r'^\d+$', remaining):
                result["road"] = remaining
    
    # Build raw_remainder for debugging
    raw_parts = []
    if result["house_no"]:
        raw_parts.append(f"เลขที่: {result['house_no']}")
    if result["road"]:
        raw_parts.append(f"ถนน: {result['road']}")
    if result["soi"]:
        raw_parts.append(f"ซอย: {result['soi']}")
    if result["moo"]:
        raw_parts.append(f"หมู่: {result['moo']}")
    if result["village"]:
        raw_parts.append(f"หมู่บ้าน: {result['village']}")
    
    result["raw_remainder"] = " | ".join(raw_parts) if raw_parts else ""
    
    return result


@frappe.whitelist()
def test_extract_address(text: str = "") -> dict:
    """
    Test function to extract components from a single text string.
    Useful for debugging and development.
    
    Args:
        text (str): Single address text to parse
    
    Returns:
        dict: Same as extract_address_components
    """
    return extract_address_components(text, "")