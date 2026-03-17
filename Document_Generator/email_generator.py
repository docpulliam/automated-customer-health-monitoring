# email_generator.py
from typing import Dict, Any


def _safe_str(x: Any, default: str = "") -> str:
    if x is None:
        return default
    s = str(x).strip()
    return s if s else default


def _to_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(str(x).replace(",", "").strip()))
    except Exception:
        return default


def _fmt_int(n: int) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


class EmailGenerator:
    """
    Generates the body text for the dealer Performance SnapShot email/text.
    NOTE: This version omits the Key Wins and YTD sections by design.
    """

    def __init__(self, dealer_data: Dict[str, Any]):
        self.data = dealer_data
        self.dealer_code = _safe_str(dealer_data.get("Dealer Code"), "UNKNOWN")
        self.dealer_name = _safe_str(
            dealer_data.get("Dealer Name"),
            f"Dealer {self.dealer_code}"
        )

    def _calculate_growth(self) -> float:
        """Calculates Quarter-over-Quarter growth (Q3 vs Q2)."""
        q2 = _to_int(self.data.get("Q2 Leads", 0), 0)
        q3 = _to_int(self.data.get("Q3 Leads", 0), 0)
        if q2 > 0:
            return ((q3 - q2) / q2) * 100.0
        return 0.0

    def _build_leads_section(self, growth_rate: float) -> str:
        """Build the leads summary section. Suppress QoQ if negative."""
        q2 = _to_int(self.data.get("Q2 Leads", 0), 0)
        q3 = _to_int(self.data.get("Q3 Leads", 0), 0)

        lines = [
            "E-SHOP LEADS (QoQ Analysis)",
            "Quarterly Leads:",
            f"**Total Leads Q3:** {_fmt_int(q3)}",
            f"**Total Leads Q2:** {_fmt_int(q2)}",
        ]

        if growth_rate >= 0:
            lines.append(f"**Quarter-over-Quarter Growth:** {growth_rate:.2f}%")

        return "\n".join(lines).strip()

    def _build_opportunities_section(self) -> str:
        """Derive opportunities based on audit signals."""
        opportunities = []

        # If we were unable to capture a screenshot for this dealer, it means
        # the ESHOP CTA is not currently present on the site. Call this out
        # explicitly as the first opportunity so it appears at the top of
        # the Opportunities list in both the email and PDF.
        has_screenshot = self.data.get("Has Screenshot", True)
        try:
            has_screenshot = bool(has_screenshot)
        except Exception:
            has_screenshot = True

        if not has_screenshot:
            opportunities.append(
                "ESHOP CTA button is currently MISSING which greatly affects your lead performance."
            )

        srp_cta_top = _safe_str(self.data.get("New SRP CTA Top")).upper()
        if srp_cta_top == "FALSE":
            opportunities.append(
                "**Optimize Placement:** Move the E-Shop buttons to the **top of the CTA stack** on your SRP/VDP "
                "for maximum visibility and conversion."
            )

        price_match = _safe_str(self.data.get("Price Match Syndication")).upper()
        if price_match == "NO":
            opportunities.append(
                "**Pricing Syndication:** E-SHOP Price Match is not active. Connect pricing syndication "
                "so competitive pricing displays clearly and drives conversions."
            )

        tag_content = _safe_str(self.data.get("Tag")).upper()
        if "EDPA ISSUE" in tag_content or "MISSING CREDIT APP DATA" in tag_content:
            opportunities.append(
                "**Credit Application Link:** Connect your RouteOne or DealerTrack credit app to E-SHOP "
                "to complete the digital deal and improve lead quality."
            )

        if not opportunities:
            return ""

        bullets = "\n".join(f"* {o}" for o in opportunities)
        return f"""
---

## 🛠️ Opportunities

Actions identified to increase unique lead volume and improve customer experience:

{bullets}
""".rstrip()

    def generate_email_text(self) -> str:
        """Compose the simplified body text (no Key Wins, no YTD)."""
        growth_rate = self._calculate_growth()
        leads_section = self._build_leads_section(growth_rate)
        opportunities_section = self._build_opportunities_section()

        # Keep this content tidy for both PDF and email contexts
        template = f"""
Below is your Q3 **Performance SnapShot**, focusing on E-SHOP lead performance.

---
## 📈 E-SHOP Performance Summary

{leads_section}

{opportunities_section}
""".strip()

        return template
