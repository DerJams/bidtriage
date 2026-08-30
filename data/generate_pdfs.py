"""Deterministically render the synthetic RFP PDFs.

All content is fictional. Run:  python -m data.generate_pdfs

reportlab is put in invariant mode so repeated runs produce byte-identical
PDFs (no embedded timestamps), which keeps REPRODUCE.md honest.

Case 12 is the deliberately hard case. It is NOT a true scan -- rendering a
real scan would require an OCR dependency (tesseract) that would break
clean-environment reproducibility. Instead its layout is structurally
degraded to reproduce the same failure modes: a misaligned multi-column
quantity table where alternates read as base scope, a page footer that keeps
repeating the superseded bid date, and an addendum buried on page 4.
"""
from __future__ import annotations

import pathlib

import reportlab.rl_config as rl_config

rl_config.invariant = 1  # must precede canvas/doc construction

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "synthetic" / "pdfs"

_ss = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=_ss["BodyText"], fontName="Helvetica",
                      fontSize=9.5, leading=13, spaceAfter=6)
H1 = ParagraphStyle("h1", parent=_ss["Heading1"], fontName="Helvetica-Bold",
                    fontSize=14, leading=17, alignment=TA_CENTER, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=_ss["Heading2"], fontName="Helvetica-Bold",
                    fontSize=10.5, leading=13, spaceBefore=10, spaceAfter=4)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8, leading=10)
MONO = ParagraphStyle("mono", parent=BODY, fontName="Courier", fontSize=8.2,
                      leading=11)

GRID = TableStyle([
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
])

PLAIN = TableStyle([
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
])


def _doc(path, footer_text=None):
    doc = BaseDocTemplate(str(path), pagesize=LETTER,
                          leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                          topMargin=0.8 * inch, bottomMargin=0.85 * inch,
                          title=path.stem, author="Synthetic RFP generator",
                          subject="Fictional bid document")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")

    def on_page(canvas, _d):
        if footer_text:
            canvas.saveState()
            canvas.setFont("Helvetica", 7.5)
            canvas.drawString(doc.leftMargin, 0.55 * inch, footer_text)
            canvas.drawRightString(LETTER[0] - doc.rightMargin, 0.55 * inch,
                                   "Page %d" % canvas.getPageNumber())
            canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="std", frames=[frame], onPage=on_page)])
    return doc


def kv(rows, widths=(1.9 * inch, 4.4 * inch)):
    t = Table([[k, v] for k, v in rows], colWidths=list(widths))
    t.setStyle(PLAIN)
    return t


def grid(rows, widths):
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(GRID)
    return t


# --------------------------------------------------------------------------
# Standard RFP cases (06-09). All owners, projects and people are fictional.
# --------------------------------------------------------------------------

