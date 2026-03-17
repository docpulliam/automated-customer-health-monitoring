# main.py — code-prefix screenshot matching (SRP preferred), no Key Wins, PDF via DocOutput
# Updated to:
# - Treat missing screenshots as "missing ESHOP CTA" (still generate reports)
# - Normalize dealer codes (strip leading zeros, e.g. 08564 -> 8564)

import os
from data_loader import DataLoader
from email_generator import EmailGenerator
from doc_output import DocOutput
from lead_metrics_loader import LeadMetricsLoader

# --- Configuration ---
CSV_FILE_PATH = "demo_dataset/Master_Health_Check_Data.csv"
LEAD_REPORTS_FOLDER = "demo_dataset/lead_reports"
SCREENSHOT_FOLDER = "demo_dataset/button_stack_screenshots"

# Prefer SRP screenshots over VDP when both exist
PREFERRED_LABELS = ["CTA_TOP_SRP", "CTA_TOP_VDP"]

# Optional: allow a last-resort name fallback (disabled by default since you renamed files by code)
ENABLE_NAME_FALLBACK = False


def _label_rank(filename: str) -> int:
    """Rank files so SRP is preferred over VDP (lower is better)."""
    f = filename.lower()
    for idx, lab in enumerate(PREFERRED_LABELS):
        if lab.lower() in f:
            return idx
    return 99


def _normalize_code(code: str) -> str:
    """
    Normalize dealer codes so '08564' and '8564' are treated the same.
    Strips leading zeros but leaves a single '0' if that's all there is.
    """
    s = str(code).strip()
    s = s.lstrip("0")
    return s or "0"


def find_screenshot_by_code_prefix(dealer_code: str, dealer_name: str) -> str | None:
    """
    Find screenshot whose filename starts with '{dealer_code}_'.
    If multiple, prefer SRP over VDP, then newest by mtime.
    Optionally falls back to a name-based containment check if enabled.
    """
    if not os.path.isdir(SCREENSHOT_FOLDER):
        return None

    pngs = [f for f in os.listdir(SCREENSHOT_FOLDER) if f.lower().endswith(".png")]
    if not pngs:
        return None

    candidates = []
    prefix = f"{dealer_code}_"
    for f in pngs:
        if f.startswith(prefix):
            full = os.path.join(SCREENSHOT_FOLDER, f)
            try:
                mtime = os.path.getmtime(full)
            except Exception:
                mtime = 0
            candidates.append((_label_rank(f), -mtime, full))

    if candidates:
        # SRP (CTA_TOP_SRP) ranked before VDP, newest first within same rank
        candidates.sort(key=lambda t: (t[0], t[1]))
        return candidates[0][2]

    # Optional fallback by name (disabled by default since filenames now start with code)
    if ENABLE_NAME_FALLBACK and dealer_name:
        lname = dealer_name.lower()
        name_matches = []
        for f in pngs:
            if lname in f.lower():
                full = os.path.join(SCREENSHOT_FOLDER, f)
                try:
                    mtime = os.path.getmtime(full)
                except Exception:
                    mtime = 0
                name_matches.append((_label_rank(f), -mtime, full))
        if name_matches:
            name_matches.sort(key=lambda t: (t[0], t[1]))
            return name_matches[0][2]

    return None


