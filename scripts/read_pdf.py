import fitz  # PyMuPDF
import sys
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Extract text from a heavy PDF iteratively.")
    parser.add_argument("pdf_path", help="Absolute path to the PDF file")
    parser.add_argument("--start", type=int, default=1, help="Start page (1-indexed)")
    parser.add_argument("--end", type=int, default=None, help="End page (inclusive, 1-indexed)")
    parser.add_argument("--max_pages", type=int, default=20, help="Maximum number of pages to read at once to prevent context overflow")
    
    # Simple workaround to handle Zed's flat string injection without quotes breaking argparse
    import shlex
    # Drop the first arg (script name)
    args_str = " ".join(sys.argv[1:])
    try:
        parsed_args = shlex.split(args_str)
        args = parser.parse_args(parsed_args)
    except Exception:
        # Fallback
        args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: Provided PDF path does not exist: {args.pdf_path}")
        sys.exit(1)

    try:
        doc = fitz.open(args.pdf_path)
    except Exception as e:
        print(f"Error: Failed to open PDF. Is it a valid PDF file? Details: {e}")
        sys.exit(1)

    total_pages = len(doc)
    
    # 0-indexed conversion for fitz
    start_idx = max(0, args.start - 1)
    
    if args.end is not None:
        end_idx = min(args.end, total_pages)
    else:
        end_idx = total_pages
        
    # Apply safety limit
    pages_to_read = end_idx - start_idx
    if pages_to_read > args.max_pages:
        end_idx = start_idx + args.max_pages
        warning = f"\n[!] SAFETY LIMIT TRIGGERED: To prevent context overflow, reading is restricted to {args.max_pages} pages per call.\n[!] Please call the skill again with `--start {end_idx + 1}` to read the next chunk of pages."
    else:
        warning = ""

    print(f"[{args.pdf_path}] - Total Pages: {total_pages}")
    print(f"Reading Pages {start_idx + 1} to {end_idx}...\n")
    print("=" * 60)

    for i in range(start_idx, end_idx):
        try:
            page = doc[i]
            text = page.get_text()
            print(f"\n--- PAGE {i + 1} ---\n")
            print(text.strip())
        except Exception as e:
            print(f"[Error reading page {i + 1}: {e}]")
            
    print("\n" + "=" * 60)
    print(f"Finished reading {end_idx - start_idx} pages.")
    
    if warning:
        print(warning)

if __name__ == "__main__":
    main()