STANDARD = {
    "case_06": {
        "owner": "Larkspur Civic Development Authority",
        "project": "Larkspur Civic Center Annex Mechanical Package",
        "solicitation": "LCDA-MEP-2026-08",
        "location": "Denver, CO",
        "trades": "HVAC and controls",
        "scope": (
            "The Work comprises the complete mechanical package for the Civic Center "
            "Annex, including four (4) custom air handling units, associated hydronic "
            "heating and chilled water piping within the mechanical penthouse, VAV "
            "terminal units throughout the occupied floors, and a new direct digital "
            "control system tied to the Authority existing campus front end. "
            "Plumbing scope is bid under a separate package and is excluded here."
        ),
        "qty": [
            ["Item", "Description", "Unit", "Qty"],
            ["23 73 13", "Custom indoor air handling unit, 12,000 CFM", "EA", "4"],
            ["23 36 00", "VAV terminal unit with hot water reheat coil", "EA", "86"],
            ["23 21 13", "Hydronic piping, welded carbon steel, 4 in.", "LF", "1,240"],
            ["23 09 23", "DDC controller, field-mounted", "EA", "94"],
            ["23 05 93", "Testing, adjusting and balancing, complete system", "LS", "1"],
        ],
        "estimate": "$1,200,000",
        "bid_due": "September 29, 2026 at 2:00 PM MT",
        "walkthrough": "September 15, 2026 at 8:30 AM",
        "constr_start": "November 1, 2026",
        "constr_end": "February 28, 2027",
        "bonds": [
            ["Requirement", "Amount"],
            ["Bid bond", "5% of total base bid"],
            ["Performance bond", "100% of contract sum"],
            ["Payment bond", "100% of contract sum"],
            ["Commercial general liability", "$2,000,000 per occurrence"],
        ],
        "contact": "Ingeborg Talamantez-Fyfe, Contracting Officer",
    },
    "case_07": {
        "owner": "Cache La Poudre Community College District",
        "project": "Science Building HVAC Modernization",
        "solicitation": "CLPCC-2026-ITB-041",
        "location": "Fort Collins, CO",
        "trades": "HVAC, sheet metal, and controls",
        "scope": (
            "Replacement of the Science Building original constant-volume air "
            "handling equipment with variable-air-volume systems, including new "
            "galvanized supply and return ductwork throughout three floors, fume hood "
            "exhaust manifolding, energy recovery ventilator installation, and a full "
            "building automation system replacement. Laboratory process piping is by "
            "others and is excluded from this package."
        ),
        "qty": [
            ["Item", "Description", "Unit", "Qty"],
            ["23 73 23", "Variable air volume air handling unit, 22,000 CFM", "EA", "3"],
            ["23 31 13", "Galvanized rectangular ductwork, fabricated and installed", "LB", "48,500"],
            ["23 35 16", "Fume hood exhaust manifold, stainless", "EA", "12"],
            ["23 72 00", "Energy recovery ventilator, enthalpy wheel", "EA", "2"],
            ["23 09 00", "Building automation system, complete replacement", "LS", "1"],
        ],
        "estimate": "$1,400,000",
        "bid_due": "October 20, 2026 at 3:00 PM MT",
        "walkthrough": "October 2, 2026 at 1:00 PM",
        "constr_start": "April 12, 2027",
        "constr_end": "September 24, 2027",
        "bonds": [
            ["Requirement", "Amount"],
            ["Bid bond", "5% of total base bid"],
            ["Performance bond", "100% of contract sum"],
            ["Payment bond", "100% of contract sum"],
            ["Commercial general liability", "$3,000,000 per occurrence"],
        ],
        "contact": "Oluwaseun Brannigan-Estevez, Director of Capital Projects",
    },
    "case_08": {
        "owner": "Pikes Hollow Athletic Club",
        "project": "Natatorium Pool Mechanical Replacement",
        "solicitation": "PHAC-2026-POOL-01",
        "location": "Colorado Springs, CO",
        "trades": "plumbing and process piping",
        "scope": (
            "Complete replacement of the natatorium pool mechanical systems, "
            "including circulation pumps, regenerative media filters, chemical feed "
            "and controller equipment, surge tank piping, and all associated CPVC and "
            "copper distribution piping. Pool dehumidification equipment is existing "
            "to remain and is not part of this scope."
        ),
        "qty": [
            ["Item", "Description", "Unit", "Qty"],
            ["22 11 23", "Circulation pump, 40 HP, end suction", "EA", "3"],
            ["22 11 23", "Regenerative media filter vessel", "EA", "2"],
            ["22 67 00", "Chemical feed system, complete with controller", "LS", "1"],
            ["22 11 16", "CPVC distribution piping, 6 in.", "LF", "820"],
            ["22 11 16", "Type L copper piping, 2 in. and smaller", "LF", "460"],
        ],
        "estimate": "$600,000",
        "bid_due": "October 14, 2026 at 5:00 PM MT",
        "walkthrough": None,
        "constr_start": "February 8, 2027",
        "constr_end": "May 29, 2027",
        "bonds": None,
        "contact": "Marisol Ferrante-Okonkwo, Club General Manager",
    },
    "case_09": {
        "owner": "Vantage Point Logistics",
        "project": "Distribution Center Ventilation Upgrade",
        "solicitation": "VPL-DC4-MECH-2026",
        "location": "Longmont, CO",
        "trades": "sheet metal and HVAC",
        "scope": (
            "Fabrication and installation of a new warehouse ventilation and "
            "destratification system across 640,000 square feet of distribution "
            "space, including spiral supply ductwork, gravity relief ventilators, "
            "make-up air units serving the dock doors, and unit heaters throughout. "
            "Controls integration is by the Owner existing vendor and is excluded "
            "from this package."
        ),
        "qty": [
            ["Item", "Description", "Unit", "Qty"],
            ["23 31 16", "Spiral round ductwork, galvanized, 24 in. dia.", "LF", "14,200"],
            ["23 34 23", "Destratification fan, high volume low speed", "EA", "38"],
            ["23 74 13", "Make-up air unit, direct gas fired, 20,000 CFM", "EA", "6"],
            ["23 34 16", "Gravity relief ventilator, curb mounted", "EA", "44"],
            ["23 55 33", "Gas fired unit heater, 250 MBH", "EA", "52"],
        ],
        "estimate": "$2,200,000",
        "bid_due": "November 10, 2026 at 4:00 PM MT",
        "walkthrough": "October 22, 2026 at 9:00 AM",
        "constr_start": "May 3, 2027",
        "constr_end": "October 15, 2027",
        "bonds": [
            ["Requirement", "Amount"],
            ["Bid bond", "5% of total base bid"],
            ["Performance bond", "100% of contract sum"],
            ["Payment bond", "100% of contract sum"],
            ["Commercial general liability", "$4,000,000 per occurrence"],
        ],
        "contact": "Bartholomew Nkemdirim-Salazar, Facilities Program Manager",
    },
}


