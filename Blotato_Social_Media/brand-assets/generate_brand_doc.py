#!/usr/bin/env python3
"""Generate AIwithDhruv Brand Bible PDF using ReportLab."""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Colors ──────────────────────────────────────────────────────────
CYAN = HexColor("#00c8e8")
CYAN_DARK = HexColor("#00a8b8")
DARK_BG = HexColor("#0a0a0f")
CARD_BG = HexColor("#16161e")
PURPLE = HexColor("#c842f5")
GREEN = HexColor("#00ff88")
WARM = HexColor("#ff6b35")
AMBER = HexColor("#f59e0b")
TEXT_PRIMARY = HexColor("#e8e8f0")
TEXT_SECONDARY = HexColor("#9090a0")
NAVY = HexColor("#1a1a2e")
INDIGO = HexColor("#4361EE")
LIGHT_GRAY = HexColor("#f8f9fa")
MEDIUM_GRAY = HexColor("#6b7280")
DARK_TEXT = HexColor("#1a1a2e")
BODY_TEXT = HexColor("#374151")
BORDER_LIGHT = HexColor("#e5e7eb")
ACCENT_BLUE = HexColor("#0ea5e9")
WHITE_BG = HexColor("#ffffff")

OUT_DIR = Path(__file__).parent
PDF_PATH = OUT_DIR / "AIwithDhruv-Brand-Bible.pdf"

# Try to load logo images
CIRCULAR_LOGO = OUT_DIR / "Circular 2.0.png"
SQUARE_LOGO = OUT_DIR / "Square 2.0.png"
DHRUV_SQUARE = OUT_DIR / "dhruv-square.png"


# ── Styles ──────────────────────────────────────────────────────────
def make_styles():
    s = {}
    s["title"] = ParagraphStyle(
        "Title", fontName="Helvetica-Bold", fontSize=28,
        textColor=DARK_TEXT, leading=34, alignment=TA_LEFT,
        spaceAfter=4*mm
    )
    s["subtitle"] = ParagraphStyle(
        "Subtitle", fontName="Helvetica", fontSize=13,
        textColor=MEDIUM_GRAY, leading=18, alignment=TA_LEFT,
        spaceAfter=8*mm
    )
    s["h1"] = ParagraphStyle(
        "H1", fontName="Helvetica-Bold", fontSize=20,
        textColor=DARK_TEXT, leading=26, spaceBefore=10*mm,
        spaceAfter=4*mm
    )
    s["h2"] = ParagraphStyle(
        "H2", fontName="Helvetica-Bold", fontSize=14,
        textColor=ACCENT_BLUE, leading=20, spaceBefore=6*mm,
        spaceAfter=3*mm
    )
    s["h3"] = ParagraphStyle(
        "H3", fontName="Helvetica-Bold", fontSize=12,
        textColor=DARK_TEXT, leading=16, spaceBefore=4*mm,
        spaceAfter=2*mm
    )
    s["body"] = ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=10,
        textColor=BODY_TEXT, leading=15, spaceAfter=3*mm
    )
    s["body_bold"] = ParagraphStyle(
        "BodyBold", fontName="Helvetica-Bold", fontSize=10,
        textColor=DARK_TEXT, leading=15, spaceAfter=2*mm
    )
    s["bullet"] = ParagraphStyle(
        "Bullet", fontName="Helvetica", fontSize=10,
        textColor=BODY_TEXT, leading=15, leftIndent=12*mm,
        bulletIndent=6*mm, spaceAfter=1.5*mm
    )
    s["small"] = ParagraphStyle(
        "Small", fontName="Helvetica", fontSize=8.5,
        textColor=MEDIUM_GRAY, leading=12, spaceAfter=2*mm
    )
    s["label"] = ParagraphStyle(
        "Label", fontName="Helvetica-Bold", fontSize=9,
        textColor=MEDIUM_GRAY, leading=12, spaceAfter=1*mm,
        textTransform="uppercase"
    )
    s["quote"] = ParagraphStyle(
        "Quote", fontName="Helvetica-Oblique", fontSize=12,
        textColor=ACCENT_BLUE, leading=18, leftIndent=8*mm,
        rightIndent=8*mm, spaceBefore=4*mm, spaceAfter=4*mm,
        borderPadding=4*mm
    )
    s["footer"] = ParagraphStyle(
        "Footer", fontName="Helvetica", fontSize=7.5,
        textColor=MEDIUM_GRAY, alignment=TA_CENTER
    )
    s["cover_title"] = ParagraphStyle(
        "CoverTitle", fontName="Helvetica-Bold", fontSize=36,
        textColor=DARK_TEXT, leading=44, alignment=TA_CENTER,
        spaceAfter=6*mm
    )
    s["cover_tagline"] = ParagraphStyle(
        "CoverTagline", fontName="Helvetica", fontSize=14,
        textColor=MEDIUM_GRAY, leading=20, alignment=TA_CENTER,
        spaceAfter=3*mm
    )
    s["cover_sub"] = ParagraphStyle(
        "CoverSub", fontName="Helvetica", fontSize=11,
        textColor=BODY_TEXT, leading=16, alignment=TA_CENTER,
        spaceAfter=8*mm
    )
    s["toc"] = ParagraphStyle(
        "TOC", fontName="Helvetica", fontSize=11,
        textColor=BODY_TEXT, leading=20, leftIndent=6*mm,
        spaceAfter=1*mm
    )
    return s


