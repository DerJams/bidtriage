"""Corpus v2 cases 19 to 30. New document shapes and failure modes."""
from data.v2.common import *  # noqa: F401,F403

CASES = []


def add(**kw):
    CASES.append(kw)


H = "__heading__"

# --------------------------------------------------------------------- 19
add(
    id="case_19", format="pdf_design_build",
    parts=[pdf_part(V2P + "/case_19.pdf", [
        (H, "REQUEST FOR PROPOSALS - DESIGN BUILD"),
        ("client_name", "Owner: Meridian Hollow Hospitality Group"),
        ("project_title", "Project: Meridian Hollow Conference Centre Mechanical Design Build"),
        ("location", "Project Location: Denver, CO"),
        ("trade_scope", "Trades Required: HVAC, piping, sheet metal, and controls"),
        (H, "PART A - DELIVERY"),
        ("prose", "This is a design-build procurement. The successful proposer carries design responsibility for the mechanical systems from schematic through construction documents, and shall carry the allowances listed in Part C within the proposed price."),
        (H, "PART B - COMMERCIAL"),
        ("estimated_project_value", "Owner's not-to-exceed budget for this package is $5,500,000."),
        ("bid_due_date", "Proposals due: November 24, 2026 at 3:00 PM MT"),
        ("walkthrough_date", "Pre-proposal site visit: November 2, 2026 at 10:00 AM"),
        ("prose", "Construction start: July 12, 2027. Substantial completion: April 28, 2028."),
        (H, "PART C - ALLOWANCES"),
        ("prose", "Carry an allowance of $180,000 for owner-directed kitchen exhaust modifications and $95,000 for acoustic treatment at the rooftop units. Allowances are included within the not-to-exceed figure."),
        (H, "PART D - BONDS AND INSURANCE"),
        ("bond_insurance", STD_BOND_TEXT),
    ])],
    fields={
        "client_name": F("Meridian Hollow Hospitality Group", low("Meridian Hollow Hospitality Group")),
        "project_title": F("Meridian Hollow Conference Centre Mechanical Design Build", low("Meridian Hollow Conference Centre Mechanical Design Build")),
        "trade_scope": F(["hvac", "piping", "sheet_metal", "controls"], ["controls", "hvac", "piping", "sheet_metal"]),
        "location": F("Denver, CO", "denver, co"),
        "bid_due_date": F("November 24, 2026", "2026-11-24", {"time_local": "15:00"}),
        "estimated_project_value": F("$5,500,000", M(5500000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("November 2, 2026", "2026-11-02"),
    },
    construction_window=["2027-07-12", "2028-04-28"],
)

# --------------------------------------------------------------------- 20
add(
    id="case_20", format="pdf_rfp",
    parts=[pdf_part(V2P + "/case_20.pdf", [
        (H, "INVITATION TO BID"),
        ("client_name", "Owner: Tenmile Basin Recreation District"),
        ("project_title", "Project: Tenmile Basin Ice Arena Dehumidification Upgrade"),
        ("location", "Project Location: Frisco, CO"),
        ("trade_scope", "Trades Required: HVAC and controls"),
        (H, "SECTION 1 - SCOPE"),
        ("prose", "Replacement of the arena dehumidification units, new supply ductwork above the seating bowl, and integration of the new equipment into the District's existing control front end. The ice plant refrigeration system is existing to remain and is not part of this scope."),
        (H, "SECTION 2 - SCHEDULE AND BUDGET"),
        ("estimated_project_value", "Engineer's estimate: $890,000"),
        ("bid_due_date", "Bid due: November 12, 2026 at 2:00 PM MT"),
        ("walkthrough_date", "An optional pre-bid walk-through will be held November 3, 2026 at 11:00 AM. Attendance is not mandatory and bids from firms that do not attend will be accepted."),
        ("prose", "Construction start: May 24, 2027. Substantial completion: August 20, 2027."),
        (H, "SECTION 3 - BONDS AND INSURANCE"),
        ("bond_insurance", MUNI_BOND_TEXT),
    ])],
    fields={
        "client_name": F("Tenmile Basin Recreation District", low("Tenmile Basin Recreation District")),
        "project_title": F("Tenmile Basin Ice Arena Dehumidification Upgrade", low("Tenmile Basin Ice Arena Dehumidification Upgrade")),
        "trade_scope": F(["hvac", "controls"], ["controls", "hvac"]),
        "location": F("Frisco, CO", "frisco, co"),
        "bid_due_date": F("November 12, 2026", "2026-11-12", {"time_local": "14:00"}),
        "estimated_project_value": F("$890,000", M(890000)),
        "bond_insurance": F("10% bid bond; 100% performance and payment; $2M/$4M GL", MUNI_BOND),
        "walkthrough_date": F("November 3, 2026", "2026-11-03"),
    },
    construction_window=["2027-05-24", "2027-08-20"],
)

# --------------------------------------------------------------------- 21
# Two locations in one package: the owner's offices and the actual site.
add(
    id="case_21", format="platform_invitation_with_attachment",
    parts=[
        email_part(
            V2E + "/case_21.eml",
            "Alpenglow Resort Holdings via BidBoard <team@bidboardconnect.example>", TO,
            "Bid Invite: Alpenglow Village Lodge Mechanical Replacement Project",
            "Wed, 02 Sep 2026 07:30:00 -0600",
            [("prose", "You have been invited to bid."),
             ("client_name", "Client: Alpenglow Resort Holdings"),
             ("project_title", "Project: Alpenglow Village Lodge Mechanical Replacement"),
             ("prose", "Owner's corporate offices are at 1400 Seventeenth Street, Denver, CO. All correspondence and bid submissions go to the Denver office."),
             ("location", "Place of performance: Vail, CO"),
             ("bid_due_date", "Bids due: November 19, 2026 at 4:00 PM MT"),
             ("walkthrough_date", "Job walk: October 28, 2026 at 9:00 AM"),
             ("prose", "Project lead: Bartholomew Quintanilla-Reed, Development Manager."),
             ("prose", "Attached: scope narrative and commercial terms.")],
            role="platform invitation"),
        pdf_part(V2P + "/case_21_scope.pdf", [
            (H, "SCOPE NARRATIVE AND COMMERCIAL TERMS"),
            ("prose", "Replacement of the lodge boiler plant and snowmelt heat exchangers, with new distribution piping through the lower level."),
            ("trade_scope", "Base bid trades: HVAC and piping."),
            ("estimated_project_value", "Owner's construction budget is $1,320,000."),
            ("prose", "Construction start: April 19, 2027. Substantial completion: September 30, 2027."),
            ("bond_insurance", STD_BOND_TEXT),
        ], role="scope attachment"),
    ],
    fields={
        "client_name": F("Alpenglow Resort Holdings", low("Alpenglow Resort Holdings")),
        "project_title": F("Alpenglow Village Lodge Mechanical Replacement", low("Alpenglow Village Lodge Mechanical Replacement")),
        "trade_scope": F(["hvac", "piping"], ["hvac", "piping"]),
        "location": F("Vail, CO", "vail, co"),
        "bid_due_date": F("November 19, 2026", "2026-11-19", {"time_local": "16:00"}),
        "estimated_project_value": F("$1,320,000", M(1320000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("October 28, 2026", "2026-10-28"),
    },
    construction_window=["2027-04-19", "2027-09-30"],
)

# --------------------------------------------------------------------- 22
# The value appears only in the attached bid form, never in the email.
add(
    id="case_22", format="email_with_bid_form",
    parts=[
        email_part(
            V2E + "/case_22.eml",
            "Océane Thibodeaux-Marsh <othibodeaux@quarryviewpartners.example>", TO,
            "Quarry View Commerce Park - mechanical bid package",
            "Thu, 03 Sep 2026 10:14:00 -0600",
            [("prose", "Good afternoon,"),
             ("client_name", "Quarry View Partners is inviting bids for the mechanical package."),
             ("project_title", "The project is the Quarry View Commerce Park Building 2 Fitout."),
             ("location", "Site is in Lakewood, CO."),
             ("trade_scope", "Trades: HVAC, plumbing, and controls."),
             ("bid_due_date", "Bids are due October 22, 2026 at 3:00 PM MT."),
             ("walkthrough_date", "Walk-through: October 6, 2026 at 8:30 AM."),
             ("prose", "Construction runs March 15, 2027 to July 30, 2027."),
             ("prose", "The engineer's estimate and the bonding requirements are on the attached bid form. Please price the form as issued."),
             ("prose", "Oceane Thibodeaux-Marsh, Development Associate")],
            role="cover email"),
        pdf_part(V2P + "/case_22_bidform.pdf", [
            (H, "BID FORM"),
            ("prose", "Quarry View Commerce Park Building 2 Fitout. Submit this form complete."),
            ("estimated_project_value", "Engineer's estimate for this package: $740,000"),
            ("prose", "BASE BID .......................... $ ____________"),
            ("prose", "ALTERNATE 1, dock heaters ......... $ ____________"),
            ("bond_insurance", STD_BOND_TEXT),
            ("prose", "Acknowledge addenda received: ____ ____ ____"),
        ], role="bid form attachment"),
    ],
    fields={
        "client_name": F("Quarry View Partners", low("Quarry View Partners")),
        "project_title": F("Quarry View Commerce Park Building 2 Fitout", low("Quarry View Commerce Park Building 2 Fitout")),
        "trade_scope": F(["hvac", "plumbing", "controls"], ["controls", "hvac", "plumbing"]),
        "location": F("Lakewood, CO", "lakewood, co"),
        "bid_due_date": F("October 22, 2026", "2026-10-22", {"time_local": "15:00"}),
        "estimated_project_value": F("$740,000", M(740000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("October 6, 2026", "2026-10-06"),
    },
    construction_window=["2027-03-15", "2027-07-30"],
)

# --------------------------------------------------------------------- 23
# Multi-phase construction. Phase 1 lands inside the at-capacity window.
add(
    id="case_23", format="pdf_multiphase",
    parts=[pdf_part(V2P + "/case_23.pdf", [
        (H, "INVITATION TO BID - PHASED CONSTRUCTION"),
        ("client_name", "Owner: Bramblewood Senior Living Trust"),
        ("project_title", "Project: Bramblewood Campus Mechanical Renewal"),
        ("location", "Project Location: Boulder, CO"),
        ("trade_scope", "Trades Required: HVAC, plumbing, and controls"),
        (H, "SECTION 1 - PHASING"),
        ("prose", "The Work is phased to keep the campus occupied throughout. Phase 1 covers the north residence wing. Phase 2 covers the commons and clinic. Both phases are awarded under a single contract and a single bid."),
        ("prose", "Phase 1 construction: October 26, 2026 through February 12, 2027. Phase 2 construction: March 1, 2027 through August 6, 2027. The contract construction window therefore runs from the Phase 1 start to the Phase 2 completion."),
        (H, "SECTION 2 - SCHEDULE AND BUDGET"),
        ("estimated_project_value", "Engineer's estimate: $1,980,000"),
        ("bid_due_date", "Bid due: October 8, 2026 at 2:00 PM MT"),
        ("walkthrough_date", "Pre-bid walk-through: September 23, 2026 at 9:00 AM"),
        (H, "SECTION 3 - BONDS AND INSURANCE"),
        ("bond_insurance", STD_BOND_TEXT),
    ])],
    fields={
        "client_name": F("Bramblewood Senior Living Trust", low("Bramblewood Senior Living Trust")),
        "project_title": F("Bramblewood Campus Mechanical Renewal", low("Bramblewood Campus Mechanical Renewal")),
        "trade_scope": F(["hvac", "plumbing", "controls"], ["controls", "hvac", "plumbing"]),
        "location": F("Boulder, CO", "boulder, co"),
        "bid_due_date": F("October 8, 2026", "2026-10-08", {"time_local": "14:00"}),
        "estimated_project_value": F("$1,980,000", M(1980000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("September 23, 2026", "2026-09-23"),
    },
    construction_window=["2026-10-26", "2027-08-06"],
)

# --------------------------------------------------------------------- 24
# Walk-through is by appointment, so no date exists. An abstention test.
add(
    id="case_24", format="email_rfp",
    parts=[email_part(
        V2E + "/case_24.eml",
        "Ferdinand Achebe-Lindqvist <fachebe@northgatelearning.example>", TO,
        "Northgate Learning Centre - mechanical bids",
        "Fri, 04 Sep 2026 09:00:00 -0600",
        [("prose", "Hello,"),
         ("client_name", "Northgate Learning Centre is requesting mechanical bids."),
         ("project_title", "The project is the Northgate Learning Centre Ventilation Improvements."),
         ("location", "We are in Arvada, CO."),
         ("trade_scope", "Trades needed: HVAC and sheet metal."),
         ("prose", "The work is new ventilation for six classrooms plus a small ERV, ducted through the existing ceiling plenum."),
         ("estimated_project_value", "Our board approved $395,000 for this work."),
         ("bid_due_date", "Bids are due October 16, 2026 at 4:00 PM MT."),
         ("prose", "There is no scheduled walk-through. Site visits are by appointment; call the front office and we will let you in any afternoon."),
         ("bond_insurance", STD_BOND_TEXT),
         ("prose", "Construction would run June 14, 2027 to August 20, 2027, over the summer break."),
         ("prose", "Ferdinand Achebe-Lindqvist, Operations Director")])],
    fields={
        "client_name": F("Northgate Learning Centre", low("Northgate Learning Centre")),
        "project_title": F("Northgate Learning Centre Ventilation Improvements", low("Northgate Learning Centre Ventilation Improvements")),
        "trade_scope": F(["hvac", "sheet_metal"], ["hvac", "sheet_metal"]),
        "location": F("Arvada, CO", "arvada, co"),
        "bid_due_date": F("October 16, 2026", "2026-10-16", {"time_local": "16:00"}),
        "estimated_project_value": F("$395,000", M(395000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": None,
    },
    absent_notes={"walkthrough_date": "Site visits are by appointment; no date exists."},
    construction_window=["2027-06-14", "2027-08-20"],
)

# --------------------------------------------------------------------- 25
# Alternates-only pricing request. No base scope value is given.
add(
    id="case_25", format="platform_invitation",
    parts=[email_part(
        V2E + "/case_25.eml",
        "Cottonwood Bend Developments via BidBoard <team@bidboardconnect.example>", TO,
        "Bid Invite: Cottonwood Bend Retail Alternates Pricing Project",
        "Mon, 07 Sep 2026 08:45:00 -0600",
        [("prose", "You have been invited to price alternates only."),
         ("client_name", "Client: Cottonwood Bend Developments"),
         ("project_title", "Project: Cottonwood Bend Retail Alternates Pricing"),
         ("location", "Location: Broomfield, CO"),
         ("trade_scope", "Trades: HVAC and controls"),
         ("bid_due_date", "Pricing due: October 20, 2026 at 5:00 PM MT"),
         ("prose", "This request covers ALTERNATES ONLY. The base bid package was awarded in July. Price Alternate 3 (rooftop unit upsizing) and Alternate 5 (economizer controls retrofit) as separate line items."),
         ("prose", "No overall construction value is released for the alternates package, and construction dates will follow from the base contract schedule once alternates are accepted."),
         ("prose", "No job walk is scheduled."),
         ("bond_insurance", STD_BOND_TEXT),
         ("prose", "Project lead: Anneliese Fontaine-Barros.")])],
    fields={
        "client_name": F("Cottonwood Bend Developments", low("Cottonwood Bend Developments")),
        "project_title": F("Cottonwood Bend Retail Alternates Pricing", low("Cottonwood Bend Retail Alternates Pricing")),
        "trade_scope": F(["hvac", "controls"], ["controls", "hvac"]),
        "location": F("Broomfield, CO", "broomfield, co"),
        "bid_due_date": F("October 20, 2026", "2026-10-20", {"time_local": "17:00"}),
        "estimated_project_value": None,
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": None,
    },
    absent_notes={"estimated_project_value": "Alternates-only request; no value released.",
                  "walkthrough_date": "Invitation states no job walk is scheduled."},
    construction_window=None,
)

# --------------------------------------------------------------------- 26
# Negotiated work: no competitive bid date and no released value.
add(
    id="case_26", format="pdf_negotiated",
    parts=[pdf_part(V2P + "/case_26.pdf", [
        (H, "REQUEST FOR QUALIFICATIONS AND BUDGETARY INPUT"),
        ("client_name", "Owner: Chapel Rock Congregational Trust"),
        ("project_title", "Project: Chapel Rock Sanctuary Mechanical Renewal"),
        ("location", "Project Location: Golden, CO"),
        ("trade_scope", "Trades Required: HVAC and piping"),
        (H, "PART 1 - PROCUREMENT METHOD"),
        ("prose", "This is a negotiated procurement. The Trust is not issuing a competitive bid and there is no sealed bid deadline. Interested contractors are asked to submit qualifications and budgetary input, after which the Trust will negotiate a contract with a single firm."),
        (H, "PART 2 - SCOPE"),
        ("prose", "Replacement of the sanctuary air handling equipment and the associated hydronic piping, with attention to acoustic performance during services."),
        (H, "PART 3 - COMMERCIAL"),
        ("prose", "No construction budget has been established. Establishing a budget is part of the requested budgetary input. Construction dates will be set during negotiation."),
        ("walkthrough_date", "Site tour: October 14, 2026 at 10:00 AM"),
        ("bond_insurance", STD_BOND_TEXT),
    ])],
    fields={
        "client_name": F("Chapel Rock Congregational Trust", low("Chapel Rock Congregational Trust")),
        "project_title": F("Chapel Rock Sanctuary Mechanical Renewal", low("Chapel Rock Sanctuary Mechanical Renewal")),
        "trade_scope": F(["hvac", "piping"], ["hvac", "piping"]),
        "location": F("Golden, CO", "golden, co"),
        "bid_due_date": None,
        "estimated_project_value": None,
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("October 14, 2026", "2026-10-14"),
    },
    absent_notes={"bid_due_date": "Negotiated procurement; no sealed bid deadline exists.",
                  "estimated_project_value": "No construction budget has been established."},
    construction_window=None,
)

# --------------------------------------------------------------------- 27
add(
    id="case_27", format="email_urgent",
    parts=[email_part(
        V2E + "/case_27.eml",
        "Xiomara Delgado-Fenwick <xdelgado@ridgelinemechanicalgc.example>", TO,
        "URGENT - need pricing Friday - Vista Marketplace RTU swap",
        "Tue, 08 Sep 2026 17:52:00 -0600",
        [("prose", "Short notice, sorry."),
         ("client_name", "Ridgeline Mechanical GC lost a sub and needs coverage."),
         ("project_title", "Job is the Vista Marketplace RTU Swap."),
         ("location", "Denver, CO."),
         ("trade_scope", "HVAC and sheet metal."),
         ("estimated_project_value", "Budget is $265,000."),
         ("bid_due_date", "I need numbers by September 18, 2026 at 5:00 PM MT."),
         ("prose", "No walk-through, there is no time. Roof access photos attached separately."),
         ("bond_insurance", "No bonding on this one. Certificate of insurance only."),
         ("prose", "Construction is February 22, 2027 to April 9, 2027."),
         ("prose", "Xiomara Delgado-Fenwick")])],
    fields={
        "client_name": F("Ridgeline Mechanical GC", low("Ridgeline Mechanical GC")),
        "project_title": F("Vista Marketplace RTU Swap", low("Vista Marketplace RTU Swap")),
        "trade_scope": F(["hvac", "sheet_metal"], ["hvac", "sheet_metal"]),
        "location": F("Denver, CO", "denver, co"),
        "bid_due_date": F("September 18, 2026", "2026-09-18", {"time_local": "17:00"}),
        "estimated_project_value": F("$265,000", M(265000)),
        "bond_insurance": F("No bonding required", bond(required=False)),
        "walkthrough_date": None,
    },
    absent_notes={"walkthrough_date": "Source states there is no walk-through."},
    construction_window=["2027-02-22", "2027-04-09"],
)

# --------------------------------------------------------------------- 28
# Not-to-exceed ceiling, below the size band.
add(
    id="case_28", format="pdf_rfp",
    parts=[pdf_part(V2P + "/case_28.pdf", [
        (H, "INVITATION TO BID"),
        ("client_name", "Owner: Larkspur Lane Housing Cooperative"),
        ("project_title", "Project: Larkspur Lane Boiler Room Repiping"),
        ("location", "Project Location: Boulder, CO"),
        ("trade_scope", "Trades Required: piping and plumbing"),
        (H, "SECTION 1 - SCOPE"),
        ("prose", "Repiping of the boiler room primary loop, replacement of isolation valves, and new expansion tank. The boilers themselves are existing to remain."),
        (H, "SECTION 2 - SCHEDULE AND BUDGET"),
        ("estimated_project_value", "The Cooperative has set a not-to-exceed ceiling of $180,000 for this work. Bids above the ceiling will be rejected."),
        ("bid_due_date", "Bid due: October 26, 2026 at 1:00 PM MT"),
        ("walkthrough_date", "Pre-bid walk-through: October 12, 2026 at 4:00 PM"),
        ("prose", "Construction start: March 22, 2027. Substantial completion: May 14, 2027."),
        (H, "SECTION 3 - BONDS AND INSURANCE"),
        ("bond_insurance", STD_BOND_TEXT),
    ])],
    fields={
        "client_name": F("Larkspur Lane Housing Cooperative", low("Larkspur Lane Housing Cooperative")),
        "project_title": F("Larkspur Lane Boiler Room Repiping", low("Larkspur Lane Boiler Room Repiping")),
        "trade_scope": F(["piping", "plumbing"], ["piping", "plumbing"]),
        "location": F("Boulder, CO", "boulder, co"),
        "bid_due_date": F("October 26, 2026", "2026-10-26", {"time_local": "13:00"}),
        "estimated_project_value": F("$180,000", M(180000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("October 12, 2026", "2026-10-12"),
    },
    construction_window=["2027-03-22", "2027-05-14"],
)

# --------------------------------------------------------------------- 29
# Trade scope is split: part of it in the invitation, part in the attachment.
add(
    id="case_29", format="platform_invitation_with_attachment",
    parts=[
        email_part(
            V2E + "/case_29.eml",
            "Sable Creek Industrial via BidBoard <team@bidboardconnect.example>", TO,
            "Bid Invite: Sable Creek Cold Box Ventilation Project",
            "Wed, 09 Sep 2026 06:55:00 -0600",
            [("prose", "You have been invited to bid."),
             ("client_name", "Client: Sable Creek Industrial Properties"),
             ("project_title", "Project: Sable Creek Cold Box Ventilation"),
             ("prose", "Bid package: Mechanical ventilation"),
             ("location", "Location: Longmont, CO"),
             ("bid_due_date", "Bids due: November 6, 2026 at 11:00 AM MT"),
             ("walkthrough_date", "Job walk: October 20, 2026 at 7:30 AM"),
             ("prose", "This invitation covers the ventilation and ductwork scope. The attachment lists the full trade breakdown including the controls scope carried under this package."),
             ("prose", "Project lead: Nikolaj Ferreira-Stout.")],
            role="platform invitation"),
        pdf_part(V2P + "/case_29_scope.pdf", [
            (H, "SCOPE NARRATIVE AND COMMERCIAL TERMS"),
            ("prose", "Ventilation for the ambient-temperature cold box enclosure, including make-up air, exhaust ductwork, and the control sequences that stage the fans."),
            ("trade_scope", "Full trade breakdown for this package: HVAC, sheet metal, and controls. Refrigeration for the cold box itself is by the Owner's specialty vendor and is excluded from this package."),
            ("estimated_project_value", "Owner's construction budget is $1,470,000."),
            ("prose", "Construction start: May 10, 2027. Substantial completion: September 3, 2027."),
            ("bond_insurance", STD_BOND_TEXT),
        ], role="scope attachment"),
    ],
    fields={
        "client_name": F("Sable Creek Industrial Properties", low("Sable Creek Industrial Properties")),
        "project_title": F("Sable Creek Cold Box Ventilation", low("Sable Creek Cold Box Ventilation")),
        "trade_scope": F(["hvac", "sheet_metal", "controls"], ["controls", "hvac", "sheet_metal"]),
        "location": F("Longmont, CO", "longmont, co"),
        "bid_due_date": F("November 6, 2026", "2026-11-06", {"time_local": "11:00"}),
        "estimated_project_value": F("$1,470,000", M(1470000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("October 20, 2026", "2026-10-20"),
    },
    construction_window=["2027-05-10", "2027-09-03"],
)

# --------------------------------------------------------------------- 30
# Owner and GC named separately, and the scope carries a trade not self-performed.
add(
    id="case_30", format="email_owner_and_gc",
    parts=[email_part(
        V2E + "/case_30.eml",
        "Perpetua Vandermolen-Ashby <pvandermolen@stonehavenbuilders.example>", TO,
        "Bid solicitation - Harborlight Distribution Centre mechanical and fire protection",
        "Thu, 10 Sep 2026 13:20:00 -0600",
        [("prose", "Good afternoon,"),
         ("prose", "Stonehaven Builders is acting as construction manager on this project and is issuing this solicitation on the Owner's behalf. Submit bids to Stonehaven; the contract will be held directly with the Owner."),
         ("client_name", "The Owner is Harborlight Logistics Trust."),
         ("project_title", "The project is the Harborlight Distribution Centre Mechanical Package."),
         ("location", "The facility is in Broomfield, CO."),
         ("trade_scope", "This package covers HVAC, sheet metal, and fire protection. The fire protection scope is included in the base bid and is not an alternate."),
         ("estimated_project_value", "The Owner's budget is $1,540,000."),
         ("bid_due_date", "Bids are due November 2, 2026 at 2:00 PM MT."),
         ("walkthrough_date", "Site walk: October 15, 2026 at 8:00 AM."),
         ("bond_insurance", STD_BOND_TEXT),
         ("prose", "Construction runs April 12, 2027 to September 17, 2027."),
         ("prose", "Perpetua Vandermolen-Ashby, Stonehaven Builders")])],
    fields={
        "client_name": F("Harborlight Logistics Trust", low("Harborlight Logistics Trust")),
        "project_title": F("Harborlight Distribution Centre Mechanical Package", low("Harborlight Distribution Centre Mechanical Package")),
        "trade_scope": F(["hvac", "sheet_metal", "fire_protection"], ["fire_protection", "hvac", "sheet_metal"]),
        "location": F("Broomfield, CO", "broomfield, co"),
        "bid_due_date": F("November 2, 2026", "2026-11-02", {"time_local": "14:00"}),
        "estimated_project_value": F("$1,540,000", M(1540000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("October 15, 2026", "2026-10-15"),
    },
    construction_window=["2027-04-12", "2027-09-17"],
)
