"""Corpus v2 cases 06 to 18.

06 to 12 are revised from v1. 10 and 11 are rewritten per the research: a
platform invitation is structured and field-rich, and the ambiguity lives in
the attachment, so they are now multi-part cases.

13 onward are new shapes, not new values in existing templates.
"""
from data.v2.common import *  # noqa: F401,F403

CASES = []


def add(**kw):
    CASES.append(kw)


H = "__heading__"

# --------------------------------------------------------------------- 06
add(
    id="case_06", format="pdf_rfp",
    parts=[pdf_part(V2P + "/case_06.pdf", [
        (H, "INVITATION TO BID"),
        ("client_name", "Owner: Larkspur Civic Development Authority"),
        ("project_title", "Project: Larkspur Civic Center Annex Mechanical Package"),
        ("location", "Project Location: Denver, CO"),
        ("trade_scope", "Trades Required: HVAC and controls"),
        (H, "SECTION 1 - SCOPE OF WORK"),
        ("prose", "The Work comprises four custom air handling units, hydronic heating and chilled water piping within the mechanical penthouse, VAV terminal units throughout the occupied floors, and a new direct digital control system. Plumbing is bid under a separate package."),
        (H, "SECTION 2 - SCHEDULE AND BUDGET"),
        ("estimated_project_value", "Engineer's estimate: $1,200,000"),
        ("bid_due_date", "Bid due: September 29, 2026 at 2:00 PM MT"),
        ("walkthrough_date", "Pre-bid walk-through: September 15, 2026 at 8:30 AM"),
        ("prose", "Construction start: November 1, 2026. Substantial completion: February 28, 2027."),
        (H, "SECTION 3 - BONDING AND INSURANCE"),
        ("bond_insurance", MUNI_BOND_TEXT),
    ])],
    fields={
        "client_name": F("Larkspur Civic Development Authority", low("Larkspur Civic Development Authority")),
        "project_title": F("Larkspur Civic Center Annex Mechanical Package", low("Larkspur Civic Center Annex Mechanical Package")),
        "trade_scope": F(["hvac", "controls"], ["controls", "hvac"]),
        "location": F("Denver, CO", "denver, co"),
        "bid_due_date": F("September 29, 2026", "2026-09-29", {"time_local": "14:00"}),
        "estimated_project_value": F("$1,200,000", M(1200000)),
        "bond_insurance": F("10% bid bond; 100% performance and payment; $2M/$4M GL", MUNI_BOND),
        "walkthrough_date": F("September 15, 2026", "2026-09-15"),
    },
    construction_window=["2026-11-01", "2027-02-28"],
)

# --------------------------------------------------------------------- 07
add(
    id="case_07", format="pdf_rfp",
    parts=[pdf_part(V2P + "/case_07.pdf", [
        (H, "INVITATION TO BID"),
        ("client_name", "Owner: Cache La Poudre Community College District"),
        ("project_title", "Project: Science Building HVAC Modernization"),
        ("location", "Project Location: Fort Collins, CO"),
        ("trade_scope", "Trades Required: HVAC, sheet metal, and controls"),
        (H, "SECTION 1 - SCOPE OF WORK"),
        ("prose", "Replacement of constant-volume air handling equipment with variable-air-volume systems, new galvanized supply and return ductwork across three floors, fume hood exhaust manifolding, energy recovery ventilators, and a full building automation replacement. Laboratory process piping is by others."),
        (H, "SECTION 2 - SCHEDULE AND BUDGET"),
        ("estimated_project_value", "Engineer's estimate: $1,400,000"),
        ("bid_due_date", "Bid due: October 20, 2026 at 3:00 PM MT"),
        ("walkthrough_date", "Pre-bid walk-through: October 2, 2026 at 1:00 PM"),
        ("prose", "Construction start: April 12, 2027. Substantial completion: September 24, 2027."),
        (H, "SECTION 3 - BONDING AND INSURANCE"),
        ("bond_insurance", MUNI_BOND_TEXT),
    ])],
    fields={
        "client_name": F("Cache La Poudre Community College District", low("Cache La Poudre Community College District")),
        "project_title": F("Science Building HVAC Modernization", low("Science Building HVAC Modernization")),
        "trade_scope": F(["hvac", "sheet_metal", "controls"], ["controls", "hvac", "sheet_metal"]),
        "location": F("Fort Collins, CO", "fort collins, co"),
        "bid_due_date": F("October 20, 2026", "2026-10-20", {"time_local": "15:00"}),
        "estimated_project_value": F("$1,400,000", M(1400000)),
        "bond_insurance": F("10% bid bond; 100% performance and payment; $2M/$4M GL", MUNI_BOND),
        "walkthrough_date": F("October 2, 2026", "2026-10-02"),
    },
    construction_window=["2027-04-12", "2027-09-24"],
)