def hr():
    return HRFlowable(
        width="100%", thickness=0.5, color=BORDER_LIGHT,
        spaceBefore=4*mm, spaceAfter=4*mm
    )


def color_swatch_table(colors_list):
    """Create a color swatch table."""
    rows = []
    for name, hex_val, usage in colors_list:
        color = HexColor(hex_val)
        swatch = Table(
            [[""]],
            colWidths=[12*mm], rowHeights=[12*mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), color),
                ("ROUNDEDCORNERS", [3, 3, 3, 3]),
                ("BOX", (0, 0), (0, 0), 0.5, BORDER_LIGHT),
            ])
        )
        rows.append([swatch, name, hex_val, usage])

    t = Table(rows, colWidths=[18*mm, 40*mm, 28*mm, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (1, 0), (-1, -1), 9),
        ("TEXTCOLOR", (1, 0), (1, -1), DARK_TEXT),
        ("TEXTCOLOR", (2, 0), (2, -1), MEDIUM_GRAY),
        ("TEXTCOLOR", (3, 0), (3, -1), BODY_TEXT),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4*mm),
    ]))
    return t


def info_table(data, col1_width=40*mm):
    """Create a key-value info table."""
    t = Table(data, colWidths=[col1_width, None])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), DARK_TEXT),
        ("TEXTCOLOR", (1, 0), (1, -1), BODY_TEXT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2*mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2*mm),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, BORDER_LIGHT),
    ]))
    return t


def pricing_table(data, headers):
    """Create a pricing table."""
    all_rows = [headers] + data
    t = Table(all_rows, colWidths=[55*mm, 35*mm, None])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f1f5f9")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), BODY_TEXT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5*mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5*mm),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("LINEBEFORE", (1, 0), (1, -1), 0.3, BORDER_LIGHT),
        ("LINEBEFORE", (2, 0), (2, -1), 0.3, BORDER_LIGHT),
    ]))
    return t