def render_standard(case_id, d):
    story = [
        Paragraph("INVITATION TO BID", H1),
        Paragraph(d["owner"].upper(), H1),
        Spacer(1, 10),
        kv([
            ("Solicitation No.", d["solicitation"]),
            ("Project", d["project"]),
            ("Owner", d["owner"]),
            ("Project Location", d["location"]),
            ("Trades Required", d["trades"]),
        ]),
        Paragraph("SECTION 1 - SCOPE OF WORK", H2),
        Paragraph(d["scope"], BODY),
        Paragraph("SECTION 2 - SCHEDULE OF QUANTITIES", H2),
        grid(d["qty"], [0.85 * inch, 3.3 * inch, 0.55 * inch, 0.8 * inch]),
        Spacer(1, 4),
        Paragraph(
            "Quantities shown are for bidder convenience. Bidders are responsible "
            "for verifying all quantities from the contract drawings.", SMALL),
        Paragraph("SECTION 3 - PROJECT SCHEDULE AND BUDGET", H2),
    ]

    sched = [("Engineer's estimate", d["estimate"]), ("Bid due", d["bid_due"])]
    if d["walkthrough"]:
        sched.append(("Pre-bid walk-through", d["walkthrough"]))
    sched += [("Construction start", d["constr_start"]),
              ("Substantial completion", d["constr_end"])]
    story.append(kv(sched))

    if not d["walkthrough"]:
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "A pre-bid walk-through will not be held for this project. Bidders may "
            "arrange individual site access by appointment with the Club.", BODY))

    story.append(Paragraph("SECTION 4 - BONDING AND INSURANCE", H2))
    if d["bonds"]:
        story.append(grid(d["bonds"], [3.6 * inch, 2.7 * inch]))
    else:
        story.append(Paragraph(
            "This is a privately funded project. No bid bond, performance bond, or "
            "payment bond is required for this solicitation. Bidders shall provide a "
            "current certificate of insurance upon award.", BODY))

    story.append(Paragraph("SECTION 5 - CONTACT", H2))
    story.append(Paragraph("Direct all questions in writing to " + d["contact"] + ".", BODY))

    path = OUT / (case_id + ".pdf")
    footer = d["solicitation"] + "  |  " + d["project"]
    _doc(path, footer_text=footer).build(story)
    print("wrote " + str(path.relative_to(ROOT)))


# --------------------------------------------------------------------------
# Case 12 -- the deliberately hard case.
# --------------------------------------------------------------------------

