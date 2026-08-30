"""Corpus v2 cases 01 to 05: revised from v1 with aligned commercial terms."""
from data.v2.common import *  # noqa: F401,F403

CASES = []


def add(**kw):
    CASES.append(kw)


# ==========================================================================
# Revised from v1 (01 to 12). Same documents in spirit, commercial terms
# aligned, and the two platform cases rewritten per the research.
# ==========================================================================

add(
    id="case_01", format="email_rfp",
    parts=[email_part(
        V2E + "/case_01.eml",
        "Marguerite Delacroix-Whitfield <mdelacroix@cascaderidge-k12.example>", TO,
        "Invitation to Bid - Cascade Ridge Middle School RTU Replacement",
        "Tue, 25 Aug 2026 09:14:22 -0600",
        [("prose", "Good morning,"),
         ("client_name", "Cascade Ridge School District 12 is soliciting competitive sealed bids from qualified mechanical contractors."),
         ("project_title", "The project is the Cascade Ridge Middle School RTU Replacement."),
         ("prose", "The work consists of removal and replacement of fourteen packaged rooftop units serving the classroom wings, associated ductwork modifications, new roof curbs, and full integration into the District's existing building automation system."),
         ("trade_scope", "Trades required: HVAC, sheet metal, and controls."),
         ("location", "Site: Cascade Ridge Middle School, Arvada, CO."),
         ("walkthrough_date", "Mandatory pre-bid walk-through: September 11, 2026 at 9:00 AM local time. Attendance is mandatory."),
         ("bid_due_date", "Sealed bids are due no later than September 25, 2026 at 2:00 PM MT."),
         ("estimated_project_value", "The District's engineer has established a construction budget of $850,000."),
         ("bond_insurance", MUNI_BOND_TEXT),
         ("prose", "Construction is scheduled to commence February 15, 2027 with substantial completion required by July 30, 2027."),
         ("prose", "Marguerite Delacroix-Whitfield\nFacilities Contracting Officer")])],
    fields={
        "client_name": F("Cascade Ridge School District 12", low("Cascade Ridge School District 12")),
        "project_title": F("Cascade Ridge Middle School RTU Replacement", low("Cascade Ridge Middle School RTU Replacement")),
        "trade_scope": F(["hvac", "sheet_metal", "controls"], ["controls", "hvac", "sheet_metal"]),
        "location": F("Arvada, CO", "arvada, co"),
        "bid_due_date": F("September 25, 2026", "2026-09-25", {"time_local": "14:00"}),
        "estimated_project_value": F("$850,000", M(850000)),
        "bond_insurance": F("10% bid bond; 100% performance and payment; $2M/$4M GL", MUNI_BOND),
        "walkthrough_date": F("September 11, 2026", "2026-09-11"),
    },
    construction_window=["2027-02-15", "2027-07-30"],
)

add(
    id="case_02", format="email_rfp",
    parts=[email_part(
        V2E + "/case_02.eml",
        "Terrence Oyelaran-Boothe <toyelaran@brightmesa-property.example>", TO,
        "Domestic water piping retrofit - Bright Mesa Commons",
        "Wed, 26 Aug 2026 15:42:08 -0600",
        [("prose", "Hi,"),
         ("client_name", "Bright Mesa Property Group is looking for bids on this one."),
         ("project_title", "The job is the Bright Mesa Commons Domestic Water Piping Retrofit."),
         ("trade_scope", "Scope is plumbing and piping only. No HVAC, no controls."),
         ("location", "Property is in Boulder, CO."),
         ("estimated_project_value", "Budget we're working with is $310,000."),
         ("bid_due_date", "Bids are due September 18, 2026."),
         ("prose", "We're not holding a formal walk-through for this one, but I can get you into the mechanical rooms any weekday with a day's notice."),
         ("bond_insurance", "This is a private project and we are not requiring any bonding on it. No bid bond, no performance bond, no payment bond. A standard certificate of insurance is fine."),
         ("prose", "Work would start March 1, 2027 and we'd want it wrapped by June 15, 2027."),
         ("prose", "Terrence Oyelaran-Boothe\nDirector of Asset Management")])],
    fields={
        "client_name": F("Bright Mesa Property Group", low("Bright Mesa Property Group")),
        "project_title": F("Bright Mesa Commons Domestic Water Piping Retrofit", low("Bright Mesa Commons Domestic Water Piping Retrofit")),
        "trade_scope": F(["plumbing", "piping"], ["piping", "plumbing"]),
        "location": F("Boulder, CO", "boulder, co"),
        "bid_due_date": F("September 18, 2026", "2026-09-18"),
        "estimated_project_value": F("$310,000", M(310000)),
        "bond_insurance": F("No bonding required", bond(required=False)),
        "walkthrough_date": None,
    },
    absent_notes={"walkthrough_date": "Source states no formal walk-through will be held."},
    construction_window=["2027-03-01", "2027-06-15"],
)