def build_pdf():
    styles = make_styles()
    doc = SimpleDocTemplate(
        str(PDF_PATH), pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title="AIwithDhruv Brand Bible",
        author="Dhruv Tomar",
    )
    story = []

    # ── PAGE 1: COVER ────────────────────────────────────────────────

    story.append(Spacer(1, 25*mm))

    # Logo
    if CIRCULAR_LOGO.exists():
        logo = Image(str(CIRCULAR_LOGO), width=50*mm, height=50*mm)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 8*mm))

    story.append(Paragraph("AIwithDhruv", styles["cover_title"]))
    story.append(Paragraph("Brand Bible & Identity Guide", styles["cover_tagline"]))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Turning AI Into Outcomes",
        styles["quote"]
    ))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "Comprehensive brand identity, visual guidelines, messaging framework,<br/>"
        "service catalog, content strategy, and positioning for the AIwithDhruv brand.<br/><br/>"
        "Version 1.0 | March 2026",
        styles["cover_sub"]
    ))
    story.append(Spacer(1, 15*mm))

    # Dhruv's photo
    if DHRUV_SQUARE.exists():
        photo = Image(str(DHRUV_SQUARE), width=40*mm, height=40*mm)
        photo.hAlign = "CENTER"
        story.append(photo)
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph("Dhruv Tomar", ParagraphStyle(
            "CenterBold", fontName="Helvetica-Bold", fontSize=12,
            textColor=DARK_TEXT, alignment=TA_CENTER
        )))
        story.append(Paragraph(
            "AI Architect &amp; Product Lead",
            ParagraphStyle("CenterSub", fontName="Helvetica", fontSize=9,
                           textColor=MEDIUM_GRAY, alignment=TA_CENTER, spaceAfter=4*mm)
        ))

    story.append(PageBreak())

    # ── PAGE 2: TABLE OF CONTENTS ────────────────────────────────────

    story.append(Paragraph("Contents", styles["h1"]))
    story.append(hr())

    toc_items = [
        "1. Brand Identity & Core Information",
        "2. Visual Identity — Colors, Typography & Style",
        "3. Logo Usage & Brand Assets",
        "4. Brand Positioning & Messaging",
        "5. Social Media Presence & Links",
        "6. Content Strategy & Voice",
        "7. Products & Portfolio",
        "8. Service Catalog & Pricing",
        "9. Technical Stack & Infrastructure",
        "10. Proposal & Sales Framework",
        "11. Trust Signals & Proof Points",
        "12. About Dhruv Tomar",
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles["toc"]))

    story.append(PageBreak())

    # ── SECTION 1: BRAND IDENTITY ────────────────────────────────────

    story.append(Paragraph("1. Brand Identity & Core Information", styles["h1"]))
    story.append(hr())

    story.append(info_table([
        ["Brand Name", "AIwithDhruv"],
        ["Created By", "Dhruv Tomar"],
        ["Tagline", "Turning AI Into Outcomes"],
        ["Headline", "I Don't Build Features. I Ship Entire Businesses."],
        ["Subtitle", "Product, pipeline, marketing, revenue \u2014 one AI architect, zero handoffs."],
        ["Website", "https://aiwithdhruv.com"],
        ["Email", "aiwithdhruv@gmail.com"],
        ["Phone", "+91 8770101822"],
        ["Location", "India (serving clients worldwide)"],
        ["Founded", "2024"],
    ]))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "AIwithDhruv is the personal brand and consulting practice of Dhruv Tomar \u2014 "
        "an AI Architect &amp; Product Lead who builds end-to-end AI systems that run businesses autonomously. "
        "From AI voice agents and sales pipelines to browser automation and RAG systems, "
        "the brand represents production-grade AI engineering, not demos or POCs.",
        styles["body"]
    ))

    story.append(Paragraph("Core Philosophy", styles["h3"]))
    bullets = [
        "Build, don't just advise \u2014 every system is shipped, deployed, and running in production",
        "Consultant + Engineer + Product Owner \u2014 three roles in one person",
        "Teach for free, build for money \u2014 content is marketing, not revenue",
        "Horizontal infrastructure over vertical micro-SaaS \u2014 sell the engine, not one niche app",
        "Open source first \u2014 43+ published skills, community-driven growth",
    ]
    for b in bullets:
        story.append(Paragraph(f"\u2022 {b}", styles["bullet"]))

    story.append(PageBreak())

    # ── SECTION 2: VISUAL IDENTITY ───────────────────────────────────

    story.append(Paragraph("2. Visual Identity", styles["h1"]))
    story.append(hr())

    story.append(Paragraph("Primary Color Palette", styles["h2"]))
    story.append(Paragraph(
        "The AIwithDhruv brand uses a dark-mode-first aesthetic with cyan as the primary accent, "
        "evoking technology, intelligence, and precision. Purple and warm orange serve as secondary accents.",
        styles["body"]
    ))

    story.append(color_swatch_table([
        ("Cyan Primary", "#00c8e8", "Brand core, CTAs, glows, accents"),
        ("Cyan Dark", "#00a8b8", "Hover states, secondary cyan"),
        ("Purple Glow", "#c842f5", "AI/magic visual effects"),
        ("Green Accent", "#00ff88", "Live status, success states"),
        ("Warm Orange", "#ff6b35", "Energy, CTA highlights"),
        ("Amber", "#f59e0b", "Warnings, warm glow effects"),
    ]))

    story.append(Paragraph("Background Palette (Dark Theme)", styles["h2"]))
    story.append(color_swatch_table([
        ("BG Primary", "#0a0a0f", "Page background"),
        ("BG Secondary", "#111118", "Section backgrounds"),
        ("BG Card", "#16161e", "Card surfaces"),
        ("Navy Dark", "#1a1a2e", "Text color on light backgrounds"),
    ]))

    story.append(Paragraph("Text Colors", styles["h2"]))
    story.append(color_swatch_table([
        ("Text Primary", "#e8e8f0", "Headings, body text (dark mode)"),
        ("Text Secondary", "#9090a0", "Subtext, descriptions"),
        ("Text Muted", "#78788a", "Labels, timestamps"),
        ("Body Text", "#374151", "Body text (light mode / PDFs)"),
    ]))

    story.append(Paragraph("Typography", styles["h2"]))
    story.append(info_table([
        ["Primary Font", "Geist Sans (Google Fonts)"],
        ["Monospace", "Geist Mono"],
        ["Fallback", "Helvetica, Arial, sans-serif"],
        ["Headings", "Bold, large sizes (8xl for hero, 2xl\u20134xl for sections)"],
        ["Body", "Regular weight, 10\u201312pt, generous leading"],
        ["PDF Documents", "Helvetica family, clean white backgrounds"],
    ]))

    story.append(Paragraph("Visual Style Rules", styles["h2"]))
    style_rules = [
        "Dark-mode first \u2014 always design for dark backgrounds unless creating print/PDF",
        "Soft cone glows (Huly-style) \u2014 never hard-edged gradients",
        "Ambient grid backgrounds with 60px spacing and subtle opacity",
        "Glass morphism with backdrop blur on cards and overlays",
        "Grain overlay at 2.5% opacity for texture",
        "Metallic text effects for hero headings (gradient + glow)",
        "3D perspective tilt cards on hover (perspective: 1000px)",
        "Floating particle animations with sine/cosine math",
        "Dhruv's photo style: always black t-shirt, glasses, cinematic lighting",
        "Thumbnails: dark background, purple/teal neon accents, MacBook Pro visible",
    ]
    for r in style_rules:
        story.append(Paragraph(f"\u2022 {r}", styles["bullet"]))

    story.append(PageBreak())

    # ── SECTION 3: LOGO USAGE ────────────────────────────────────────

    story.append(Paragraph("3. Logo Usage & Brand Assets", styles["h1"]))
    story.append(hr())

    story.append(Paragraph("Primary Logos", styles["h2"]))
    story.append(Paragraph(
        "The AIwithDhruv logo features the brand name with a stylized AI brain circuit icon. "
        "The tagline 'Turning AI Into Outcomes' appears below the brand name. "
        "Two formats are available:",
        styles["body"]
    ))

    # Show logos side by side if available
    logo_data = []
    if CIRCULAR_LOGO.exists():
        logo_data.append([
            Image(str(CIRCULAR_LOGO), width=35*mm, height=35*mm),
            "Circular Logo\nUse for: profile pictures,\navatars, social media icons,\nfavicons"
        ])
    if SQUARE_LOGO.exists():
        logo_data.append([
            Image(str(SQUARE_LOGO), width=35*mm, height=35*mm),
            "Square Logo\nUse for: thumbnails,\nheader images, OG images,\nbrand cards"
        ])
    if logo_data:
        lt = Table(logo_data, colWidths=[45*mm, None])
        lt.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (1, 0), (1, -1), 10),
            ("TEXTCOLOR", (1, 0), (1, -1), BODY_TEXT),
            ("LEFTPADDING", (1, 0), (1, -1), 6*mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6*mm),
        ]))
        story.append(lt)

    story.append(Paragraph("Dhruv Tomar \u2014 Profile Photo", styles["h2"]))
    if DHRUV_SQUARE.exists():
        photo_table = Table(
            [[
                Image(str(DHRUV_SQUARE), width=35*mm, height=35*mm),
                "Square headshot (1536\u00d71536px)\nUse for: speaker bios, about sections,\n"
                "social profiles, press kits.\n\nStyle: Black t-shirt, glasses,\n"
                "cinematic studio lighting,\nteal/warm ambient background."
            ]],
            colWidths=[45*mm, None]
        )
        photo_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (1, 0), (1, -1), 10),
            ("TEXTCOLOR", (1, 0), (1, -1), BODY_TEXT),
            ("LEFTPADDING", (1, 0), (1, -1), 6*mm),
        ]))
        story.append(photo_table)

    story.append(Paragraph("Logo Don'ts", styles["h3"]))
    donts = [
        "Never stretch or distort the logo proportions",
        "Never use the logo on a busy or cluttered background without contrast overlay",
        "Never change the logo colors outside of the approved palette",
        "Never add drop shadows, 3D effects, or outlines to the logo",
        "Never place text too close to the logo \u2014 maintain clear space equal to the 'A' height",
    ]
    for d in donts:
        story.append(Paragraph(f"\u2022 {d}", styles["bullet"]))

    story.append(Paragraph("Brand Assets Inventory", styles["h2"]))
    story.append(info_table([
        ["Circular 2.0.png", "Circular logo with brain icon + tagline"],
        ["Square 2.0.png", "Square logo with brain icon + tagline"],
        ["dhruv-square.png", "1536\u00d71536 headshot (square crop)"],
        ["dhruv-original.png", "2752\u00d71536 headshot (widescreen)"],
    ]))

    story.append(PageBreak())

    # ── SECTION 4: POSITIONING ───────────────────────────────────────

    story.append(Paragraph("4. Brand Positioning & Messaging", styles["h1"]))
    story.append(hr())

    story.append(Paragraph(
        '"I Don\'t Build Features. I Ship Entire Businesses."',
        styles["quote"]
    ))

    story.append(Paragraph("Positioning Statement", styles["h2"]))
    story.append(Paragraph(
        "AIwithDhruv is the go-to AI Architect &amp; Product Lead for founders and businesses who need "
        "production-grade AI systems \u2014 not just prototypes. Dhruv combines deep technical expertise "
        "(LangGraph, RAG, voice AI, browser automation) with business acumen (product strategy, "
        "revenue growth, client management) to deliver AI systems that generate real revenue. "
        "He took a B2B SaaS from 0 to 10 Cr ARR, trained 2200+ engineers, and has 20+ production "
        "systems running live.",
        styles["body"]
    ))

    story.append(Paragraph("Key Differentiators", styles["h2"]))
    diffs = [
        ("3-in-1 Operator", "Consultant + Engineer + Product Owner. Companies hire 3 separate people for what Dhruv does alone."),
        ("Production, Not Demos", "Every system is deployed, monitored, and running. Not a POC shop."),
        ("Zero Handoffs", "End-to-end delivery: product design, engineering, marketing integration, revenue tracking."),
        ("Proven Scale", "0\u219210 Cr ARR growth, 218 automation workflows, 20+ live systems."),
        ("Open Source Authority", "43+ published skills, community-adopted frameworks, transparent infrastructure."),
        ("AI-Native Workflow", "26 custom AI agents, 17 MCP servers, 149 skills \u2014 the most advanced personal AI setup in the industry."),
    ]
    for title, desc in diffs:
        story.append(Paragraph(f"<b>{title}:</b> {desc}", styles["body"]))

    story.append(Paragraph("Messaging Do's and Don'ts", styles["h2"]))

    msg_table = Table(
        [
            ["DO", "DON'T"],
            ["Say 'I built' or 'I shipped'", "Say 'I can build' or 'I could build'"],
            ["Lead with specific numbers and results", "Use vague claims ('best in class')"],
            ["Frame AI as a tool in a business system", "Hype AI as magic or sentient"],
            ["Show production URLs and live demos", "Show mockups or Figma screenshots"],
            ["Use 'production-grade' and 'autonomous'", "Use 'cutting-edge' or 'revolutionary'"],
            ["Reference specific tech (LangGraph, n8n, RAG)", "Use generic terms ('AI-powered')"],
        ],
        colWidths=[85*mm, 85*mm]
    )
    msg_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), HexColor("#dcfce7")),
        ("BACKGROUND", (1, 0), (1, 0), HexColor("#fee2e2")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), BODY_TEXT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5*mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5*mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 3*mm),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("LINEBEFORE", (1, 0), (1, -1), 0.5, BORDER_LIGHT),
    ]))
    story.append(msg_table)

    story.append(PageBreak())

    # ── SECTION 5: SOCIAL MEDIA ──────────────────────────────────────

    story.append(Paragraph("5. Social Media Presence & Links", styles["h1"]))
    story.append(hr())

    story.append(info_table([
        ["Website", "https://aiwithdhruv.com"],
        ["LinkedIn", "https://linkedin.com/in/aiwithdhruv"],
        ["YouTube", "https://youtube.com/@aiwithdhruv"],
        ["GitHub", "https://github.com/aiagentwithdhruv"],
        ["X (Twitter)", "https://x.com/aiwithdhruv"],
        ["Calendly", "https://calendly.com/aiwithdhruv/makeaiworkforyou"],
        ["Euron (Teaching)", "https://euron.one"],
        ["n8n Instance", "https://n8n.aiwithdhruv.cloud"],
    ]))

    story.append(Paragraph("LinkedIn Bio", styles["h2"]))
    story.append(Paragraph(
        "<b>Headline:</b> AI Automation Engineer | I build systems that run your business "
        "while you sleep | n8n, Voice AI, Claude",
        styles["body"]
    ))
    story.append(Paragraph(
        "LinkedIn is the primary content distribution channel. The profile emphasizes: "
        "AI Voice Agents (24/7 answering, qualifying, booking), n8n Workflow Automation (200+ production workflows), "
        "AI Chatbots (RAG pipeline, lead capture, guardrails), Full AI Sales Systems (QuotaHit.com), "
        "and Lead Generation Autopilot.",
        styles["body"]
    ))

    story.append(Paragraph("Social Media Handles (Consistent)", styles["h2"]))
    story.append(Paragraph(
        "All platforms use <b>aiwithdhruv</b> as the handle for brand consistency. "
        "GitHub uses <b>aiagentwithdhruv</b> (legacy handle).",
        styles["body"]
    ))

    story.append(PageBreak())

    # ── SECTION 6: CONTENT STRATEGY ──────────────────────────────────

    story.append(Paragraph("6. Content Strategy & Voice", styles["h1"]))
    story.append(hr())

    story.append(Paragraph("Brand Voice", styles["h2"]))
    story.append(Paragraph(
        "The AIwithDhruv voice is direct, technical, and results-oriented. It's the voice of someone "
        "who ships, not someone who theorizes. Think 'senior engineer explaining to a smart peer' \u2014 "
        "never condescending, never vague, always specific.",
        styles["body"]
    ))
    voice_traits = [
        ("Direct:", "Lead with the answer. No fluff preambles."),
        ("Technical but accessible:", "Use real tech names (LangGraph, n8n, RAG) but explain the business impact."),
        ("First-person:", "'I built' framing, not 'you should build'."),
        ("Numbers-driven:", "Always include specific metrics, costs, timelines."),
        ("Authentic:", "Share real failures too. Not everything works first time."),
        ("Non-corporate:", "Conversational tone. No buzzword soup."),
    ]
    for trait, desc in voice_traits:
        story.append(Paragraph(f"\u2022 <b>{trait}</b> {desc}", styles["bullet"]))

    story.append(Paragraph("Content Distribution Strategy", styles["h2"]))
    story.append(Paragraph(
        "<b>Flow:</b> Post (hook) \u2192 First Comment (links + context) \u2192 Article (deep-dive) \u2192 YouTube (visual demo)",
        styles["body"]
    ))

    story.append(Paragraph("LinkedIn Content Mix", styles["h3"]))
    content_mix = [
        ("40%", "Pain point callouts \u2014 specific problems your audience faces"),
        ("30%", "Proof/results with screenshots \u2014 show live systems, real numbers"),
        ("20%", "Educational how-to \u2014 step-by-step breakdowns of what you built"),
        ("10%", "Direct CTA \u2014 'DM me AI' or link to services"),
    ]
    for pct, desc in content_mix:
        story.append(Paragraph(f"\u2022 <b>{pct}</b> \u2014 {desc}", styles["bullet"]))

    story.append(Paragraph("Content Rules", styles["h3"]))
    content_rules = [
        "Always include a visual (screenshot, video, diagram) \u2014 never text-only",
        "Engage on 10 posts before and after publishing",
        "Reply to ALL comments within 2 hours",
        "Max 2 prompts to generate content \u2014 if it needs more, the idea isn't clear",
        "No content calendars \u2014 post when there's something real to share",
        "Add Euron CTA subtly (not every post)",
        "Tags/descriptions max 450 characters",
    ]
    for r in content_rules:
        story.append(Paragraph(f"\u2022 {r}", styles["bullet"]))

    story.append(Paragraph("Thumbnail & Visual Style", styles["h3"]))
    story.append(Paragraph(
        "Dhruv's signature visual style for thumbnails and social graphics:",
        styles["body"]
    ))
    thumb_rules = [
        "Dark background (navy/black) with purple/teal neon accents",
        "Dhruv in a black t-shirt with glasses \u2014 always consistent",
        "MacBook Pro visible in frame (tech credibility)",
        "Cinematic, high-production quality lighting",
        "Bold text overlay with the core insight",
        "Hand-drawn whiteboard style for educational infographics (use handdrawn-diagram skill)",
    ]
    for r in thumb_rules:
        story.append(Paragraph(f"\u2022 {r}", styles["bullet"]))

    story.append(PageBreak())

    # ── SECTION 7: PRODUCTS ──────────────────────────────────────────

    story.append(Paragraph("7. Products & Portfolio", styles["h1"]))
    story.append(hr())

    story.append(Paragraph("Live Products", styles["h2"]))

    products = [
        ("QuotaHit", "quotahit.com", "Autonomous AI Sales Department",
         "7 AI agents (Scout, Researcher, Qualifier, Outreach, Closer, Demo, Ops). "
         "Full lead-to-close pipeline. Next.js + Supabase + Inngest."),
        ("IndianWhisper", "indianwhisper.com", "Voice-to-Text Mac App",
         "Community Edition. Free alternative to Wispr ($8/mo). WhisperKit-powered. "
         "Mac native app + Next.js website."),
        ("FinAI", "finai.aiwithdhruv.com", "Financial Document Intelligence",
         "RAG chat, credit memo generation, PDF pipeline with pgvector. "
         "Next.js + FastAPI + OpenRouter."),
        ("FitTrack AI", "fitness.aiwithdhruv.com", "AI Fitness Tracker",
         "Camera-based rep counting, food photo analysis, workout tracking. "
         "MediaPipe + Gemini."),
        ("LaptopFinder AI", "laptopfinder.aiwithdhruv.com", "AI Laptop Recommendations",
         "pgvector RAG for personalized laptop matching."),
        ("Portfolio", "aiwithdhruv.com", "Personal Portfolio & Services",
         "ScreenSage integrated. Next.js 16 + Tailwind v4. Premium dark design."),
    ]

    for name, url, desc, detail in products:
        story.append(Paragraph(f"<b>{name}</b> \u2014 {url}", styles["body_bold"]))
        story.append(Paragraph(f"{desc}. {detail}", styles["body"]))

    story.append(Paragraph("Open Source Projects", styles["h2"]))

    oss = [
        ("Ghost Browser", "github.com/aiagentwithdhruv/ghost-browser",
         "AI browser automation. 8 agents, 5 combos, 10 MCP tools. "
         "LinkedIn, Indeed, Twitter, GitHub automation. Anti-detection built in."),
        ("Claude Skills Library", "github.com/aiagentwithdhruv/skills",
         "43 published open-source skills. Install: npx skills add aiagentwithdhruv/skills"),
        ("AI Coding Rules", "github.com/aiagentwithdhruv/ai-coding-rules",
         "15 production rules + 9 doc templates for AI-native full-stack development."),
        ("Multimodal RAG", "github.com/aiagentwithdhruv/multimodal-rag",
         "5-modality ingestion (text, PDF, image, audio, video). "
         "Next.js + FastAPI + Pinecone + Gemini."),
        ("Agentic Workflows", "github.com/aiagentwithdhruv/agentic-workflows",
         "WAT pattern framework for building autonomous AI workflows."),
        ("ScreenSage", "Open Source",
         "Real-time AI screen assistant with Gemini Live + screen share."),
    ]

    for name, url, desc in oss:
        story.append(Paragraph(f"<b>{name}</b> \u2014 {url}", styles["body_bold"]))
        story.append(Paragraph(desc, styles["body"]))

    story.append(Paragraph("Teaching & Education", styles["h2"]))
    story.append(Paragraph(
        "<b>Euron Platform (euron.one)</b> \u2014 2200+ engineers trained across live classes on "
        "LangGraph, RAG, n8n, voice AI, and agentic systems. Currently running the "
        "'Future-Proof AI Automation Bootcamp' (19 weeks, Sat & Sun 8\u201310 PM IST). "
        "Also consulting with Malavika Lakireddy on LLM Basics to AI-Native Business course.",
        styles["body"]
    ))

    story.append(Paragraph("Zero-to-Production Course (8 AI Products)", styles["h3"]))
    course_products = [
        "SupportIQ \u2014 AI Support Copilot",
        "HireSignal \u2014 AI Interviewer (Frontend + Backend BUILT)",
        "DealPulse \u2014 Sales Intelligence",
        "LearnOS \u2014 Learning Platform",
        "MediCore \u2014 Medical AI",
        "VidSafe \u2014 Video Intelligence",
        "FraudLens \u2014 Fraud Detection",
        "KnowBase \u2014 Knowledge Copilot",
    ]
    for p in course_products:
        story.append(Paragraph(f"\u2022 {p}", styles["bullet"]))

    story.append(PageBreak())

    # ── SECTION 8: SERVICES & PRICING ────────────────────────────────

    story.append(Paragraph("8. Service Catalog & Pricing", styles["h1"]))
    story.append(hr())

    story.append(Paragraph("Tier 1: Quick Wins \u2014 $500\u2013$3,000 (3\u20137 days)", styles["h2"]))
    story.append(pricing_table(
        [
            ["n8n Workflow Automation", "$500\u2013$1,500", "1\u20133 custom workflows"],
            ["AI Chatbot (FAQ/Lead Capture)", "$1,500\u2013$3,000", "RAG pipeline + guardrails"],
            ["Email Automation Setup", "$800\u2013$2,500", "Drip sequences + triggers"],
            ["WhatsApp Bot Setup", "$1,000\u2013$2,500", "Business API integration"],
            ["Social Media Autopilot", "$1,500\u2013$3,000", "Content pipeline + scheduling"],
        ],
        ["Service", "Price Range", "Details"]
    ))

    story.append(Paragraph("Tier 2: Standard Projects \u2014 $3,000\u2013$10,000 (1\u20132 weeks)", styles["h2"]))
    story.append(pricing_table(
        [
            ["AI Voice Agent + CRM", "$5,000\u2013$8,000", "Vapi/Twilio + CRM integration"],
            ["Full Lead Gen System", "$3,000\u2013$8,000", "Scrape + score + email outreach"],
            ["n8n Workflow Suite (5\u201310)", "$5,000\u2013$15,000", "End-to-end automation"],
            ["AI Sales Follow-Up Machine", "$5,000\u2013$7,000", "Auto-qualify + sequence"],
        ],
        ["Service", "Price Range", "Details"]
    ))

    story.append(Paragraph("Tier 3: Enterprise \u2014 $10,000\u2013$50,000 (2\u20134 weeks)", styles["h2"]))
    story.append(pricing_table(
        [
            ["Multi-Agent AI System", "$15,000\u2013$50,000", "Custom agent orchestration"],
            ["AI Sales Intelligence Platform", "$20,000\u2013$50,000", "Full pipeline + dashboards"],
            ["Full CRM + Automation Overhaul", "$15,000\u2013$30,000", "Migration + workflows"],
            ["Voice AI Call Center", "$10,000\u2013$25,000", "Multi-agent phone system"],
            ["AI Guardrail Pipeline", "$5,000\u2013$25,000", "6-layer enterprise security"],
        ],
        ["Service", "Price Range", "Details"]
    ))

    story.append(Paragraph("Retainer Services (Monthly Recurring)", styles["h2"]))
    story.append(pricing_table(
        [
            ["n8n Maintenance + Support", "$500\u2013$2,000/mo", "Monitoring + updates"],
            ["Social Media Management", "$2,000\u2013$5,000/mo", "Content + posting + engagement"],
            ["AI Lead Gen Retainer", "$2,000\u2013$8,000/mo", "Ongoing pipeline"],
            ["Full AI Automation Retainer", "$3,000\u2013$10,000/mo", "Dedicated AI engineer"],
        ],
        ["Service", "Price Range", "Details"]
    ))

    story.append(PageBreak())

    # ── SECTION 9: TECH STACK ────────────────────────────────────────

    story.append(Paragraph("9. Technical Stack & Infrastructure", styles["h1"]))
    story.append(hr())

    story.append(Paragraph("Core Technology", styles["h2"]))
    tech_table = Table(
        [
            ["Layer", "Technologies"],
            ["Frontend", "Next.js 16, React 19, Tailwind CSS v4, TypeScript, Framer Motion"],
            ["Backend", "FastAPI, Python 3.12, Node.js"],
            ["Database", "Supabase (PostgreSQL), pgvector, Pinecone, Redis"],
            ["AI/LLM", "Claude (Anthropic), GPT-4o, Gemini, OpenRouter, Euri API"],
            ["AI Frameworks", "LangGraph, LangChain, AI SDK, RAG pipelines"],
            ["Voice AI", "Vapi, Twilio, Plivo, WhisperKit, Gemini Live"],
            ["Automation", "n8n (218 workflows), Inngest, Claude Code Skills"],
            ["Browser", "Playwright, Ghost Browser (custom), Puppeteer"],
            ["Deployment", "Vercel, AWS (ECS Fargate, S3, ALB), Modal, Docker"],
            ["CI/CD", "GitHub Actions, Vercel Preview Deployments"],
            ["MCP Servers", "17 servers (custom + cloud: Gamma, Gmail, Excalidraw)"],
            ["AI Agents", "26 total (12 custom + 14 GSD)"],
            ["Skills", "149 total (42 custom + 107 global)"],
        ],
        colWidths=[35*mm, None]
    )
    tech_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f1f5f9")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), BODY_TEXT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5*mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5*mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 3*mm),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ("LINEBEFORE", (1, 0), (1, -1), 0.3, BORDER_LIGHT),
    ]))
    story.append(tech_table)

    story.append(Paragraph("AI System Architecture", styles["h2"]))
    story.append(Paragraph(
        "The AIwithDhruv workspace runs a 3-layer system: a <b>Skills Layer</b> (149 bundled capabilities "
        "with SKILL.md + scripts), an <b>Orchestration Layer</b> (Claude makes intelligent routing decisions), "
        "and <b>Shared Utilities</b> (common infrastructure). The system follows a self-annealing loop: "
        "when errors occur, fix \u2192 test \u2192 update docs \u2192 system improves. "
        "Probabilistic AI (decision-making) is separated from deterministic code (execution) for reliability.",
        styles["body"]
    ))

    story.append(PageBreak())

    # ── SECTION 10: SALES FRAMEWORK ──────────────────────────────────

    story.append(Paragraph("10. Proposal & Sales Framework", styles["h1"]))
    story.append(hr())

    story.append(Paragraph("Proposal Template", styles["h2"]))
    story.append(Paragraph(
        "Every proposal follows this structure (max 150 words):",
        styles["body"]
    ))
    proposal_steps = [
        "Open with: 'I've built exactly this before' + specific match to their problem",
        "Include 1 specific number or result (e.g., '31% reply rates', '60% cost reduction')",
        "3-step breakdown specific to their problem (not generic)",
        "Timeline + investment range (never hide pricing)",
        "End with a question that forces a reply",
        "Link to portfolio proof: quotahit.com, YouTube demos, GitHub",
    ]
    for s in proposal_steps:
        story.append(Paragraph(f"\u2022 {s}", styles["bullet"]))

    story.append(Paragraph("Proof Points for Proposals", styles["h2"]))
    story.append(info_table([
        ["Revenue Growth", "0 \u2192 10 Cr ARR at B2B SaaS (Onsite)"],
        ["Cost Reduction", "60\u201370% cost reduction through AI automation"],
        ["Email Performance", "31% reply rates on cold outreach"],
        ["Scale", "2200+ engineers trained on Euron"],
        ["Systems", "20+ production systems running live"],
        ["Automation", "218 n8n workflows (54 active)"],
        ["Open Source", "43+ published skills, adopted by community"],
    ]))

    story.append(Paragraph("Objection Handling", styles["h2"]))
    objections = [
        ('"Too expensive"', "ROI framing: saves 20 hrs/week at $50/hr = $4K/mo savings vs $3K one-time investment"),
        ('"We can do it ourselves"', "Speed argument: 5 days vs weeks. Plus production-grade quality from day 1."),
        ('"We use Zapier/Make"', "n8n advantage: 10x power, 1/3 cost, self-hosted, no vendor lock-in."),
        ('"Need to think about it"', "Ask specific concern to address now. Offer a free 15-min architecture call."),
    ]
    for obj, response in objections:
        story.append(Paragraph(f"\u2022 <b>{obj}</b> \u2192 {response}", styles["bullet"]))

    story.append(PageBreak())

    # ── SECTION 11: TRUST SIGNALS ────────────────────────────────────

    story.append(Paragraph("11. Trust Signals & Proof Points", styles["h1"]))
    story.append(hr())

    story.append(Paragraph("Portfolio Statistics (Hero Section)", styles["h2"]))
    stats = [
        ("0\u219210 Cr ARR", "Revenue growth at Onsite B2B SaaS"),
        ("2200+", "Engineers trained on Euron platform"),
        ("20+", "Production AI systems shipped & running"),
        ("43+", "Open-source skills published"),
        ("218", "n8n automation workflows built"),
        ("40+", "GitHub repositories (30 public)"),
    ]
    for stat, desc in stats:
        story.append(Paragraph(f"\u2022 <b>{stat}</b> \u2014 {desc}", styles["bullet"]))

    story.append(Paragraph("Video Proof Points", styles["h2"]))
    story.append(info_table([
        ["Voice AI + CRM", "youtube.com/watch?v=RJON7N7yQ3Y"],
        ["3 AI Products Live", "youtu.be/I1UXNYwvMBc"],
        ["Live AI Class (1000+)", "youtube.com/live/9JlSu6ui39U"],
        ["E2E AI Product", "youtu.be/N1btQ3VaKQQ"],
        ["Real-time Voice Agents", "youtu.be/3hzoRwTRuTU"],
        ["Agentic AI Demo", "youtu.be/KGGFc9cee0I"],
    ], col1_width=45*mm))

    story.append(Paragraph("Live URLs", styles["h2"]))
    live_urls = [
        "aiwithdhruv.com \u2014 Portfolio",
        "quotahit.com \u2014 AI Sales Platform",
        "indianwhisper.com \u2014 Voice-to-Text App",
        "finai.aiwithdhruv.com \u2014 Financial Intelligence",
        "fitness.aiwithdhruv.com \u2014 AI Fitness Tracker",
        "laptopfinder.aiwithdhruv.com \u2014 Laptop Recommendations",
    ]
    for u in live_urls:
        story.append(Paragraph(f"\u2022 {u}", styles["bullet"]))

    story.append(PageBreak())

    # ── SECTION 12: ABOUT DHRUV ──────────────────────────────────────

    story.append(Paragraph("12. About Dhruv Tomar", styles["h1"]))
    story.append(hr())

    if DHRUV_SQUARE.exists():
        photo = Image(str(DHRUV_SQUARE), width=35*mm, height=35*mm)
        photo.hAlign = "LEFT"
        story.append(photo)
        story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        "Dhruv Tomar is an AI Architect &amp; Product Lead based in India, "
        "serving clients worldwide. He specializes in building production-grade AI systems "
        "that run businesses autonomously \u2014 from lead generation and sales automation to "
        "voice AI agents and browser automation.",
        styles["body"]
    ))
    story.append(Paragraph(
        "With a track record of taking a B2B SaaS from 0 to 10 Cr ARR, training 2200+ engineers, "
        "and shipping 20+ production systems, Dhruv brings a rare combination of deep technical "
        "expertise and business acumen. He operates as a 3-in-1: consultant, engineer, and product owner.",
        styles["body"]
    ))

    story.append(Paragraph("Current Role", styles["h3"]))
    story.append(Paragraph(
        "<b>AI Architect &amp; Product Lead</b> at MSBC Group (London HQ, "
        "22 years, 200+ engineers, $19.7M revenue). Working across FinTech (RemoraTech), "
        "Construction Safety AI (Saifety.ai), and Manufacturing ERP (DWERP) domains.",
        styles["body"]
    ))

    story.append(Paragraph("Partnerships", styles["h3"]))
    partners = [
        ("Growx Agency", "AI Consultant. End-to-end digital agency (India + International). Dhruv provides AI/tech consulting, Shikhar handles marketing/ads."),
        ("MensaAI", "AI Consultant for Malavika Lakireddy\u2019s AI Native Agency. Focus on international clients, $5\u201310K deals."),
        ("Euron", "AI Instructor &amp; Consultant. Live classes, bootcamps, 2200+ learners. Teaching for free, building in public."),
    ]
    for name, desc in partners:
        story.append(Paragraph(f"\u2022 <b>{name}:</b> {desc}", styles["bullet"]))

    story.append(Paragraph("Personal Style", styles["h3"]))
    story.append(Paragraph(
        "Always in a black t-shirt with glasses. Cinematic, high-production visual presence. "
        "Direct communicator who leads with results, not promises. Believes in shipping over talking, "
        "building over advising, and outcomes over features.",
        styles["body"]
    ))

    story.append(Spacer(1, 10*mm))
    story.append(hr())
    story.append(Paragraph(
        "AIwithDhruv Brand Bible v1.0 | March 2026 | Confidential",
        styles["footer"]
    ))
    story.append(Paragraph(
        "aiwithdhruv@gmail.com | aiwithdhruv.com | linkedin.com/in/aiwithdhruv",
        styles["footer"]
    ))

    # ── BUILD ────────────────────────────────────────────────────────
    doc.build(story)
    print(f"PDF generated: {PDF_PATH}")
    return PDF_PATH


if __name__ == "__main__":
    build_pdf()
