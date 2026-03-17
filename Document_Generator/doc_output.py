import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import re

class DocOutput:
    OUTPUT_FOLDER = "Health_Checks"

    def __init__(self, dealer_name: str, dealer_code: str, email_text: str,
                 screenshot_path: str = "", metrics: dict | None = None):
        self.dealer_name = dealer_name
        self.dealer_code = dealer_code
        self.email_text = email_text
        self.screenshot_path = screenshot_path
        self.metrics = metrics or {}

    def _fit_image(self, img_path, max_w, max_h):
        try:
            from PIL import Image as PILImage
            with PILImage.open(img_path) as im:
                w, h = im.size
        except Exception:
            return Image(img_path, width=max_w, height=max_h)
        scale = min(max_w / float(w), max_h / float(h))
        return Image(img_path, width=w * scale, height=h * scale)

    def _extract_numbers_from_text(self):
        q3_match = re.search(r"\*{0,2}Total Leads Q3:\*{0,2}\s*([\d,]+)", self.email_text, re.IGNORECASE)
        q2_match = re.search(r"\*{0,2}Total Leads Q2:\*{0,2}\s*([\d,]+)", self.email_text, re.IGNORECASE)
        growth_match = re.search(r"Quarter[- ]over[- ]Quarter Growth:\s*([\-0-9.,]+)%", self.email_text, re.IGNORECASE)
        q3_val = q3_match.group(1) if q3_match else "0"
        q2_val = q2_match.group(1) if q2_match else "0"
        growth_val = growth_match.group(1) if growth_match else None
        return q2_val, q3_val, growth_val

    def save_document(self):
        os.makedirs(self.OUTPUT_FOLDER, exist_ok=True)
        base_filename = f"{self.dealer_code}_{self.dealer_name.replace(' ', '_')}_Health_Check_Q3.pdf"
        full_filepath = os.path.join(self.OUTPUT_FOLDER, base_filename)

        doc = SimpleDocTemplate(
            full_filepath,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50,
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='HC_Title', fontSize=16, leading=20, spaceAfter=12, textColor=colors.black))
        styles.add(ParagraphStyle(name='HC_Section', fontSize=13, leading=16, spaceAfter=8, textColor=colors.black))
        styles.add(ParagraphStyle(name='HC_Body', fontSize=10, leading=13, spaceAfter=6))
        styles.add(ParagraphStyle(name='HC_Bullet', fontSize=10, leading=13, leftIndent=15, bulletIndent=5, spaceAfter=5))

        story = []
        story.append(Paragraph(f"<b>{self.dealer_name} ({self.dealer_code}) Performance SnapShot Q3</b>", styles['HC_Title']))
        story.append(Spacer(1, 6))
        story.append(Paragraph("Below is your Q3 'Performance SnapShot', focusing on E-SHOP lead performance.", styles['HC_Body']))
        story.append(Spacer(1, 10))

        # Prefer explicit metrics; fallback to regex
        show_growth = False
        if self.metrics:
            q2_num = int(self.metrics.get("Q2", 0))
            q3_num = int(self.metrics.get("Q3", 0))
            growth_pct = round(((q3_num - q2_num) / q2_num) * 100, 2) if q2_num > 0 else 0.0
            q2_val, q3_val = f"{q2_num:,}", f"{q3_num:,}"
            # show only if positive
            show_growth = growth_pct > 0
            growth_val = f"{growth_pct:.2f}"
        else:
            q2_val, q3_val, growth_val = self._extract_numbers_from_text()
            try:
                show_growth = growth_val is not None and float(growth_val) > 0
            except Exception:
                show_growth = False

        story.append(Paragraph("E-SHOP Performance Summary", styles['HC_Section']))
        story.append(Paragraph("E-SHOP LEADS (QoQ Analysis)", styles['HC_Body']))
        story.append(Paragraph(f"<b>Total Leads Q3:</b> {q3_val}", styles['HC_Body']))
        story.append(Paragraph(f"<b>Total Leads Q2:</b> {q2_val}", styles['HC_Body']))
        if show_growth:
            story.append(Paragraph(f"<b>Quarter-over-Quarter Growth:</b> {growth_val}%", styles['HC_Body']))
        story.append(Spacer(1, 8))

        # Opportunities as bullets (from email text)
        story.append(Paragraph("Opportunities", styles['HC_Section']))
        story.append(Paragraph("Actions identified to increase unique lead volume and improve customer experience:", styles['HC_Body']))
        story.append(Spacer(1, 4))
        for line in self.email_text.splitlines():
            if line.strip().startswith("* "):
                story.append(Paragraph(line.strip()[2:], styles['HC_Bullet']))
        story.append(Spacer(1, 10))

        # Screenshot
        if self.screenshot_path and os.path.exists(self.screenshot_path):
            story.append(Paragraph("Current E-Shop Button Stack:", styles['HC_Body']))
            story.append(Spacer(1, 6))
            story.append(self._fit_image(self.screenshot_path, max_w=460, max_h=260))
            story.append(Spacer(1, 18))

        # Next-Level Optimization
        story.append(Paragraph("Next-Level Optimization: New Features", styles['HC_Section']))
        story.append(Paragraph("<b>Deep Linking</b>", styles['HC_Body']))
        story.append(Paragraph(
            "Sends shoppers straight to a specific vehicle’s payment options "
            "(Trade-In, Credit Check, Test Drive, Payment Calculations) for faster conversion.",
            styles['HC_Body']
        ))
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Banners</b>", styles['HC_Body']))
        story.append(Paragraph(
            "Banners capture high-intent shoppers immediately upon landing on your site, "
            "driving urgency and engagement for current programs. Our marketing team updates banners "
            "throughout the year to keep incentives and campaigns fresh.",
            styles['HC_Body']
        ))
        story.append(Spacer(1, 8))

        banner_img_path = "White_WhiteJeep_Climb.png"
        if os.path.exists(banner_img_path):
            story.append(Paragraph("Example Banner:", styles['HC_Body']))
            story.append(Spacer(1, 6))
            story.append(self._fit_image(banner_img_path, max_w=470, max_h=160))
            story.append(Spacer(1, 6))

        try:
            doc.build(story)
            print(f"  ✅ Created PDF document: {full_filepath}")
        except Exception as e:
            print(f"  ❌ Failed (Document): {e}")