add(
    id="case_03", format="email_rfp_forwarded",
    parts=[email_part(
        V2E + "/case_03.eml",
        "Priyanka Raghunathan-Six <praghunathan@vergecoldchain.example>", TO,
        "FW: Verge Cold Chain - Larimer Street Cold Storage Buildout",
        "Thu, 27 Aug 2026 11:03:55 -0600",
        [("prose", "Forwarding along, Dmitri asked me to get this in front of a few more mechanical shops since our usual refrigeration sub is booked solid."),
         ("prose", "-----Original Message-----\nFrom: Dmitri Vasconcelos-Ahn\nSent: Thursday, August 27, 2026 8:12 AM"),
         ("client_name", "Verge Cold Chain Holdings is issuing an invitation to bid."),
         ("project_title", "The package is the Larimer Street Cold Storage Buildout."),
         ("prose", "The package is refrigeration-led. Scope includes a low-temperature ammonia refrigeration system serving four freezer rooms, associated process piping, and evaporator coil installation."),
         ("trade_scope", "Trades required: refrigeration, piping, HVAC."),
         ("location", "Facility is in Denver, CO."),
         ("estimated_project_value", "Engineer's estimate is $700,000."),
         ("walkthrough_date", "Site walk is set for September 14, 2026."),
         ("bid_due_date", "Bids close September 30, 2026."),
         ("bond_insurance", STD_BOND_TEXT),
         ("prose", "Construction window is April 5, 2027 through August 20, 2027."),
         ("prose", "Dmitri Vasconcelos-Ahn\nPreconstruction Manager")])],
    fields={
        "client_name": F("Verge Cold Chain Holdings", low("Verge Cold Chain Holdings")),
        "project_title": F("Larimer Street Cold Storage Buildout", low("Larimer Street Cold Storage Buildout")),
        "trade_scope": F(["refrigeration", "piping", "hvac"], ["hvac", "piping", "refrigeration"]),
        "location": F("Denver, CO", "denver, co"),
        "bid_due_date": F("September 30, 2026", "2026-09-30"),
        "estimated_project_value": F("$700,000", M(700000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("September 14, 2026", "2026-09-14"),
    },
    construction_window=["2027-04-05", "2027-08-20"],
)

add(
    id="case_04", format="email_rfp",
    parts=[email_part(
        V2E + "/case_04.eml",
        "Aurelio Nakashima-Prather <anakashima@mesaverdanaindustrial.example>", TO,
        "ITB - Mesa Verdana Industrial Park Building C - HVAC",
        "Wed, 26 Aug 2026 07:28:40 -0600",
        [("prose", "Summit Peak,"),
         ("project_title", "We are bidding out the mechanical package for Mesa Verdana Industrial Park Building C."),
         ("location", "The site is in Grand Junction, CO."),
         ("trade_scope", "Scope: HVAC and controls."),
         ("prose", "Six split systems, one makeup air unit, and BAS point mapping to the existing park-wide front end. No plumbing."),
         ("estimated_project_value", "Estimated value: $480,000."),
         ("walkthrough_date", "Walk-through: September 8, 2026 at 10:00 AM."),
         ("bid_due_date", "Bids due: September 22, 2026."),
         ("bond_insurance", STD_BOND_TEXT),
         ("prose", "Construction runs January 11, 2027 to May 28, 2027."),
         ("client_name", "Aurelio Nakashima-Prather, Mesa Verdana Industrial Partners")])],
    fields={
        "client_name": F("Mesa Verdana Industrial Partners", low("Mesa Verdana Industrial Partners")),
        "project_title": F("Mesa Verdana Industrial Park Building C", low("Mesa Verdana Industrial Park Building C")),
        "trade_scope": F(["hvac", "controls"], ["controls", "hvac"]),
        "location": F("Grand Junction, CO", "grand junction, co"),
        "bid_due_date": F("September 22, 2026", "2026-09-22"),
        "estimated_project_value": F("$480,000", M(480000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("September 8, 2026", "2026-09-08"),
    },
    construction_window=["2027-01-11", "2027-05-28"],
)

add(
    id="case_05", format="email_rfp_tabular",
    parts=[email_part(
        V2E + "/case_05.eml",
        "Rosalind Achterberg-Nwosu <rachterberg@helioptixdata.example>", TO,
        "Helioptix Data Campus Phase II - Mechanical Bid Package",
        "Fri, 28 Aug 2026 13:55:17 -0600",
        [("prose", "BID PACKAGE HDC2-M-01 - MECHANICAL"),
         ("client_name", "Issuing entity ......... Helioptix Data Infrastructure"),
         ("project_title", "Project ................ Helioptix Data Campus Phase II"),
         ("location", "Site ................... Denver, CO"),
         ("trade_scope", "Trades required ...... HVAC, piping, sheet metal, controls"),
         ("prose", "Scope .................. Chilled water plant, four 900-ton centrifugal chillers; primary and secondary distribution piping; 28 computer room air handlers; sheet metal containment."),
         ("estimated_project_value", "Engineer's estimate .. $4,500,000"),
         ("bid_due_date", "Bid due date ......... October 9, 2026, 4:00 PM MT"),
         ("walkthrough_date", "Pre-bid walk-through . September 17, 2026"),
         ("prose", "Construction start ... March 22, 2027\nSubstantial compl. ... December 18, 2027"),
         ("bond_insurance", STD_BOND_TEXT),
         ("prose", "Rosalind Achterberg-Nwosu\nProcurement Lead")])],
    fields={
        "client_name": F("Helioptix Data Infrastructure", low("Helioptix Data Infrastructure")),
        "project_title": F("Helioptix Data Campus Phase II", low("Helioptix Data Campus Phase II")),
        "trade_scope": F(["hvac", "piping", "sheet_metal", "controls"], ["controls", "hvac", "piping", "sheet_metal"]),
        "location": F("Denver, CO", "denver, co"),
        "bid_due_date": F("October 9, 2026", "2026-10-09", {"time_local": "16:00"}),
        "estimated_project_value": F("$4,500,000", M(4500000)),
        "bond_insurance": F("5% bid bond; 100% performance and payment; $2M/$4M GL", STD_BOND),
        "walkthrough_date": F("September 17, 2026", "2026-09-17"),
    },
    construction_window=["2027-03-22", "2027-12-18"],
)