# --------------------------------------------------------------------- 08
add(
    id="case_08", format="pdf_rfp",
    parts=[pdf_part(V2P + "/case_08.pdf", [
        (H, "INVITATION TO BID"),
        ("client_name", "Owner: Pikes Hollow Athletic Club"),
        ("project_title", "Project: Natatorium Pool Mechanical Replacement"),
        ("location", "Project Location: Colorado Springs, CO"),
        ("trade_scope", "Trades Required: plumbing and process piping"),
        (H, "SECTION 1 - SCOPE OF WORK"),
        ("prose", "Complete replacement of the natatorium pool mechanical systems: circulation pumps, regenerative media filters, chemical feed and controller equipment, surge tank piping, and associated CPVC and copper distribution. Pool dehumidification equipment is existing to remain."),
        (H, "SECTION 2 - SCHEDULE AND BUDGET"),
        ("estimated_project_value", "Engineer's estimate: $600,000"),
        ("bid_due_date", "Bid due: October 14, 2026 at 5:00 PM MT"),
        ("prose", "A pre-bid walk-through will not be held for this project. Bidders may arrange individual site access by appointment with the Club."),
        ("prose", "Construction start: February 8, 2027. Substantial completion: May 29, 2027."),
        (H, "SECTION 3 - BONDING AND INSURANCE"),
        ("bond_insurance", "This is a privately funded project. No bid bond, performance bond, or payment bond is required for this solicitation. Bidders shall provide a current certificate of insurance upon award."),
    ])],
    fields={
        "client_name": F("Pikes Hollow Athletic Club", low("Pikes Hollow Athletic Club")),
        "project_title": F("Natatorium Pool Mechanical Replacement", low("Natatorium Pool Mechanical Replacement")),
        "trade_scope": F(["plumbing", "piping"], ["piping", "plumbing"]),
        "location": F("Colorado Springs, CO", "colorado springs, co"),
        "bid_due_date": F("October 14, 2026", "2026-10-14", {"time_local": "17:00"}),
        "estimated_project_value": F("$600,000", M(600000)),
        "bond_insurance": F("No bonding required", bond(required=False)),
        "walkthrough_date": None,
    },
    absent_notes={"walkthrough_date": "Source states a walk-through will not be held."},
    construction_window=["2027-02-08", "2027-05-29"],
)