C12_FOOTER = ("SARMC-CP-2026-03  |  CENTRAL PLANT UPGRADE  |  "
              "BID DATE: OCTOBER 16, 2026  |  UNCONTROLLED IF PRINTED")


def render_case_12():
    """Silver Aspen Regional Medical Campus -- Central Plant Upgrade.

    Traps, all reproducing real intake failures:
      1. Every page footer repeats the SUPERSEDED bid date (Oct 16). The
         controlling date is on page 4, Addendum No. 2 (Nov 6).
      2. The quantity table has a BASE BID column and an ALT 1 column. Fire
         protection standpipe work appears ONLY under ALT 1 with a base
         quantity of zero. Reading it as base scope pulls a trade Summit Peak
         does not self-perform, which flips the triage decision to no-bid.
      3. The engineer's estimate is a range, not a point value.
    """
    story = []

    # --- Page 1: cover, still showing the original date -------------------
    story += [
        Paragraph("SILVER ASPEN REGIONAL MEDICAL CAMPUS", H1),
        Paragraph("CENTRAL PLANT UPGRADE", H1),
        Paragraph("PROJECT MANUAL - VOLUME 1 OF 3", H1),
        Spacer(1, 16),
        kv([
            ("SOLICITATION", "SARMC-CP-2026-03"),
            ("OWNER", "Silver Aspen Regional Medical Campus"),
            ("SITE", "Castle Rock, CO"),
            ("ISSUED", "August 14, 2026"),
            ("BID DATE", "October 16, 2026 at 2:00 PM MT"),
            ("PRE-BID WALK", "September 30, 2026 at 7:30 AM"),
        ]),
        Spacer(1, 14),
        Paragraph(
            "NOTICE TO BIDDERS: This project manual is issued subject to addenda. "
            "Bidders are responsible for confirming they have received and "
            "incorporated all addenda prior to submission. Dates appearing on this "
            "cover sheet and in page footers are as-issued and may be superseded by "
            "addendum. Refer to Volume 1, Part 4 for all issued addenda.", BODY),
        Spacer(1, 10),
        Paragraph(
            "The Owner reserves the right to reject any and all bids and to waive "
            "informalities in the bidding.", BODY),
        PageBreak(),
    ]

    # --- Page 2: scope narrative -----------------------------------------
    story += [
        Paragraph("PART 1 - SUMMARY OF WORK", H2),
        Paragraph(
            "The Project consists of the replacement and expansion of the central "
            "utility plant serving the Silver Aspen Regional Medical Campus. Base "
            "Bid work includes demolition of two existing steam-to-hot-water "
            "converters, installation of three new condensing hot water boilers, "
            "replacement of the primary chilled water pumping assembly, new "
            "underground and above-grade hydronic distribution piping between the "
            "plant and Buildings A and C, and complete replacement of the plant "
            "control system including graphics and integration to the campus "
            "building automation network.", BODY),
        Paragraph(
            "Base Bid trades are mechanical (HVAC), process and hydronic piping, and "
            "automatic temperature controls. The Contractor shall self-perform not "
            "less than thirty percent (30%) of the Base Bid work.", BODY),
        Paragraph(
            "ALTERNATE NO. 1 is a separately priced add alternate covering "
            "modifications to the standpipe and fire suppression risers in the plant "
            "penthouse. Alternate No. 1 is NOT part of the Base Bid and shall be "
            "priced separately on the bid form. The Owner may elect not to award "
            "Alternate No. 1. Bidders who do not hold a fire protection license may "
            "bid the Base Bid and decline Alternate No. 1 without prejudice.", BODY),
        Paragraph("PART 2 - COMMERCIAL TERMS", H2),
        kv([
            ("ENGINEER ESTIMATE", "$1,800,000 to $2,100,000"),
            ("CONSTRUCTION START", "March 15, 2027"),
            ("SUBSTANTIAL COMPLETION", "November 30, 2027"),
            ("BID BOND", "5% of base bid"),
            ("PERFORMANCE BOND", "100% of contract sum"),
            ("PAYMENT BOND", "100% of contract sum"),
            ("GENERAL LIABILITY", "$5,000,000 per occurrence"),
        ]),
        PageBreak(),
    ]

    # --- Page 3: the misaligned quantity table ---------------------------
    # Rendered as preformatted monospace with deliberately ragged column
    # alignment, the way a poorly produced bid tab actually reads.
    qty_lines = [
        "PART 3 - SCHEDULE OF QUANTITIES",
        "",
        "                                              BASE BID      ALT 1",
        "SPEC     DESCRIPTION                    UNIT     QTY         QTY",
        "-------- ------------------------------ ---- ---------- ----------",
        "23 52 16 Condensing hot water boiler,    EA        3           0",
        "         4,000 MBH",
        "23 21 23 Primary CHW pump, 60 HP,        EA        4           0",
        "         base mounted",
        "23 21 13 Hydronic piping, welded,        LF     2,180           0",
        "         8 in. and larger",
        "23 21 13 Hydronic piping, welded,        LF     3,640           0",
        "         6 in. and smaller",
        "23 09 23 DDC plant controller and        LS        1           0",
        "         graphics package",
        "23 05 93 TAB, complete plant             LS        1           0",
        "21 12 00 Standpipe riser modification,   EA        0           6",
        "         penthouse                                  <-- ALT 1 ONLY",
        "21 13 16 Wet pipe sprinkler head         EA        0          altered",
        "         relocation, plant penthouse                   under ALT 1",
        "-------- ------------------------------ ---- ---------- ----------",
        "",
        "NOTE: The ALT 1 QTY column applies to Alternate No. 1 only. Items showing",
        "a BASE BID QTY of 0 are excluded from the Base Bid scope. Spec sections",
        "21 12 00 and 21 13 16 are fire protection and are carried under Alternate",
        "No. 1 exclusively.",
    ]
    for line in qty_lines:
        text = line.replace(" ", "&nbsp;") if line.startswith(" ") or "  " in line else line
        style = H2 if line.startswith("PART 3") else MONO
        story.append(Paragraph(text if line else "&nbsp;", style))
    story.append(PageBreak())

    # --- Page 4: the addendum that actually controls ---------------------
    story += [
        Paragraph("PART 4 - ADDENDA ISSUED", H2),
        Spacer(1, 6),
        Paragraph("ADDENDUM NO. 1 - Issued September 4, 2026", H2),
        Paragraph(
            "Item 1.1: Specification Section 23 52 16, boiler manufacturer list is "
            "amended to add one additional approved manufacturer. Item 1.2: Drawing "
            "M-201, revise pipe routing at column line D-4 as shown on attached "
            "sketch SK-M-01. No change to the bid date results from this addendum.",
            BODY),
        Spacer(1, 8),
        Paragraph("ADDENDUM NO. 2 - Issued September 25, 2026", H2),
        Paragraph(
            "Item 2.1: THE BID DATE IS EXTENDED. Bids are now due November 6, 2026 "
            "at 2:00 PM MT. The bid date of October 16, 2026 shown on the cover "
            "sheet and in the page footers of this project manual is superseded and "
            "shall not be relied upon.", BODY),
        Paragraph(
            "Item 2.2: The pre-bid walk-through held September 30, 2026 is not "
            "rescheduled. Firms that attended the September 30 walk-through remain "
            "eligible to bid. No additional walk-through will be held.", BODY),
        Paragraph(
            "Item 2.3: Alternate No. 1 remains a separately priced add alternate. "
            "Several bidders inquired whether the standpipe work is included in the "
            "Base Bid. It is not.", BODY),
        Spacer(1, 10),
        Paragraph(
            "END OF ADDENDA. Bidders shall acknowledge receipt of Addenda 1 and 2 on "
            "the bid form. Failure to acknowledge may render the bid non-responsive.",
            BODY),
    ]

    path = OUT / "case_12.pdf"
    _doc(path, footer_text=C12_FOOTER).build(story)
    print("wrote " + str(path.relative_to(ROOT)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for case_id, d in sorted(STANDARD.items()):
        render_standard(case_id, d)
    render_case_12()


if __name__ == "__main__":
    main()
