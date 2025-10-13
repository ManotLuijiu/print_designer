#!/usr/bin/env python3
"""
Convert Frappe Print Format DocType JSON to Print Designer Export Format

This script converts Frappe Print Format DocType JSON (from .txt/.json files) into
the proper Print Designer export format that can be imported into Print Designer app.

Usage:
    # Single file conversion:
    python3 convert_print_format_to_designer_export.py <input_file> <output_file>

    # Batch folder conversion:
    python3 convert_print_format_to_designer_export.py <source_folder> <target_folder>

Examples:
    # Single file:
    python3 convert_print_format_to_designer_export.py "ERPNext Custom Print Format.txt" "sales_order_designer_export.json"

    # Batch folder:
    python3 convert_print_format_to_designer_export.py "./print_formats_raw" "./print_formats_converted"
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional


def create_designer_export_dict(
    print_format_dict: Dict,
    exported_by: str = "Conversion Script",
    frappe_version: str = "15.0.0"
) -> Dict:
    """
    Create Print Designer export structure from a Print Format dictionary.

    This is the core conversion function used by both:
    - Standalone script (for converting downloaded files)
    - Frappe API (for converting existing Print Formats)

    Args:
        print_format_dict: Print Format DocType dictionary
        exported_by: Name of user/script performing export
        frappe_version: Frappe version string

    Returns:
        Dict with Print Designer export structure
    """
    name = print_format_dict.get('name', 'Imported Print Format')
    doc_type = print_format_dict.get('doc_type', '')

    return {
        "export_date": datetime.now().isoformat(),
        "frappe_version": frappe_version,
        "print_designer_version": "1.7.8",
        "print_format": print_format_dict,
        "metadata": {
            "exported_by": exported_by,
            "original_name": name,
            "description": f"Converted Print Designer format for {doc_type}: {name}"
        }
    }


def convert_to_designer_export(input_file: str, output_file: str, quiet: bool = False) -> Dict:
    """
    Convert Print Format DocType JSON to Print Designer export format.

    Args:
        input_file: Path to input .txt/.json file containing Print Format DocType JSON
        output_file: Path to output .json file for Print Designer import
        quiet: If True, suppress console output

    Returns:
        Dict with conversion result info
    """
    # Read the Print Format DocType JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        print_format_doc = json.load(f)

    # Use shared conversion function
    designer_export = create_designer_export_dict(
        print_format_dict=print_format_doc,
        exported_by="Conversion Script",
        frappe_version="15.0.0"
    )

    # Extract fields for return value
    name = print_format_doc.get('name', 'Imported Print Format')
    doc_type = print_format_doc.get('doc_type', '')

    # Write the converted format
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(designer_export, f, indent=2, ensure_ascii=False)

    if not quiet:
        print("✅ Conversion successful!")
        print(f"   Input:  {input_file}")
        print(f"   Output: {output_file}")
        print(f"   Print Format: {name}")
        print(f"   DocType: {doc_type}")

    return {
        "success": True,
        "name": name,
        "doc_type": doc_type,
        "input_file": input_file,
        "output_file": output_file
    }


def convert_folder_batch(source_folder: str, target_folder: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Convert all Print Format files in a source folder to target folder.

    Args:
        source_folder: Path to folder containing .txt/.json files
        target_folder: Path to folder where converted files will be saved

    Returns:
        Tuple of (successful_conversions, failed_conversions)
    """
    source_path = Path(source_folder)
    target_path = Path(target_folder)

    # Validate source folder
    if not source_path.exists():
        raise FileNotFoundError(f"Source folder not found: {source_folder}")

    if not source_path.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_folder}")

    # Create target folder if it doesn't exist
    target_path.mkdir(parents=True, exist_ok=True)

    # Find all .txt and .json files in source folder
    input_files = list(source_path.glob('*.txt')) + list(source_path.glob('*.json'))

    if not input_files:
        print(f"⚠️  No .txt or .json files found in {source_folder}")
        return [], []

    print(f"\n📁 Batch Conversion: {source_folder} → {target_folder}")
    print(f"   Found {len(input_files)} file(s) to convert\n")

    successful = []
    failed = []

    for idx, input_file in enumerate(input_files, 1):
        # Generate output filename
        output_filename = f"{input_file.stem}_Designer_Export.json"
        output_file = target_path / output_filename

        print(f"[{idx}/{len(input_files)}] Converting: {input_file.name}...")

        try:
            result = convert_to_designer_export(
                str(input_file),
                str(output_file),
                quiet=True
            )
            successful.append(result)
            print(f"   ✅ Success: {result['name']} ({result['doc_type']})")

        except json.JSONDecodeError as e:
            error_info = {
                "input_file": str(input_file),
                "error": f"Invalid JSON: {str(e)}"
            }
            failed.append(error_info)
            print(f"   ❌ Failed: Invalid JSON - {str(e)}")

        except Exception as e:
            error_info = {
                "input_file": str(input_file),
                "error": str(e)
            }
            failed.append(error_info)
            print(f"   ❌ Failed: {str(e)}")

        print()  # Empty line between files

    return successful, failed


def print_batch_summary(successful: List[Dict], failed: List[Dict]):
    """Print batch conversion summary."""
    total = len(successful) + len(failed)

    print("=" * 60)
    print("📊 BATCH CONVERSION SUMMARY")
    print("=" * 60)
    print(f"Total Files: {total}")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    print()

    if successful:
        print("✅ Successfully Converted:")
        for result in successful:
            print(f"   • {result['name']} ({result['doc_type']})")
            print(f"     → {result['output_file']}")
        print()

    if failed:
        print("❌ Failed Conversions:")
        for error in failed:
            print(f"   • {Path(error['input_file']).name}")
            print(f"     Error: {error['error']}")
        print()

    print("💡 All converted files can now be imported into Print Designer")
    print("=" * 60)


def main():
    if len(sys.argv) != 3:
        print("❌ Usage: python3 convert_print_format_to_designer_export.py <source> <target>")
        print("\nModes:")
        print("   1. Single file: <input_file> <output_file>")
        print("   2. Batch folder: <source_folder> <target_folder>")
        print("\nExamples:")
        print("   # Single file:")
        print('   python3 convert_print_format_to_designer_export.py "format.txt" "output.json"')
        print("\n   # Batch folder:")
        print('   python3 convert_print_format_to_designer_export.py "./raw_formats" "./converted"')
        sys.exit(1)

    source = sys.argv[1]
    target = sys.argv[2]

    try:
        # Check if source is a file or folder
        source_path = Path(source)

        if not source_path.exists():
            print(f"❌ Error: Source not found: {source}")
            sys.exit(1)

        if source_path.is_file():
            # Single file conversion
            print("🔄 Mode: Single File Conversion\n")
            convert_to_designer_export(source, target)
            print(f"\n💡 You can now import '{target}' into Print Designer")

        elif source_path.is_dir():
            # Batch folder conversion
            print("🔄 Mode: Batch Folder Conversion")
            successful, failed = convert_folder_batch(source, target)
            print_batch_summary(successful, failed)

            # Exit with error code if any conversions failed
            if failed:
                sys.exit(1)

        else:
            print(f"❌ Error: Invalid source path: {source}")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