# --------------------------------------------------------------------- 09
add(
    id="case_09", format="pdf_rfp",
    parts=[pdf_part(V2P + "/case_09.pdf", [
        (H, "INVITATION TO BID"),
        ("client_name", "Owner: Vantage Point Logistics"),
        ("project_title", "Project: Distribution Center Ventilation Upgrade"),
        ("location", "Project Location: Longmont, CO"),
        ("trade_scope", "Trades Required: sheet metal and HVAC"),
        (H, "SECTION 1 - SCOPE OF WORK"),
        ("prose", "Fabrication and installation of a warehouse ventilation and destratification system across 640,000 square feet: spiral supply ductwork, gravity relief ventilators, dock make-up air units, and unit heaters. Controls integration is by the Owner's existing vendor and is excluded."),
        (H, "SECTION 2 - SCHEDULE AND BUDGET"),
        ("estimated_project_value", "Engineer's estimate: $2,200,000"),
        ("bid_due_date", "Bid due: November 10, 2026 at 4:00 PM MT"),
        ("walkthrough_date", "Pre-bid walk-through: October 22, 2026 at 9:00 AM"),
        ("prose", "Construction start: May 3, 2027. Substantial completion: October 15, 2027."),
        (H, "SECTION 3 - BONDING AND INSURANCE"),
        ("bond_insurance", STD_BOND_TEXT),
    ])],
    fields={
        "client_name": F("Vantage Point Logistics", low("Vantage Point Logistics")),
        "project_title": F("Distribution Center Ventilation Upgrade", low("Distribution Center Ventilation Upgrade")),
        "trade_scope": F(["sheet_metal", "hvac"], ["hvac", "sheet_metal"]),
        "location": F("Longmont, CO", "longmont, co"),
        "bid_due_date": F("November 10, 2026", "2026-11-10", {"time_local": "16:00"}),
        "estimated_project_value": F("$2,200,000", M(2200000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("October 22, 2026", "2026-10-22"),
    },
    construction_window=["2027-05-03", "2027-10-15"],
)

# --------------------------------------------------------------------- 10
# Rewritten: structured platform invitation, ambiguity pushed to the attachment.
add(
    id="case_10", format="platform_invitation_with_attachment",
    parts=[
        email_part(
            V2E + "/case_10.eml",
            "Front Range Transit Authority via BidBoard <team@bidboardconnect.example>", TO,
            "Bid Invite: Maintenance Facility Bay 4 Mechanical Upgrades Project",
            "Thu, 27 Aug 2026 04:02:11 -0600",
            [("prose", "You have been invited to bid."),
             ("client_name", "Client: Front Range Regional Transit Authority"),
             ("project_title", "Project: Maintenance Facility Bay 4 Mechanical Upgrades"),
             ("prose", "Bid package: Mechanical, Division 22 and 23"),
             ("location", "Location: Denver, CO"),
             ("bid_due_date", "Bids due: October 6, 2026 at 3:00 PM MT"),
             ("walkthrough_date", "Job walk: September 24, 2026 at 7:00 AM"),
             ("prose", "Project lead: Delphine Marchetti-Oyibo, Preconstruction Manager. Phone 555-0142."),
             ("prose", "View this RFP: https://bidboardconnect.example/rfp/FRRTA-26-0431"),
             ("prose", "Attached: scope narrative and commercial terms.")],
            role="platform invitation"),
        pdf_part(V2P + "/case_10_scope.pdf", [
            (H, "SCOPE NARRATIVE AND COMMERCIAL TERMS"),
            ("prose", "Bay 4 serves heavy vehicle maintenance. The work replaces the bay heating and ventilation equipment and the compressed air distribution serving the lifts."),
            ("trade_scope", "Base bid trades: HVAC, plumbing, and sheet metal."),
            ("estimated_project_value", "Owner's construction budget for this package is $1,050,000."),
            ("prose", "Construction start: April 5, 2027. Substantial completion: August 28, 2027."),
            ("bond_insurance", MUNI_BOND_TEXT),
        ], role="scope attachment"),
    ],
    fields={
        "client_name": F("Front Range Regional Transit Authority", low("Front Range Regional Transit Authority")),
        "project_title": F("Maintenance Facility Bay 4 Mechanical Upgrades", low("Maintenance Facility Bay 4 Mechanical Upgrades")),
        "trade_scope": F(["hvac", "plumbing", "sheet_metal"], ["hvac", "plumbing", "sheet_metal"]),
        "location": F("Denver, CO", "denver, co"),
        "bid_due_date": F("October 6, 2026", "2026-10-06", {"time_local": "15:00"}),
        "estimated_project_value": F("$1,050,000", M(1050000)),
        "bond_insurance": F("10% bid bond; 100% performance and payment; $2M/$4M GL", MUNI_BOND),
        "walkthrough_date": F("September 24, 2026", "2026-09-24"),
    },
    construction_window=["2027-04-05", "2027-08-28"],
)

# --------------------------------------------------------------------- 11
add(
    id="case_11", format="platform_invitation_with_attachment",
    parts=[
        email_part(
            V2E + "/case_11.eml",
            "Idaho Springs Utilities via BidBoard <team@bidboardconnect.example>", TO,
            "Bid Invite: Water Treatment Plant No. 2 Chemical Feed Piping Replacement Project",
            "Fri, 28 Aug 2026 06:17:33 -0600",
            [("prose", "You have been invited to bid."),
             ("client_name", "Client: Idaho Springs Municipal Utilities District"),
             ("project_title", "Project: Water Treatment Plant No. 2 Chemical Feed Piping Replacement"),
             ("prose", "Bid package: Process piping"),
             ("location", "Location: Idaho Springs, CO"),
             ("bid_due_date", "Bids due: November 3, 2026 at 2:00 PM MT"),
             ("prose", "Project lead: Constance Abernathy-Ruiz, District Engineer. Phone 555-0188."),
             ("prose", "View this RFP: https://bidboardconnect.example/rfp/ISMUD-2026-1174"),
             ("prose", "No job walk has been scheduled for this package."),
             ("prose", "Attached: scope narrative and commercial terms.")],
            role="platform invitation"),
        pdf_part(V2P + "/case_11_scope.pdf", [
            (H, "SCOPE NARRATIVE AND COMMERCIAL TERMS"),
            ("prose", "Replacement of the chemical feed piping serving the coagulant and disinfection systems, including containment piping, feed pumps, and calibration columns."),
            ("trade_scope", "Base bid trades: plumbing and process piping."),
            ("estimated_project_value", "Engineer's estimate is $420,000."),
            ("prose", "Construction start: March 8, 2027. Substantial completion: July 16, 2027."),
            ("bond_insurance", MUNI_BOND_TEXT),
        ], role="scope attachment"),
    ],
    fields={
        "client_name": F("Idaho Springs Municipal Utilities District", low("Idaho Springs Municipal Utilities District")),
        "project_title": F("Water Treatment Plant No. 2 Chemical Feed Piping Replacement", low("Water Treatment Plant No. 2 Chemical Feed Piping Replacement")),
        "trade_scope": F(["plumbing", "piping"], ["piping", "plumbing"]),
        "location": F("Idaho Springs, CO", "idaho springs, co"),
        "bid_due_date": F("November 3, 2026", "2026-11-03", {"time_local": "14:00"}),
        "estimated_project_value": F("$420,000", M(420000)),
        "bond_insurance": F("10% bid bond; 100% performance and payment; $2M/$4M GL", MUNI_BOND),
        "walkthrough_date": None,
    },
    absent_notes={"walkthrough_date": "Invitation states no job walk has been scheduled."},
    construction_window=["2027-03-08", "2027-07-16"],
)

# --------------------------------------------------------------------- 12
# ADVERSARIAL: addendum supersedes the bid date; alternates are not base scope.
add(
    id="case_12", format="pdf_hard",
    parts=[pdf_part(V2P + "/case_12.pdf", [
        (H, "SILVER ASPEN REGIONAL MEDICAL CAMPUS"),
        ("client_name", "OWNER: Silver Aspen Regional Medical Campus"),
        ("prose", "PROJECT MANUAL - VOLUME 1 OF 3. Solicitation SARMC-CP-2026-03."),
        ("project_title", "PROJECT: Central Plant Upgrade"),
        ("location", "SITE: Castle Rock, CO"),
        ("prose", "BID DATE: October 16, 2026 at 2:00 PM MT"),
        ("walkthrough_date", "PRE-BID WALK: September 30, 2026 at 7:30 AM"),
        ("prose", "NOTICE TO BIDDERS: This project manual is issued subject to addenda. Dates appearing on this cover sheet are as-issued and may be superseded by addendum. Refer to Part 4 for all issued addenda."),
        ("__pagebreak__", ""),
        (H, "PART 1 - SUMMARY OF WORK"),
        ("prose", "Replacement and expansion of the central utility plant: demolition of two steam-to-hot-water converters, three new condensing hot water boilers, replacement of the primary chilled water pumping assembly, new hydronic distribution piping, and complete replacement of the plant control system."),
        ("trade_scope", "Base Bid trades are mechanical (HVAC), process and hydronic piping, and automatic temperature controls."),
        ("prose", "ALTERNATE NO. 1 is a separately priced add alternate covering standpipe and fire suppression riser modifications in the plant penthouse. Alternate No. 1 is NOT part of the Base Bid. Bidders who do not hold a fire protection license may bid the Base Bid and decline Alternate No. 1 without prejudice."),
        (H, "PART 2 - COMMERCIAL TERMS"),
        ("estimated_project_value", "ENGINEER ESTIMATE: $1,800,000 to $2,100,000"),
        ("prose", "CONSTRUCTION START: March 15, 2027. SUBSTANTIAL COMPLETION: November 30, 2027."),
        ("bond_insurance", STD_BOND_TEXT),
        ("__pagebreak__", ""),
        (H, "PART 3 - SCHEDULE OF QUANTITIES"),
        ("__mono__", "                                    BASE BID   ALT 1\nSPEC     DESCRIPTION              UNIT     QTY     QTY\n-------- ------------------------ ---- ------- -------\n23 52 16 Condensing hot water boiler EA       3       0\n23 21 23 Primary CHW pump, 60 HP     EA       4       0\n23 21 13 Hydronic piping, welded     LF   5,820       0\n23 09 23 DDC plant controller        LS       1       0\n21 12 00 Standpipe riser modification EA      0       6\n21 13 16 Wet pipe sprinkler relocation EA     0       4"),
        ("prose", "NOTE: The ALT 1 QTY column applies to Alternate No. 1 only. Items showing a BASE BID QTY of 0 are excluded from the Base Bid scope. Spec sections 21 12 00 and 21 13 16 are fire protection and are carried under Alternate No. 1 exclusively."),
        ("__pagebreak__", ""),
        (H, "PART 4 - ADDENDA ISSUED"),
        ("prose", "ADDENDUM NO. 1, issued September 4, 2026. Item 1.1: boiler manufacturer list amended to add one approved manufacturer. No change to the bid date results from this addendum."),
        ("prose", "ADDENDUM NO. 2, issued September 25, 2026."),
        ("bid_due_date", "Item 2.1: THE BID DATE IS EXTENDED. Bids are now due November 6, 2026 at 2:00 PM MT. The bid date of October 16, 2026 shown on the cover sheet is superseded and shall not be relied upon."),
        ("prose", "Item 2.2: The pre-bid walk-through held September 30, 2026 is not rescheduled. Firms that attended remain eligible to bid."),
        ("prose", "Item 2.3: Alternate No. 1 remains a separately priced add alternate. Several bidders asked whether the standpipe work is included in the Base Bid. It is not."),
    ])],
    fields={
        "client_name": F("Silver Aspen Regional Medical Campus", low("Silver Aspen Regional Medical Campus")),
        "project_title": F("Central Plant Upgrade", low("Central Plant Upgrade")),
        "trade_scope": F(["hvac", "piping", "controls"], ["controls", "hvac", "piping"]),
        "location": F("Castle Rock, CO", "castle rock, co"),
        "bid_due_date": F("November 6, 2026", "2026-11-06", {"time_local": "14:00"}),
        "estimated_project_value": F("$1,800,000 to $2,100,000", M(1800000, 2100000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("September 30, 2026", "2026-09-30"),
    },
    traps=[{"kind": "addendum_supersedes", "field": "bid_due_date",
            "naive_value": "2026-10-16", "correct_value": "2026-11-06"},
           {"kind": "alternate_read_as_base", "field": "trade_scope",
            "naive_value": ["controls", "fire_protection", "hvac", "piping"],
            "correct_value": ["controls", "hvac", "piping"]}],
    construction_window=["2027-03-15", "2027-11-30"],
)

# --------------------------------------------------------------------- 13
# New shape: platform invitation is complete, but the VALUE never appears.
add(
    id="case_13", format="platform_invitation_with_attachment",
    parts=[
        email_part(
            V2E + "/case_13.eml",
            "Trailhead Medical Partners via BidBoard <team@bidboardconnect.example>", TO,
            "Bid Invite: Trailhead Surgery Center Mechanical Fitout Project",
            "Mon, 31 Aug 2026 08:05:00 -0600",
            [("prose", "You have been invited to bid."),
             ("client_name", "Client: Trailhead Medical Partners"),
             ("project_title", "Project: Trailhead Surgery Center Mechanical Fitout"),
             ("prose", "Bid package: Division 22, 23 and 25"),
             ("location", "Location: Lakewood, CO"),
             ("bid_due_date", "Bids due: October 27, 2026 at 4:00 PM MT"),
             ("walkthrough_date", "Job walk: October 8, 2026 at 8:00 AM"),
             ("prose", "Project lead: Sunniva Kowalczyk-Bell, Project Executive. Phone 555-0119."),
             ("prose", "Attached: scope narrative.")],
            role="platform invitation"),
        pdf_part(V2P + "/case_13_scope.pdf", [
            (H, "SCOPE NARRATIVE"),
            ("prose", "Mechanical fitout of four operating rooms and the sterile processing suite, including medical gas rough-in coordination with the certified installer."),
            ("trade_scope", "Base bid trades: HVAC, plumbing, and building automation controls."),
            ("prose", "Construction start: May 17, 2027. Substantial completion: November 12, 2027."),
            ("prose", "The Owner has not released a construction budget for this package. Bidders shall price the documents as issued."),
            ("bond_insurance", STD_BOND_TEXT),
        ], role="scope attachment"),
    ],
    fields={
        "client_name": F("Trailhead Medical Partners", low("Trailhead Medical Partners")),
        "project_title": F("Trailhead Surgery Center Mechanical Fitout", low("Trailhead Surgery Center Mechanical Fitout")),
        "trade_scope": F(["hvac", "plumbing", "controls"], ["controls", "hvac", "plumbing"]),
        "location": F("Lakewood, CO", "lakewood, co"),
        "bid_due_date": F("October 27, 2026", "2026-10-27", {"time_local": "16:00"}),
        "estimated_project_value": None,
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("October 8, 2026", "2026-10-08"),
    },
    absent_notes={"estimated_project_value": "Attachment states the Owner has not released a budget."},
    construction_window=["2027-05-17", "2027-11-12"],
)

# --------------------------------------------------------------------- 14
# ADVERSARIAL: an addendum changes a MATERIAL TERM rather than a date.
add(
    id="case_14", format="pdf_rfp_with_addendum",
    parts=[pdf_part(V2P + "/case_14.pdf", [
        (H, "INVITATION TO BID"),
        ("client_name", "Owner: Prairie Junction Water Reclamation Authority"),
        ("project_title", "Project: Headworks Odour Control Mechanical Package"),
        ("location", "Project Location: Greeley, CO"),
        ("trade_scope", "Trades Required: HVAC, sheet metal, and process piping"),
        (H, "SECTION 1 - SCOPE"),
        ("prose", "Installation of a foul air collection and treatment system at the headworks structure, including FRP ductwork, two carbon adsorption vessels, exhaust fans, and associated process piping."),
        (H, "SECTION 2 - SCHEDULE AND BUDGET"),
        ("estimated_project_value", "Engineer's estimate: $1,650,000"),
        ("bid_due_date", "Bid due: November 17, 2026 at 2:00 PM MT"),
        ("walkthrough_date", "Pre-bid walk-through: October 29, 2026 at 9:00 AM"),
        ("prose", "Construction start: April 26, 2027. Substantial completion: October 8, 2027."),
        (H, "SECTION 3 - BONDING AND INSURANCE"),
        ("prose", "Bid security shall be 5% of the bid amount. Performance and payment bonds are each 100% of the contract price. Commercial general liability of $1,000,000 per occurrence and $2,000,000 aggregate."),
        ("__pagebreak__", ""),
        (H, "ADDENDUM NO. 1 - ISSUED OCTOBER 30, 2026"),
        ("prose", "Item 1.1: Drawing M-104, revise duct routing at the grit chamber as shown on attached sketch SK-M-02."),
        ("bond_insurance", "Item 1.2: SECTION 3 IS AMENDED. Bid security is increased to 10% of the bid amount. Commercial general liability limits are increased to $2,000,000 per occurrence and $4,000,000 aggregate. Performance and payment bonds remain 100% of the contract price. The limits shown in Section 3 are superseded."),
        ("prose", "Item 1.3: No change to the bid date results from this addendum."),
    ])],
    fields={
        "client_name": F("Prairie Junction Water Reclamation Authority", low("Prairie Junction Water Reclamation Authority")),
        "project_title": F("Headworks Odour Control Mechanical Package", low("Headworks Odour Control Mechanical Package")),
        "trade_scope": F(["hvac", "sheet_metal", "piping"], ["hvac", "piping", "sheet_metal"]),
        "location": F("Greeley, CO", "greeley, co"),
        "bid_due_date": F("November 17, 2026", "2026-11-17", {"time_local": "14:00"}),
        "estimated_project_value": F("$1,650,000", M(1650000)),
        "bond_insurance": F("10% bid bond after Addendum 1; 100% performance and payment; $2M/$4M GL",
                            bond(bid=10, perf=100, pay=100, occ=2000000, agg=4000000)),
        "walkthrough_date": F("October 29, 2026", "2026-10-29"),
    },
    traps=[{"kind": "addendum_changes_material_term", "field": "bond_insurance",
            "naive_value": {"required": True, "bid_bond_pct": 5, "performance_bond_pct": 100,
                            "payment_bond_pct": 100, "gl_per_occurrence_usd": 1000000,
                            "gl_aggregate_usd": 2000000},
            "correct_value": {"required": True, "bid_bond_pct": 10, "performance_bond_pct": 100,
                              "payment_bond_pct": 100, "gl_per_occurrence_usd": 2000000,
                              "gl_aggregate_usd": 4000000},
            "note": "Addendum 1 raises the bid bond and the liability limits. The superseded "
                    "figures appear first and read as the answer."}],
    construction_window=["2027-04-26", "2027-10-08"],
)

# --------------------------------------------------------------------- 15
# New regime: federal Miller Act bonding, 20 percent bid guarantee.
add(
    id="case_15", format="pdf_federal",
    parts=[pdf_part(V2P + "/case_15.pdf", [
        (H, "SOLICITATION, OFFER AND AWARD"),
        ("client_name", "Contracting Activity: Rocky Flats Federal Center Facilities Office"),
        ("project_title", "Project: Building 27 Chilled Water Plant Replacement"),
        ("location", "Place of Performance: Lakewood, CO"),
        ("trade_scope", "Trades Required: HVAC, piping, and controls"),
        (H, "SECTION B - SCOPE"),
        ("prose", "Removal of two existing air-cooled chillers and installation of three replacement units, associated chilled water piping modifications, pump replacement, and integration to the existing facility control system."),
        (H, "SECTION F - SCHEDULE"),
        ("estimated_project_value", "Government estimate: $2,400,000"),
        ("bid_due_date", "Offers are due December 1, 2026 at 2:00 PM MT"),
        ("walkthrough_date", "Site visit: November 5, 2026 at 9:00 AM"),
        ("prose", "Period of performance: June 7, 2027 through December 17, 2027."),
        (H, "SECTION I - BONDS AND INSURANCE"),
        ("bond_insurance", "Pursuant to the Miller Act, a bid guarantee of 20% of the bid price is required with the offer. Performance and payment bonds shall each be 100% of the contract price. The Contractor shall maintain commercial general liability of $2,000,000 per occurrence and $4,000,000 aggregate."),
    ])],
    fields={
        "client_name": F("Rocky Flats Federal Center Facilities Office", low("Rocky Flats Federal Center Facilities Office")),
        "project_title": F("Building 27 Chilled Water Plant Replacement", low("Building 27 Chilled Water Plant Replacement")),
        "trade_scope": F(["hvac", "piping", "controls"], ["controls", "hvac", "piping"]),
        "location": F("Lakewood, CO", "lakewood, co"),
        "bid_due_date": F("December 1, 2026", "2026-12-01", {"time_local": "14:00"}),
        "estimated_project_value": F("$2,400,000", M(2400000)),
        "bond_insurance": F("20% Miller Act bid guarantee; 100% performance and payment; $2M/$4M GL",
                            bond(bid=20, perf=100, pay=100, occ=2000000, agg=4000000)),
        "walkthrough_date": F("November 5, 2026", "2026-11-05"),
    },
    construction_window=["2027-06-07", "2027-12-17"],
)

# --------------------------------------------------------------------- 16
add(
    id="case_16", format="pdf_municipal",
    parts=[pdf_part(V2P + "/case_16.pdf", [
        (H, "NOTICE INVITING SEALED BIDS"),
        ("client_name", "Owner: City of Broomfield Public Works Department"),
        ("project_title", "Project: Municipal Service Center Boiler Replacement"),
        ("location", "Project Location: Broomfield, CO"),
        ("trade_scope", "Trades Required: HVAC and piping"),
        (H, "ARTICLE 1 - SCOPE"),
        ("prose", "Replacement of two atmospheric boilers with high-efficiency condensing units, new primary loop piping, combustion air modifications, and flue replacement. Prevailing wage rates apply to this project."),
        (H, "ARTICLE 2 - SCHEDULE AND BUDGET"),
        ("estimated_project_value", "Engineer's estimate: $780,000"),
        ("bid_due_date", "Bids due: October 30, 2026 at 10:00 AM MT"),
        ("walkthrough_date", "Mandatory pre-bid conference: October 13, 2026 at 10:00 AM. Attendance is mandatory."),
        ("prose", "Construction start: March 1, 2027. Substantial completion: June 25, 2027."),
        (H, "ARTICLE 3 - BONDS AND INSURANCE"),
        ("bond_insurance", MUNI_BOND_TEXT),
    ])],
    fields={
        "client_name": F("City of Broomfield Public Works Department", low("City of Broomfield Public Works Department")),
        "project_title": F("Municipal Service Center Boiler Replacement", low("Municipal Service Center Boiler Replacement")),
        "trade_scope": F(["hvac", "piping"], ["hvac", "piping"]),
        "location": F("Broomfield, CO", "broomfield, co"),
        "bid_due_date": F("October 30, 2026", "2026-10-30", {"time_local": "10:00"}),
        "estimated_project_value": F("$780,000", M(780000)),
        "bond_insurance": F("10% bid bond; 100% performance and payment; $2M/$4M GL", MUNI_BOND),
        "walkthrough_date": F("October 13, 2026", "2026-10-13"),
    },
    construction_window=["2027-03-01", "2027-06-25"],
)

# --------------------------------------------------------------------- 17
# ADVERSARIAL: a later reply in the thread supersedes the bid date. No addendum.
add(
    id="case_17", format="email_thread_superseded",
    parts=[email_part(
        V2E + "/case_17.eml",
        "Ignatius Baumgartner-Vale <ibaumgartner@keystoneridgebuilders.example>", TO,
        "RE: RE: Golden Foundry Lofts - mechanical scope",
        "Wed, 02 Sep 2026 16:41:09 -0600",
        [("prose", "Summit Peak,"),
         ("bid_due_date", "Correction to my earlier note: our client moved the deadline. Please disregard the September 28 date I gave you below. Proposals are now due October 12, 2026 at 5:00 PM MT."),
         ("prose", "Everything else in the scope stands. Sorry for the churn."),
         ("prose", "Ignatius Baumgartner-Vale, Keystone Ridge Builders"),
         ("prose", "-----Original Message-----\nSent: Monday, August 31, 2026 9:12 AM\nSubject: RE: Golden Foundry Lofts - mechanical scope"),
         ("client_name", "Keystone Ridge Builders is soliciting subcontractor proposals as general contractor for the owner."),
         ("project_title", "The project is the Golden Foundry Lofts Adaptive Reuse."),
         ("location", "The building is in Golden, CO."),
         ("trade_scope", "Mechanical scope for this package is HVAC, plumbing, and sheet metal."),
         ("prose", "Proposals are due September 28, 2026 at 5:00 PM MT."),
         ("estimated_project_value", "Our internal budget for the mechanical package is $1,150,000."),
         ("walkthrough_date", "Site walk: September 16, 2026 at 1:00 PM."),
         ("bond_insurance", STD_BOND_TEXT),
         ("prose", "Construction runs February 1, 2027 to August 13, 2027.")])],
    fields={
        "client_name": F("Keystone Ridge Builders", low("Keystone Ridge Builders")),
        "project_title": F("Golden Foundry Lofts Adaptive Reuse", low("Golden Foundry Lofts Adaptive Reuse")),
        "trade_scope": F(["hvac", "plumbing", "sheet_metal"], ["hvac", "plumbing", "sheet_metal"]),
        "location": F("Golden, CO", "golden, co"),
        "bid_due_date": F("October 12, 2026", "2026-10-12", {"time_local": "17:00"}),
        "estimated_project_value": F("$1,150,000", M(1150000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("September 16, 2026", "2026-09-16"),
    },
    traps=[{"kind": "thread_reply_supersedes", "field": "bid_due_date",
            "naive_value": "2026-09-28", "correct_value": "2026-10-12",
            "note": "The superseded date sits in the quoted original below the correction, "
                    "which is the larger and more detailed part of the message."}],
    construction_window=["2027-02-01", "2027-08-13"],
)

# --------------------------------------------------------------------- 18
add(
    id="case_18", format="email_gc_scope_sheet",
    parts=[email_part(
        V2E + "/case_18.eml",
        "Wilhelmina Ostrowski-Kane <wostrowski@antlercreekconstruction.example>", TO,
        "Scope sheet - Antler Creek Commons Phase 1 mechanical",
        "Tue, 01 Sep 2026 11:22:47 -0600",
        [("prose", "Scope sheet attached below in the body, per your request."),
         ("client_name", "GC: Antler Creek Construction"),
         ("project_title", "PROJECT ............ Antler Creek Commons Phase 1"),
         ("location", "LOCATION ........... Denver, CO"),
         ("trade_scope", "TRADES ............. HVAC, sheet metal"),
         ("estimated_project_value", "BUDGET ............. $960,000"),
         ("bid_due_date", "BIDS DUE ........... October 5, 2026, 12:00 PM MT"),
         ("walkthrough_date", "JOB WALK ........... September 21, 2026"),
         ("prose", "CONSTRUCTION ....... 2027-01-18 to 2027-05-07"),
         ("bond_insurance", STD_BOND_TEXT),
         ("prose", "INCLUSIONS ......... rooftop units, curbs, ductwork, grilles, TAB\nEXCLUSIONS ......... controls, plumbing, fire protection, roofing patch"),
         ("prose", "Wilhelmina Ostrowski-Kane, Project Manager")])],
    fields={
        "client_name": F("Antler Creek Construction", low("Antler Creek Construction")),
        "project_title": F("Antler Creek Commons Phase 1", low("Antler Creek Commons Phase 1")),
        "trade_scope": F(["hvac", "sheet_metal"], ["hvac", "sheet_metal"]),
        "location": F("Denver, CO", "denver, co"),
        "bid_due_date": F("October 5, 2026", "2026-10-05", {"time_local": "12:00"}),
        "estimated_project_value": F("$960,000", M(960000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("September 21, 2026", "2026-09-21"),
    },
    construction_window=["2027-01-18", "2027-05-07"],
)