def run_automation():
    """
    Generate PDF reports for all dealers:
    - Uses code-prefix screenshot matching (SRP preferred).
    - If no screenshot exists, still generates a report and treats this
      as "ESHOP CTA button is currently MISSING..." in Opportunities.
    - Normalizes dealer codes (e.g. 08564 -> 8564) across Master CSV,
      lead reports, and screenshot filenames.
    """
    # 1) Load audit data
    data_loader = DataLoader(CSV_FILE_PATH)
    all_audit_data = data_loader.load_data()
    if not all_audit_data:
        print("Automation halted due to audit data load error.")
        return

    # Normalize dealer codes when building the audit map
    audit_data_map: dict[str, dict] = {}
    for row in all_audit_data:
        raw_code = row.get("Dealer Code", "")
        norm_code = _normalize_code(raw_code)
        audit_data_map[norm_code] = row

    # 2) Lead reports
    if not os.path.isdir(LEAD_REPORTS_FOLDER):
        print(f"FATAL ERROR: The folder '{LEAD_REPORTS_FOLDER}' was not found.")
        return

    lead_files = [f for f in os.listdir(LEAD_REPORTS_FOLDER) if f.lower().endswith(".csv")]
    if not lead_files:
        print("No lead report files found. Exiting.")
        return

    print(f"Found {len(lead_files)} lead reports to process.\n")

    generated_count = 0
    skipped_count = 0  # errors only
    missing_screenshot_dealers: list[tuple[str, str]] = []

    # 3) Process each dealer file
    for filename in lead_files:
        print("=======================================================")
        print(f"  Processing file: {filename}")

        path = os.path.join(LEAD_REPORTS_FOLDER, filename)

        # Load metrics & dealer code from filename
        try:
            metrics_loader = LeadMetricsLoader(path)
            lead_metrics = metrics_loader.get_dealer_lead_metrics()
            raw_code = metrics_loader.dealer_code
            dealer_code = _normalize_code(raw_code)
        except Exception as e:
            print(f"  ❌ Failed to load metrics: {e}")
            skipped_count += 1
            continue

        dealer = audit_data_map.get(dealer_code)
        if not dealer:
            print(f"  ❌ Dealer code {dealer_code} not found in Master CSV.")
            skipped_count += 1
            continue

        dealer_name = dealer.get("Dealer Name", dealer_code)
        print(f"  Matched to Dealer: {dealer_name} ({dealer_code})")
        print(f"  Automated Lead Metrics: Q2={lead_metrics['Q2 Leads']}, Q3={lead_metrics['Q3 Leads']}")

        # 4) Screenshot (code-prefix)
        screenshot_path = find_screenshot_by_code_prefix(dealer_code, dealer_name)
        has_screenshot = bool(screenshot_path and os.path.exists(screenshot_path))

        if not has_screenshot:
            # No screenshot captured for this dealer. In our audit logic,
            # this means the ESHOP CTA is not currently present on the site.
            # We will still generate the report, but the Opportunities section
            # will call this out explicitly as the first bullet.
            print(f"  ⚠️ No screenshot found for {dealer_code}. Treating as missing ESHOP CTA.")
            missing_screenshot_dealers.append((dealer_code, dealer_name))
        else:
            print(f"  📸 Using screenshot: {screenshot_path}")

        # 5) Compose the email body (no Key Wins here; EmailGenerator already omits QoQ if <= 0)
        try:
            merged = {**dealer, **lead_metrics, "Has Screenshot": has_screenshot}
            email_text = EmailGenerator(merged).generate_email_text()

            # 6) Create PDF output
            doc = DocOutput(
                dealer_name=dealer_name,
                dealer_code=dealer_code,
                email_text=email_text,
                screenshot_path=screenshot_path if has_screenshot else None,
                metrics={"Q2": lead_metrics["Q2 Leads"], "Q3": lead_metrics["Q3 Leads"]},
            )
            doc.save_document()
            generated_count += 1
        except Exception as e:
            print(f"  ❌ Failed (Document): {e}")
            skipped_count += 1

    # 7) Summary
    print("\n--- SUMMARY ---")
    print(f"✅ Reports Generated: {generated_count}")
    print(f"⚠️ Skipped (errors only): {skipped_count}")
    print(f"📁 Output Folder: {os.path.abspath('Health_Checks')}")

    # Quick debug list of those with missing screenshots (treated as missing ESHOP CTA)
    if missing_screenshot_dealers:
        print("\nDealers with no screenshot found (treated as missing ESHOP CTA) — first 20:")
        for dc, dn in missing_screenshot_dealers[:20]:
            print(f"  - {dc}: {dn}")


if __name__ == "__main__":
    run_automation()
