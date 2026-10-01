#!/usr/bin/env python3
"""Generate a deterministic corpus of synthetic sample CVs as PDFs.

Every CV is a plausible 1-2 page document built from templates and name/company
pools. No CV is a copy of any real person. The first line of every PDF is the
banner:  SYNTHETIC SAMPLE CV - not a real person

The corpus is deliberately varied so a screening model faces hard cases:
  - food-sector QA / R&D / production people, plus clearly unrelated profiles
    (IT, marketing, mechanical engineering, accounting, hospitality/retail)
  - 0 to 20 years of experience
  - ages above and below 28, with a mix of stated birth dates, inferred-only
    age, and no age evidence
  - military service completed / pending / exempted / not stated / female (N/A)
  - career shapes: steady growth at one employer, lateral moves, job hopping
    (4-6 employers in ~3 years), unclear/overlapping timelines, and a few
    deliberately messy internally-contradictory CVs
  - a mix of Greek- and English-language CVs, some with degraded characters
    (e.g. "θητεIα") to imitate bad PDF text layers

Deterministic: the same --seed always produces the same corpus. Generating N
CVs is a prefix of generating M>N CVs (per-block plans depend only on the block
index, and per-CV content on the CV index).

Requires only python3 + PyMuPDF (fitz). No other dependencies.

Usage:
  python3 scripts/make-sample-cvs.py [--count N] [--out DIR] [--seed INT] [--clean]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import sys
import unicodedata
from datetime import date

try:
    import fitz  # pymupdf
except ImportError:
    sys.stderr.write("pymupdf not installed: python3 -m pip install pymupdf\n")
    sys.exit(3)

BANNER = "SYNTHETIC SAMPLE CV - not a real person"
REFERENCE_TODAY = date(2026, 9, 17)  # fixed so the corpus is reproducible
BLOCK = 20
GENERATOR_VERSION = 1

# ---------------------------------------------------------------------------
# Fonts. Arial Unicode has full Greek + the special glyphs we use for degraded
# text (OHM SIGN U+2126, INCREMENT U+2206, MICRO SIGN U+00B5). We subset on save
# so each PDF stays ~50 KB. Fallbacks cover non-macOS hosts.
# ---------------------------------------------------------------------------
FONT_BODY_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
]
FONT_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def pick_font(candidates: list[str]) -> str:
    for p in candidates:
        if os.path.exists(p):
            return p
    raise SystemExit(
        "no usable font found; install a Greek-capable TTF and add it to "
        "FONT_BODY_CANDIDATES / FONT_BOLD_CANDIDATES"
    )


# ---------------------------------------------------------------------------
# Degradation: imitate a bad PDF text layer (as seen in the real Greek CVs).
# Accented vowels collapse to 'I', omega -> OHM SIGN, delta -> INCREMENT,
# mu -> MICRO SIGN. Applied to the fully assembled text of selected CVs.
# ---------------------------------------------------------------------------
_DEGRADE = {
    "ή": "I", "ί": "I", "ύ": "I", "ό": "I", "ώ": "I", "έ": "I", "ά": "I",
    "ΐ": "I", "ΰ": "I", "ϊ": "I", "ϋ": "I",
    "Ή": "I", "Ί": "I", "Ύ": "I", "Ό": "I", "Ώ": "I", "Έ": "I", "Ά": "I",
    "ω": "\u2126", "Ω": "\u2126",
    "μ": "\u00b5",
    "Δ": "\u2206",
}
_DEGRADE_RE = re.compile("|".join(re.escape(c) for c in _DEGRADE))


def degrade(text: str) -> str:
    text = _DEGRADE_RE.sub(lambda m: _DEGRADE[m.group(0)], text)
    # the real CVs render "R&D" as "R&D;" (stray semicolon from the text layer)
    text = text.replace("R&D", "R&D;")
    return text


# ---------------------------------------------------------------------------
# Name / place pools. Each entry is (greek, latin).
# ---------------------------------------------------------------------------
GREEK_NAMES = [
    ("Γεώργιος", "Georgios", "m"), ("Νικόλαος", "Nikolaos", "m"),
    ("Δημήτριος", "Dimitrios", "m"), ("Κωνσταντίνος", "Konstantinos", "m"),
    ("Ιωάννης", "Ioannis", "m"), ("Παναγιώτης", "Panagiotis", "m"),
    ("Βασίλειος", "Vasileios", "m"), ("Χρήστος", "Christos", "m"),
    ("Αντώνιος", "Antonios", "m"), ("Σπυρίδων", "Spyridon", "m"),
    ("Αθανάσιος", "Athanasios", "m"), ("Μιχαήλ", "Michalis", "m"),
    ("Αλέξανδρος", "Alexandros", "m"), ("Στέφανος", "Stefanos", "m"),
    ("Λεωνίδας", "Leonidas", "m"), ("Ηλίας", "Ilias", "m"),
    ("Ευάγγελος", "Evangelos", "m"), ("Θεόδωρος", "Theodoros", "m"),
    ("Πέτρος", "Petros", "m"), ("Ανδρέας", "Andreas", "m"),
    ("Μάρκος", "Markos", "m"), ("Χαράλαμπος", "Charalampos", "m"),
    ("Εμμανουήλ", "Emmanouil", "m"), ("Φώτιος", "Fotios", "m"),
    ("Μαρία", "Maria", "f"), ("Ελένη", "Eleni", "f"),
    ("Αικατερίνη", "Aikaterini", "f"), ("Σοφία", "Sofia", "f"),
    ("Αναστασία", "Anastasia", "f"), ("Δήμητρα", "Dimitra", "f"),
    ("Ιωάννα", "Ioanna", "f"), ("Χριστίνα", "Christina", "f"),
    ("Βασιλική", "Vasiliki", "f"), ("Αγγελική", "Angeliki", "f"),
    ("Παρασκευή", "Paraskevi", "f"), ("Ευαγγελία", "Evangelia", "f"),
    ("Θεοδώρα", "Theodora", "f"), ("Ειρήνη", "Eirini", "f"),
    ("Ναταλία", "Natalia", "f"), ("Άννα", "Anna", "f"),
    ("Γεωργία", "Georgia", "f"), ("Ζωή", "Zoi", "f"),
    ("Δέσποινα", "Despoina", "f"), ("Σταματία", "Stamatia", "f"),
]
GREEK_SURNAMES = [
    ("Παπαδόπουλος", "Papadopoulos"), ("Κωνσταντίνου", "Konstantinou"),
    ("Σταματίου", "Stamatiou"), ("Παπαγεωργίου", "Papageorgiou"),
    ("Νικολάου", "Nikolaou"), ("Γεωργίου", "Georgiou"),
    ("Δημητρίου", "Dimitriou"), ("Αντωνίου", "Antoniou"),
    ("Βασιλείου", "Vasileiou"), ("Οικονόμου", "Oikonomou"),
    ("Μακρής", "Makris"), ("Λάμπρου", "Lamprou"),
    ("Χατζής", "Chatzis"), ("Παππάς", "Pappas"),
    ("Σαμαράς", "Samaras"), ("Καραγιάννης", "Karayannis"),
    ("Βλάχος", "Vlachos"), ("Ζαχαριάδης", "Zachariadis"),
    ("Μανωλάκης", "Manolakis"), ("Σιδέρης", "Sideris"),
    ("Φωτόπουλος", "Fotopoulos"), ("Αναγνώστου", "Anagnostou"),
    ("Χριστοδούλου", "Christodoulou"), ("Δρακόπουλος", "Drakopoulos"),
    ("Καλογερόπουλος", "Kalogeropoulos"), ("Σπανός", "Spanos"),
    ("Τζανετάκης", "Tzanetakis"), ("Ρίζος", "Rizos"),
]
# a few international-sounding names for the unrelated profiles
INTERNATIONAL_NAMES = [
    ("Daniel", "Daniel", "m"), ("Marco", "Marco", "m"), ("Victor", "Victor", "m"),
    ("Elena", "Elena", "f"), ("Julia", "Julia", "f"), ("Nadia", "Nadia", "f"),
    ("Sofia", "Sofia", "f"), ("Mark", "Mark", "m"), ("Anna", "Anna", "f"),
]
CITIES = [
    ("Θεσσαλονίκη", "Thessaloniki"), ("Αθήνα", "Athens"), ("Πάτρα", "Patras"),
    ("Ηράκλειο", "Heraklion"), ("Λάρισα", "Larissa"), ("Βόλος", "Volos"),
    ("Ιωάννινα", "Ioannina"), ("Καβάλα", "Kavala"), ("Χανιά", "Chania"),
    ("Σέρρες", "Serres"), ("Ξάνθη", "Xanthi"), ("Τρίκαλα", "Trikala"),
    ("Κομοτηνή", "Komotini"), ("Αλεξανδρούπολη", "Alexandroupoli"),
]

# ---------------------------------------------------------------------------
# Sector definitions. Each sector carries title ladders (junior -> senior),
# companies (greek, latin), bullets, degrees, skills and summary fragments.
# ---------------------------------------------------------------------------
SECTORS = {
    "food_qa": {
        "label": "food quality / QA",
        "ladder_el": ["Τεχνικός Ποιοτικού Ελέγχου", "Υπεύθυνος Ποιοτικού Ελέγχου",
                      "Senior Υπεύθυνος Ποιότητας", "Διευθυντής Διασφάλισης Ποιότητας"],
        "ladder_en": ["Quality Control Technician", "Quality Control Supervisor",
                      "Senior Quality Assurance Officer", "Quality Assurance Manager"],
        "companies": [
            ("ΒΙΟΣΚΑΛ Α.Ε.", "VIOSKAL S.A."), ("ΔΕΛΤΑ ΤΡΟΦΙΜΑ", "DELTA FOODS"),
            ("ΜΕΒΓΑΛ Α.Ε.", "MEVGAL S.A."), ("ΝΙΚΑΣ Α.Ε.", "NIKAS S.A."),
            ("ΚΡΙ ΚΡΙ Α.Ε.", "KRI KRI S.A."), ("ΧΑΤΖΗΓΙΑΝΝΑΚΗΣ Α.Β.Ε.Ε.", "CHATZIGIANNAKIS S.A."),
            ("ΦΡΕΣΚΑ ΦΑΡΜ Α.Ε.", "FRESH FARM S.A."), ("ΟΛΥΜΠΟΣ Α.Ε.", "OLYMPOS S.A."),
            ("ΓΙΩΤΗΣ Α.Ε.", "GIOTIS S.A."), ("ΣΕΛΟΝΤΑ Α.Ε.", "SELONDA S.A."),
        ],
        "bullets_el": [
            "Έλεγχος ποιότητας πρώτων υλών και τελικών προϊόντων",
            "Τήρηση αρχείων και καταγραφή αποκλίσεων ποιότητας",
            "Εφαρμογή συστήματος HACCP και διαχείριση πιστοποιήσεων ISO 22000",
            "Διενέργεια μικροβιολογικών και φυσικοχημικών αναλύσεων",
            "Συνεργασία με την παραγωγή για τη μείωση απορρίψεων",
            "Επιθεωρήσεις προμηθευτών και εσωτερικοί έλεγχοι",
            "Διαχείριση παραπόνων πελατών και διορθωτικών ενεργειών",
            "Εκπαίδευση προσωπικού σε θέματα υγιεινής και ασφάλειας τροφίμων",
        ],
        "bullets_en": [
            "Quality inspection of raw materials and finished products",
            "Maintaining records and logging quality deviations",
            "Implementing HACCP and managing ISO 22000 certification",
            "Performing microbiological and physicochemical analyses",
            "Working with production to reduce waste and rejects",
            "Supplier audits and internal quality audits",
            "Handling customer complaints and corrective actions",
            "Training staff on food hygiene and safety",
        ],
        "degrees_el": [
            "Πτυχίο Χημείας με κατεύθυνση Τροφίμων, ΑΠΘ",
            "Πτυχίο Τεχνολογίας Τροφίμων, ΤΕΙ Θεσσαλονίκης",
            "Πτυχίο Γεωπονίας, Γεωπονικό Πανεπιστήμιο Αθηνών",
            "Πτυχίο Χημείας, ΕΚΠΑ",
            "Πτυχίο Βιολογίας, Πανεπιστήμιο Πατρών",
        ],
        "degrees_en": [
            "BSc Chemistry (Food Science direction), Aristotle University of Thessaloniki",
            "BSc Food Technology, TEI of Thessaloniki",
            "BSc Agronomy, Agricultural University of Athens",
            "BSc Chemistry, National and Kapodistrian University of Athens",
            "BSc Biology, University of Patras",
        ],
        "skills_el": ["HACCP", "ISO 22000", "ISO 9001", "BRC", "IFS", "Μικροβιολογικές αναλύσεις",
                      "Εσωτερικοί έλεγχοι", "Excel"],
        "skills_en": ["HACCP", "ISO 22000", "ISO 9001", "BRC", "IFS", "Microbiological analysis",
                      "Internal audits", "Excel"],
        "summary_el": [
            "Επαγγελματίας ποιοτικού ελέγχου με {y} χρόνια εμπειρίας στη βιομηχανία τροφίμων.",
            "Εξειδίκευση στην εφαρμογή HACCP και στη διαχείριση ποιότητας.",
            "Αναζητώ θέση σε εταιρεία τροφίμων με προοπτική εξέλιξης.",
        ],
        "summary_en": [
            "Quality professional with {y} years of experience in the food industry.",
            "Specialised in HACCP implementation and quality management.",
            "Seeking a role in a food company with room to grow.",
        ],
    },
    "food_rnd": {
        "label": "food R&D / product development",
        "ladder_el": ["Τεχνολόγος Τροφίμων", "R&D Food Technologist",
                      "Senior R&D Technologist", "Διευθυντής R&D"],
        "ladder_en": ["Food Technologist", "R&D Food Technologist",
                      "Senior R&D Technologist", "R&D Manager"],
        "companies": [
            ("ΒΙΟΣΚΑΛ Α.Ε.", "VIOSKAL S.A."), ("ΑΛΦΑ ΤΡΟΦΙΜΑ Α.Ε.", "ALFA TROFIMA S.A."),
            ("ΜΕΒΓΑΛ Α.Ε.", "MEVGAL S.A."), ("ΝΙΚΑΣ Α.Ε.", "NIKAS S.A."),
            ("ΚΡΙ ΚΡΙ Α.Ε.", "KRI KRI S.A."), ("ΟΛΥΜΠΟΣ Α.Ε.", "OLYMPOS S.A."),
            ("ΠΑΠΑΔΟΠΟΥΛΟΣ Α.Ε.", "PAPADOPOULOS BISCUITS"), ("ΛΟΥΞ Α.Ε.", "LOUX S.A."),
            ("CANDIA ΒΙΟΜΗΧΑΝΙΑ", "CANDIA INDUSTRIES"), ("ΑΡΓΩ ΤΡΟΦΙΜΑ", "ARGO FOODS"),
        ],
        "bullets_el": [
            "Ανάπτυξη νέων προϊόντων και βελτιστοποίηση συνταγολογίου",
            "Δοκιμές πιλοτικής παραγωγής και κλίμακας",
            "Μελέτη διάρκειας ζωής και σταθερότητας προϊόντων",
            "Συνεργασία με marketing για consumer testing και product launch",
            "Εφαρμογή HACCP και διαχείριση πιστοποιήσεων ISO 22000",
            "Αναζήτηση νέων πρώτων υλών και προμηθευτών",
            "Τεκμηρίωση προδιαγραφών και τεχνικών φύλλων",
            "Μείωση κόστους πρώτων υλών μέσω βελτιστοποίησης συνταγών",
        ],
        "bullets_en": [
            "Developing new products and optimising formulations",
            "Pilot plant and scale-up trials",
            "Shelf-life and product stability studies",
            "Working with marketing on consumer testing and product launch",
            "Implementing HACCP and managing ISO 22000 certification",
            "Sourcing new raw materials and suppliers",
            "Writing specifications and technical data sheets",
            "Reducing raw material cost through recipe optimisation",
        ],
        "degrees_el": [
            "Πτυχίο Τεχνολογίας Τροφίμων, ΤΕΙ Θεσσαλονίκης",
            "Πτυχίο Επιστήμης και Τεχνολογίας Τροφίμων, ΓΠΑ",
            "Πτυχίο Χημείας με κατεύθυνση Τροφίμων, ΑΠΘ",
            "Μεταπτυχιακό στην Επιστήμη Τροφίμων, ΑΠΘ",
            "Πτυχίο Γεωπονίας, Γεωπονικό Πανεπιστήμιο Αθηνών",
        ],
        "degrees_en": [
            "BSc Food Technology, TEI of Thessaloniki",
            "BSc Food Science and Technology, Agricultural University of Athens",
            "BSc Chemistry (Food Science direction), Aristotle University of Thessaloniki",
            "MSc Food Science, Aristotle University of Thessaloniki",
            "BSc Agronomy, Agricultural University of Athens",
        ],
        "skills_el": ["R&D", "Ανάπτυξη προϊόντων", "HACCP", "ISO 22000", "Sensory evaluation",
                      "Πιλοτική παραγωγή", "Excel", "SAP"],
        "skills_en": ["R&D", "Product development", "HACCP", "ISO 22000", "Sensory evaluation",
                      "Pilot plant", "Excel", "SAP"],
        "summary_el": [
            "Τεχνολόγος Τροφίμων με {y} χρόνια εμπειρίας σε R&D και ανάπτυξη προϊόντων.",
            "Εξειδίκευση στην ανάπτυξη νέων προϊόντων και στη διαχείριση ποιότητας.",
            "Ισχυρό υπόβαθρο σε Research and Development με αποδεδειγμένα αποτελέσματα.",
        ],
        "summary_en": [
            "Food Technologist with {y} years of experience in R&D and product development.",
            "Specialised in new product development and quality management.",
            "Strong background in Research and Development with proven results.",
        ],
    },
    "food_production": {
        "label": "food production / plant",
        "ladder_el": ["Χειριστής Γραμμής Παραγωγής", "Επόπτης Παραγωγής",
                      "Υπεύθυνος Παραγωγής", "Διευθυντής Μονάδας Παραγωγής"],
        "ladder_en": ["Production Line Operator", "Production Supervisor",
                      "Production Manager", "Plant Manager"],
        "companies": [
            ("ΜΕΒΓΑΛ Α.Ε.", "MEVGAL S.A."), ("ΝΙΚΑΣ Α.Ε.", "NIKAS S.A."),
            ("ΚΡΙ ΚΡΙ Α.Ε.", "KRI KRI S.A."), ("ΧΑΤΖΗΓΙΑΝΝΑΚΗΣ Α.Β.Ε.Ε.", "CHATZIGIANNAKIS S.A."),
            ("ΠΑΠΑΔΟΠΟΥΛΟΣ Α.Ε.", "PAPADOPOULOS BISCUITS"), ("ΓΙΩΤΗΣ Α.Ε.", "GIOTIS S.A."),
            ("ΣΕΛΟΝΤΑ Α.Ε.", "SELONDA S.A."), ("ΒΙΚΟΣ Α.Ε.", "VIKOS S.A."),
            ("ΜΑΚΕΔΟΝΙΚΗ ΖΥΜΗ", "MACEDONIAN DOUGH"), ("ΑΡΓΩ ΤΡΟΦΙΜΑ", "ARGO FOODS"),
        ],
        "bullets_el": [
            "Επίβλεψη γραμμών παραγωγής και διαχείριση προγράμματος βάρδιας",
            "Διαχείριση ομάδας τεχνιτών και χειριστών παραγωγής",
            "Βελτιστοποίηση παραμέτρων παραγωγής και αύξηση OEE",
            "Τήρηση κανόνων υγιεινής και ασφάλειας τροφίμων",
            "Συντήρηση και αποκατάσταση βλαβών εξοπλισμού",
            "Προγραμματισμός παραγωγής και διαχείριση αποθεμάτων",
            "Εφαρμογή συστήματος HACCP στην παραγωγή",
            "Μείωση απορρίψεων και βελτίωση απόδοσης γραμμής",
        ],
        "bullets_en": [
            "Supervising production lines and managing shift schedules",
            "Managing a team of technicians and line operators",
            "Optimising production parameters and increasing OEE",
            "Enforcing food hygiene and safety rules",
            "Maintenance and troubleshooting of production equipment",
            "Production planning and inventory management",
            "Applying HACCP on the production floor",
            "Reducing waste and improving line efficiency",
        ],
        "degrees_el": [
            "Πτυχίο Τεχνολογίας Τροφίμων, ΤΕΙ Θεσσαλονίκης",
            "Πτυχίο Μηχανολόγων Μηχανικών, ΑΠΘ",
            "Πτυχίο Διοίκησης Επιχειρήσεων, ΠΑΜΑΚ",
            "Πτυχίο Χημικών Μηχανικών, ΑΠΘ",
            "Απολυτήριο Λυκείου",
        ],
        "degrees_en": [
            "BSc Food Technology, TEI of Thessaloniki",
            "BSc Mechanical Engineering, Aristotle University of Thessaloniki",
            "BSc Business Administration, University of Macedonia",
            "BSc Chemical Engineering, Aristotle University of Thessaloniki",
            "High School Diploma",
        ],
        "skills_el": ["HACCP", "ISO 22000", "Προγραμματισμός παραγωγής", "OEE", "SAP",
                      "Διαχείριση ομάδας", "Συντήρηση εξοπλισμού", "Excel"],
        "skills_en": ["HACCP", "ISO 22000", "Production planning", "OEE", "SAP",
                      "Team management", "Equipment maintenance", "Excel"],
        "summary_el": [
            "Επαγγελματίας παραγωγής με {y} χρόνια εμπειρίας σε βιομηχανία τροφίμων.",
            "Εμπειρία στη διαχείριση γραμμών παραγωγής και ομάδων.",
            "Αναζητώ θέση με μεγαλύτερες ευθύνες σε μονάδα παραγωγής τροφίμων.",
        ],
        "summary_en": [
            "Production professional with {y} years of experience in the food industry.",
            "Experience managing production lines and teams.",
            "Seeking a role with more responsibility in a food manufacturing plant.",
        ],
    },
    "it": {
        "label": "IT / software",
        "ladder_el": ["Junior Software Developer", "Software Developer",
                      "Senior Software Engineer", "Tech Lead"],
        "ladder_en": ["Junior Software Developer", "Software Developer",
                      "Senior Software Engineer", "Tech Lead"],
        "companies": [
            ("COSMOTE", "COSMOTE"), ("VODAFONE ΕΛΛΑΣ", "VODAFONE GREECE"),
            ("ACCENTURE ΕΛΛΑΣ", "ACCENTURE GREECE"), ("INTRASOFT", "INTRASOFT"),
            ("NETCOMPANY", "NETCOMPANY"), ("ΟΤΕ", "OTE"),
            ("SINGULAR LOGIC", "SINGULAR LOGIC"), ("ENTERSOFT", "ENTERSOFT"),
            ("AGILE ACTORS", "AGILE ACTORS"), ("SOFTONE", "SOFTONE"),
        ],
        "bullets_el": [
            "Ανάπτυξη και συντήρηση εφαρμογών σε JavaScript και TypeScript",
            "Αυτοματοποίηση διαδικασιών και διαχείριση tickets",
            "Σχεδιασμός και υλοποίηση REST APIs",
            "Διαχείριση βάσεων δεδομένων SQL",
            "Συνεργασία με ομάδες infrastructure για escalations",
            "Τεκμηρίωση και ενημέρωση knowledge base",
            "Ανάπτυξη web εφαρμογών με HTML, CSS και JavaScript",
            "Deployment και διαχείριση hosting",
        ],
        "bullets_en": [
            "Developing and maintaining applications in JavaScript and TypeScript",
            "Automating processes and managing tickets",
            "Designing and implementing REST APIs",
            "Managing SQL databases",
            "Coordinating with infrastructure teams on escalations",
            "Documenting and updating the knowledge base",
            "Building web applications with HTML, CSS and JavaScript",
            "Deployment and hosting management",
        ],
        "degrees_el": [
            "Πτυχίο Πληροφορικής, ΑΠΘ",
            "Πτυχίο Μηχανικών Η/Υ και Πληροφορικής, Πανεπιστήμιο Πατρών",
            "Πτυχίο Εφαρμοσμένης Πληροφορικής, ΠΑΜΑΚ",
            "Πτυχίο Πληροφορικής, Οικονομικό Πανεπιστήμιο Αθηνών",
            "Πτυχίο Ηλεκτρολόγων Μηχανικών και Μηχανικών Υπολογιστών, ΕΜΠ",
        ],
        "degrees_en": [
            "BSc Computer Science, Aristotle University of Thessaloniki",
            "BSc Computer Engineering and Informatics, University of Patras",
            "BSc Applied Informatics, University of Macedonia",
            "BSc Informatics, Athens University of Economics and Business",
            "BSc Electrical and Computer Engineering, NTUA",
        ],
        "skills_el": ["JavaScript", "TypeScript", "SQL", "Git", "HTML/CSS", "ServiceNow",
                      "REST APIs", "Linux"],
        "skills_en": ["JavaScript", "TypeScript", "SQL", "Git", "HTML/CSS", "ServiceNow",
                      "REST APIs", "Linux"],
        "summary_el": [
            "Προγραμματιστής με {y} χρόνια εμπειρίας σε ανάπτυξη λογισμικού.",
            "Εξειδίκευση σε web εφαρμογές και αυτοματοποίηση.",
            "Αναζητώ θέση σε ομάδα ανάπτυξης με σύγχρονη τεχνολογία.",
        ],
        "summary_en": [
            "Software developer with {y} years of experience in software development.",
            "Specialised in web applications and automation.",
            "Seeking a role in a development team using modern technology.",
        ],
    },
    "marketing": {
        "label": "marketing / digital",
        "ladder_el": ["Marketing Assistant", "Marketing Executive",
                      "Digital Marketing Specialist", "Marketing Manager"],
        "ladder_en": ["Marketing Assistant", "Marketing Executive",
                      "Digital Marketing Specialist", "Marketing Manager"],
        "companies": [
            ("OGILVY ΕΛΛΑΣ", "OGILVY GREECE"), ("PUBLICIS ΕΛΛΑΣ", "PUBLICIS GREECE"),
            ("MINDSHARE", "MINDSHARE"), ("DDB ΑΘΗΝΑ", "DDB ATHENS"),
            ("DIGITAL AGENCY ΑΘΗΝΑ", "DIGITAL AGENCY ATHENS"), ("MEDIASTORM", "MEDIASTORM"),
            ("ΠΛΑΙΣΙΟ Α.Ε.", "PLAISIO S.A."), ("SKL AVENITIS", "SKLAVENITIS"),
        ],
        "bullets_el": [
            "Διαχείριση καμπανιών στα social media",
            "Δημιουργία περιεχομένου και copywriting",
            "Ανάλυση δεδομένων καμπανιών με Google Analytics",
            "Συνεργασία με ομάδες πωλήσεων και προϊόντος",
            "Διαχείριση προϋπολογισμού διαφήμισης",
            "Οργάνωση εκδηλώσεων και product launches",
            "SEO και βελτιστοποίηση ιστοσελίδας",
            "Δημιουργία ενημερωτικών δελτίων (newsletters)",
        ],
        "bullets_en": [
            "Managing social media campaigns",
            "Content creation and copywriting",
            "Analysing campaign data with Google Analytics",
            "Working with sales and product teams",
            "Managing advertising budgets",
            "Organising events and product launches",
            "SEO and website optimisation",
            "Creating newsletters",
        ],
        "degrees_el": [
            "Πτυχίο Διοίκησης Επιχειρήσεων, ΠΑΜΑΚ",
            "Πτυχίο Marketing και Επικοινωνίας, Οικονομικό Πανεπιστήμιο Αθηνών",
            "Πτυχίο Επικοινωνίας και ΜΜΕ, ΕΚΠΑ",
            "Πτυχίο Διοίκησης Επιχειρήσεων, ΑΠΘ",
        ],
        "degrees_en": [
            "BSc Business Administration, University of Macedonia",
            "BSc Marketing and Communication, Athens University of Economics and Business",
            "BSc Communication and Media, National and Kapodistrian University of Athens",
            "BSc Business Administration, Aristotle University of Thessaloniki",
        ],
        "skills_el": ["Google Analytics", "SEO", "Social Media", "Copywriting", "Meta Ads",
                      "Google Ads", "Excel", "Photoshop"],
        "skills_en": ["Google Analytics", "SEO", "Social Media", "Copywriting", "Meta Ads",
                      "Google Ads", "Excel", "Photoshop"],
        "summary_el": [
            "Στέλεχος marketing με {y} χρόνια εμπειρίας σε ψηφιακό και παραδοσιακό marketing.",
            "Εξειδίκευση σε καμπάνιες και ανάλυση δεδομένων.",
            "Αναζητώ θέση σε δυναμική ομάδα marketing.",
        ],
        "summary_en": [
            "Marketing professional with {y} years of experience in digital and traditional marketing.",
            "Specialised in campaigns and data analysis.",
            "Seeking a role in a dynamic marketing team.",
        ],
    },
    "mechanical": {
        "label": "mechanical engineering",
        "ladder_el": ["Μηχανικός Συντήρησης", "Maintenance Engineer",
                      "Production Engineer", "Μηχανικός Έργων"],
        "ladder_en": ["Maintenance Engineer", "Maintenance Engineer",
                      "Production Engineer", "Project Engineer"],
        "companies": [
            ("ΕΛΛΗΝΙΚΑ ΠΕΤΡΕΛΑΙΑ Α.Ε.", "HELLENIC PETROLEUM S.A."),
            ("ΤΙΤΑΝ Α.Ε.", "TITAN S.A."), ("ΧΑΛΥΒΔΟΥΡΓΙΑ ΕΛΛΑΔΟΣ", "HELLENIC STEEL"),
            ("ΣΩΛΗΝΟΥΡΓΕΙΑ ΚΟΡΙΝΘΟΥ", "CORINTH PIPEWORKS"), ("SIEMENS HELLAS", "SIEMENS HELLAS"),
            ("METKA", "METKA"), ("ΤΕΡΝΑ ΕΝΕΡΓΕΙΑΚΗ", "TERNA ENERGY"),
            ("ΜΥΤΙΛΗΝΑΙΟΣ", "MYTILINEOS"),
        ],
        "bullets_el": [
            "Συντήρηση και αποκατάσταση βλαβών σε βιομηχανικό εξοπλισμό",
            "Εγκατάσταση και προγραμματισμός PLCs (Siemens S7)",
            "Επίβλεψη γραμμών παραγωγής και διαχείριση προγράμματος συντήρησης",
            "Βελτιστοποίηση παραμέτρων παραγωγής και αύξηση OEE",
            "Τεκμηρίωση τεχνικών εγχειριδίων",
            "Διαχείριση ομάδας τεχνιτών παραγωγής",
            "Σχεδιασμός και επίβλεψη έργων",
            "Ανάλυση αιτιών βλαβών (RCA)",
        ],
        "bullets_en": [
            "Maintenance and troubleshooting of industrial equipment",
            "Installing and programming PLCs (Siemens S7)",
            "Supervising production lines and managing maintenance schedules",
            "Optimising production parameters and increasing OEE",
            "Writing technical documentation",
            "Managing a team of production technicians",
            "Designing and supervising projects",
            "Root cause analysis of failures",
        ],
        "degrees_el": [
            "Πτυχίο Μηχανολόγων Μηχανικών, ΑΠΘ",
            "Πτυχίο Μηχανολόγων Μηχανικών, ΕΜΠ",
            "Πτυχίο Μηχανολόγων Μηχανικών, Πανεπιστήμιο Πατρών",
            "Πτυχίο Ηλεκτρολόγων Μηχανικών, ΑΠΘ",
        ],
        "degrees_en": [
            "BSc Mechanical Engineering, Aristotle University of Thessaloniki",
            "BSc Mechanical Engineering, NTUA",
            "BSc Mechanical Engineering, University of Patras",
            "BSc Electrical Engineering, Aristotle University of Thessaloniki",
        ],
        "skills_el": ["PLC", "AutoCAD", "SolidWorks", "Συντήρηση", "OEE", "Διαχείριση έργων",
                      "SAP", "Excel"],
        "skills_en": ["PLC", "AutoCAD", "SolidWorks", "Maintenance", "OEE", "Project management",
                      "SAP", "Excel"],
        "summary_el": [
            "Μηχανολόγος Μηχανικός με {y} χρόνια εμπειρίας σε παραγωγικές διαδικασίες.",
            "Εμπειρία σε αυτοματισμούς, PLCs και βελτιστοποίηση παραγωγής.",
            "Αναζητώ νέες ευκαιρίες σε βιομηχανικό περιβάλλον.",
        ],
        "summary_en": [
            "Mechanical Engineer with {y} years of experience in production processes.",
            "Experience in automation, PLCs and production optimisation.",
            "Seeking new opportunities in an industrial environment.",
        ],
    },
    "accounting": {
        "label": "accounting / finance",
        "ladder_el": ["Λογιστής", "Senior Λογιστής", "Υπεύθυνος Λογιστηρίου",
                      "Οικονομικός Διευθυντής"],
        "ladder_en": ["Accountant", "Senior Accountant", "Accounting Manager",
                      "Finance Manager"],
        "companies": [
            ("DELOITTE ΕΛΛΑΣ", "DELOITTE GREECE"), ("PWC ΕΛΛΑΣ", "PWC GREECE"),
            ("EY ΕΛΛΑΣ", "EY GREECE"), ("KPMG ΕΛΛΑΣ", "KPMG GREECE"),
            ("GRANT THORNTON", "GRANT THORNTON"), ("ΛΟΓΙΣΤΙΚΟ ΓΡΑΦΕΙΟ ΘΕΣΣΑΛΟΝΙΚΗΣ", "ACCOUNTING OFFICE THESSALONIKI"),
            ("ΠΛΑΙΣΙΟ Α.Ε.", "PLAISIO S.A."), ("ΣΑΡΑΝΤΗΣ Α.Ε.", "SARANTIS S.A."),
        ],
        "bullets_el": [
            "Τήρηση λογιστικών βιβλίων και έκδοση τιμολογίων",
            "Σύνταξη οικονομικών καταστάσεων",
            "Διαχείριση φορολογικών δηλώσεων",
            "Συμφωνίες τραπεζικών λογαριασμών",
            "Μισθοδοσία και διαχείριση προσωπικού",
            "Συνεργασία με ελεγκτές και φορολογικές αρχές",
            "Προϋπολογισμός και ανάλυση κόστους",
            "Χρήση λογιστικών προγραμμάτων (SoftOne, Epsilon)",
        ],
        "bullets_en": [
            "Maintaining accounting books and issuing invoices",
            "Preparing financial statements",
            "Managing tax returns",
            "Bank reconciliations",
            "Payroll and HR administration",
            "Working with auditors and tax authorities",
            "Budgeting and cost analysis",
            "Using accounting software (SoftOne, Epsilon)",
        ],
        "degrees_el": [
            "Πτυχίο Λογιστικής και Χρηματοοικονομικής, ΤΕΙ",
            "Πτυχίο Οικονομικών Επιστημών, ΑΠΘ",
            "Πτυχίο Διοίκησης Επιχειρήσεων, ΠΑΜΑΚ",
            "Πτυχίο Λογιστικής, Οικονομικό Πανεπιστήμιο Αθηνών",
        ],
        "degrees_en": [
            "BSc Accounting and Finance, TEI",
            "BSc Economics, Aristotle University of Thessaloniki",
            "BSc Business Administration, University of Macedonia",
            "BSc Accounting, Athens University of Economics and Business",
        ],
        "skills_el": ["SoftOne", "Epsilon", "Excel", "Φορολογική νομοθεσία", "Μισθοδοσία",
                      "IFRS", "SAP"],
        "skills_en": ["SoftOne", "Epsilon", "Excel", "Tax legislation", "Payroll",
                      "IFRS", "SAP"],
        "summary_el": [
            "Λογιστής με {y} χρόνια εμπειρίας σε λογιστήριο και οικονομικές υπηρεσίες.",
            "Εξειδίκευση σε φορολογικά θέματα και οικονομικές καταστάσεις.",
            "Αναζητώ θέση σε οργανωμένο λογιστήριο.",
        ],
        "summary_en": [
            "Accountant with {y} years of experience in accounting and finance.",
            "Specialised in tax matters and financial statements.",
            "Seeking a role in an organised accounting department.",
        ],
    },
    "hospitality": {
        "label": "hospitality / retail",
        "ladder_el": ["Υπάλληλος Καταστήματος", "Ταμίας", "Υπεύθυνος Καταστήματος",
                      "Store Manager"],
        "ladder_en": ["Store Assistant", "Cashier", "Store Supervisor", "Store Manager"],
        "companies": [
            ("SKL AVENITIS", "SKLAVENITIS"), ("LIDL ΕΛΛΑΣ", "LIDL GREECE"),
            ("AB ΒΑΣΙΛΟΠΟΥΛΟΣ", "AB VASILOPOULOS"), ("ΜΑΣΟΥΤΗΣ", "MASOUTIS"),
            ("ΞΕΝΟΔΟΧΕΙΟ ΘΕΣΣΑΛΟΝΙΚΗ", "HOTEL THESSALONIKI"), ("ΓΡΗΓΟΡΗΣ", "GRIGORIS"),
            ("EVEREST", "EVEREST"), ("GOODY'S", "GOODY'S"),
        ],
        "bullets_el": [
            "Εξυπηρέτηση πελατών και διαχείριση ταμείου",
            "Διαχείριση φρέσκων προϊόντων και έλεγχος ημερομηνιών λήξης",
            "Οργάνωση καταστήματος και διαχείριση αποθέματος",
            "Εκπαίδευση νέου προσωπικού",
            "Τήρηση κανόνων υγιεινής και ασφάλειας",
            "Διαχείριση παραγγελιών και προμηθευτών",
            "Επίτευξη στόχων πωλήσεων",
            "Διαχείριση βάρδιας και προγράμματος προσωπικού",
        ],
        "bullets_en": [
            "Customer service and cash management",
            "Managing fresh products and checking expiry dates",
            "Store organisation and inventory management",
            "Training new staff",
            "Enforcing hygiene and safety rules",
            "Managing orders and suppliers",
            "Meeting sales targets",
            "Managing shifts and staff schedules",
        ],
        "degrees_el": [
            "Πτυχίο Τουριστικών Επαγγελμάτων, ΤΕΙ",
            "Πτυχίο Διοίκησης Επιχειρήσεων, ΠΑΜΑΚ",
            "Απολυτήριο Λυκείου",
            "Πτυχίο Οικονομικών Επιστημών, ΑΠΘ",
        ],
        "degrees_en": [
            "BSc Tourism Management, TEI",
            "BSc Business Administration, University of Macedonia",
            "High School Diploma",
            "BSc Economics, Aristotle University of Thessaloniki",
        ],
        "skills_el": ["Εξυπηρέτηση πελατών", "Διαχείριση ταμείου", "Διαχείριση αποθέματος",
                      "HACCP", "Οργάνωση", "Ομαδική εργασία"],
        "skills_en": ["Customer service", "Cash management", "Inventory management",
                      "HACCP", "Organisation", "Teamwork"],
        "summary_el": [
            "Επαγγελματίας λιανικής με {y} χρόνια εμπειρίας σε καταστήματα τροφίμων.",
            "Εμπειρία στη διαχείριση καταστήματος και ομάδων.",
            "Αναζητώ θέση με μεγαλύτερες ευθύνες.",
        ],
        "summary_en": [
            "Retail professional with {y} years of experience in food retail.",
            "Experience managing stores and teams.",
            "Seeking a role with more responsibility.",
        ],
    },
}

# generic bullets usable across sectors
GENERIC_BULLETS_EL = [
    "Συνεργασία με άλλα τμήματα για την επίτευξη στόχων",
    "Τήρηση διαδικασιών και τεκμηρίωση εργασιών",
    "Συμμετοχή σε εβδομαδιαίες συναντήσεις ομάδας",
    "Αναφορά αποτελεσμάτων στον προϊστάμενο",
    "Εκπαίδευση νέων συναδέλφων",
]
GENERIC_BULLETS_EN = [
    "Collaborating with other departments to meet targets",
    "Following procedures and documenting work",
    "Attending weekly team meetings",
    "Reporting results to the line manager",
    "Training new colleagues",
]

UNIVERSITIES_EL = [
    "Αριστοτέλειο Πανεπιστήμιο Θεσσαλονίκης", "Εθνικό Μετσόβιο Πολυτεχνείο",
    "Γεωπονικό Πανεπιστήμιο Αθηνών", "Πανεπιστήμιο Πατρών",
    "Πανεπιστήμιο Μακεδονίας", "Οικονομικό Πανεπιστήμιο Αθηνών",
    "Εθνικό και Καποδιστριακό Πανεπιστήμιο Αθηνών", "ΤΕΙ Θεσσαλονίκης",
]
UNIVERSITIES_EN = [
    "Aristotle University of Thessaloniki", "National Technical University of Athens",
    "Agricultural University of Athens", "University of Patras",
    "University of Macedonia", "Athens University of Economics and Business",
    "National and Kapodistrian University of Athens", "TEI of Thessaloniki",
]

CERTIFICATIONS_EL = [
    "Πιστοποιητικό Εκπαίδευσης HACCP", "ISO 22000 Internal Auditor",
    "ISO 9001 Internal Auditor", "ECDL", "Άδεια Οδήγησης Β' Κατηγορίας",
    "ServiceNow Fundamentals", "Google Analytics Certification",
    "Food Safety Level 2", "BRC Internal Auditor",
]
CERTIFICATIONS_EN = [
    "HACCP Training Certificate", "ISO 22000 Internal Auditor",
    "ISO 9001 Internal Auditor", "ECDL", "Driving Licence (Category B)",
    "ServiceNow Fundamentals", "Google Analytics Certification",
    "Food Safety Level 2", "BRC Internal Auditor",
]

LANGUAGES_EL = [
    "Αγγλικά (C1)", "Αγγλικά (C2)", "Γερμανικά (B1)", "Γερμανικά (B2)",
    "Γαλλικά (B1)", "Ιταλικά (A2)",
]
LANGUAGES_EN = [
    "Greek (native)", "English (C1)", "English (C2)", "German (B1)",
    "German (B2)", "French (B1)", "Italian (A2)",
]

# ---------------------------------------------------------------------------
# Per-block planning. Each block of 20 CVs is assigned a fixed mix of sectors,
# career shapes, genders, languages, age-evidence kinds, military statuses,
# experience buckets and degradation flags, then shuffled deterministically.
# ---------------------------------------------------------------------------
BLOCK_SECTORS = (
    ["food_qa"] * 5 + ["food_rnd"] * 3 + ["food_production"] * 3
    + ["it"] * 2 + ["marketing"] * 2 + ["mechanical"] * 2 + ["accounting"] * 2
    + ["hospitality"] * 1
)  # 20; food = 11/20
BLOCK_SHAPES = (
    ["steady_growth"] * 6 + ["lateral_moves"] * 5 + ["job_hopping"] * 4
    + ["unclear_timeline"] * 3 + ["messy"] * 2
)  # 20
BLOCK_GENDERS = ["f"] * 8 + ["m"] * 12  # 20
BLOCK_LANGS = ["el"] * 12 + ["en"] * 8  # 20
BLOCK_AGE_EVIDENCE = (
    ["stated"] * 10 + ["inferred"] * 7 + ["none"] * 3
)  # 20
BLOCK_MILITARY_M = (
    ["completed"] * 6 + ["pending"] * 2 + ["exempted"] * 1 + ["not_stated"] * 3
)  # 12, for male slots
BLOCK_EXP = (
    ["0-1"] * 3 + ["2-4"] * 4 + ["5-9"] * 7 + ["10-20"] * 6
)  # 20
BLOCK_DEGRADED = ["degraded"] * 7 + ["clean"] * 13  # 20
# force exactly 3 messy CVs per 40 (indices 3, 17, 29 mod 40)
MESSY_INDICES = {3, 17, 29}


def plan_block(seed: int, block: int) -> dict:
    rng = random.Random(seed * 1_000_003 + block * 7919)
    sectors = list(BLOCK_SECTORS)
    rng.shuffle(sectors)
    shapes = list(BLOCK_SHAPES)
    rng.shuffle(shapes)
    genders = list(BLOCK_GENDERS)
    rng.shuffle(genders)
    langs = list(BLOCK_LANGS)
    rng.shuffle(langs)
    age_ev = list(BLOCK_AGE_EVIDENCE)
    rng.shuffle(age_ev)
    mil_m = list(BLOCK_MILITARY_M)
    rng.shuffle(mil_m)
    exp = list(BLOCK_EXP)
    rng.shuffle(exp)
    deg = list(BLOCK_DEGRADED)
    rng.shuffle(deg)
    return {
        "sector": sectors, "shape": shapes, "gender": genders, "lang": langs,
        "age_evidence": age_ev, "military_m": mil_m, "exp": exp, "degraded": deg,
    }


def _force_messy(plan: dict, index: int) -> None:
    """Guarantee a messy CV at the fixed indices, swapping to keep counts."""
    if index % 40 not in MESSY_INDICES:
        return
    block, pos = index // BLOCK, index % BLOCK
    if plan["shape"][pos] == "messy":
        return
    # find a messy slot in this block that is not itself a forced index
    for j in range(BLOCK):
        if plan["shape"][j] == "messy" and (block * BLOCK + j) % 40 not in MESSY_INDICES:
            plan["shape"][pos], plan["shape"][j] = plan["shape"][j], plan["shape"][pos]
            return


# ---------------------------------------------------------------------------
# Date helpers (no third-party dateutil).
# ---------------------------------------------------------------------------
def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date(y, m, day)


def fmt_my(d: date) -> str:
    return f"{d.month:02d}/{d.year}"


def fmt_my_en(d: date) -> str:
    return f"{d.month:02d}/{d.year}"


# ---------------------------------------------------------------------------
# Record builder.
# ---------------------------------------------------------------------------
def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "cv"


def _pick(rng, items):
    return items[rng.randrange(len(items))]


def _sample(rng, items, n):
    return rng.sample(items, min(n, len(items)))


def _email(first_lat, last_lat, rng):
    dom = _pick(rng, ["gmail.com", "yahoo.gr", "outlook.com", "hotmail.com", "email.gr"])
    return f"{_slug(first_lat)}.{_slug(last_lat)}@{dom}"


def _phone(rng):
    return f"+30 69{rng.randint(0, 9)} {rng.randint(100, 999)} {rng.randint(1000, 9999)}"


def _make_jobs(rng, sector, shape, years, lang, today):
    """Return a list of job dicts for the given career shape."""
    sec = SECTORS[sector]
    ladder = sec["ladder_el"] if lang == "el" else sec["ladder_en"]
    companies = sec["companies"]
    bullets = sec["bullets_el"] if lang == "el" else sec["bullets_en"]
    generic = GENERIC_BULLETS_EL if lang == "el" else GENERIC_BULLETS_EN
    present = "Σήμερα" if lang == "el" else "Present"

    def job(title, company, start, end, date_str=None, bullets_extra=None):
        b = _sample(rng, bullets, rng.randint(2, 4)) + _sample(rng, generic, rng.randint(0, 2))
        if bullets_extra:
            b = b + bullets_extra
        return {
            "title": title, "company": company, "start": start, "end": end,
            "date_str": date_str, "bullets": b,
        }

    def date_str(start, end):
        if start is None and end is None:
            return "(χωρίς ημερομηνίες)" if lang == "el" else "(no dates given)"
        if start is None:
            return f"– {present}"
        if end is None:
            return f"{fmt_my(start)} – {present}"
        return f"{fmt_my(start)} – {fmt_my(end)}"

    jobs = []
    if shape == "steady_growth":
        # one employer, 2-3 promotions; optionally a prior short role elsewhere
        comp = _pick(rng, companies)
        end = add_months(today, -rng.randint(0, 14))
        start = add_months(end, -years * 12 - rng.randint(0, 11))
        n_roles = 2 if years < 6 else 3
        seg = (years * 12) // n_roles
        for k in range(n_roles):
            s = add_months(start, k * seg)
            e = add_months(start, (k + 1) * seg) if k < n_roles - 1 else end
            lvl = min(k, len(ladder) - 1)
            jobs.append(job(ladder[lvl], comp, s, e))
        if years >= 4 and rng.random() < 0.5:
            prev = _pick(rng, companies)
            ps = add_months(start, -rng.randint(6, 14))
            pe = add_months(start, -1)
            jobs.insert(0, job(ladder[0], prev, ps, pe))
    elif shape == "lateral_moves":
        n = min(4, 2 + years // 3)
        end = add_months(today, -rng.randint(0, 14))
        start = add_months(end, -years * 12 - rng.randint(0, 11))
        span = (years * 12) // n
        for k in range(n):
            s = add_months(start, k * span)
            e = add_months(start, (k + 1) * span) if k < n - 1 else end
            lvl = rng.randint(1, min(2, len(ladder) - 1))
            jobs.append(job(ladder[lvl], _pick(rng, companies), s, e))
    elif shape == "job_hopping":
        # 4-6 employers inside the last ~3 years
        n = rng.randint(4, 6)
        end = add_months(today, -rng.randint(0, 6))
        start = add_months(end, -rng.randint(30, 38))
        span = (end.toordinal() - start.toordinal()) // n
        for k in range(n):
            s = add_months(start, k * span // 30)
            e = add_months(start, (k + 1) * span // 30) if k < n - 1 else end
            lvl = rng.randint(0, min(1, len(ladder) - 1))
            jobs.append(job(ladder[lvl], _pick(rng, companies), s, e))
    elif shape == "unclear_timeline":
        # mixed date quality: some year-only, one undated, one present
        n = rng.randint(3, 4)
        end = add_months(today, -rng.randint(0, 10))
        start = add_months(end, -years * 12 - rng.randint(0, 11))
        span = (years * 12) // n
        for k in range(n):
            s = add_months(start, k * span)
            e = add_months(start, (k + 1) * span) if k < n - 1 else end
            lvl = rng.randint(0, min(2, len(ladder) - 1))
            ds = None
            if k == 0:
                ds = f"{s.year} – {e.year}"  # year-only
            elif k == n - 1:
                ds = f"{fmt_my(s)} – {present}"
            elif k == 1:
                ds = "(χωρίς ημερομηνίες)" if lang == "el" else "(no dates given)"
            else:
                ds = f"{fmt_my(s)} – {fmt_my(e)}"
            jobs.append(job(ladder[lvl], _pick(rng, companies), s, e, date_str=ds))
    elif shape == "messy":
        # deliberately contradictory: overlapping full-time roles, a missing
        # year, and unusable dates
        comp_a, comp_b = _pick(rng, companies), _pick(rng, companies)
        end = add_months(today, -rng.randint(0, 8))
        # role A spans 2019-2023, role B overlaps 2020-2022 (both full-time)
        a_s, a_e = date(2019, 3, 1), date(2023, 6, 1)
        b_s, b_e = date(2020, 9, 1), date(2022, 4, 1)
        jobs.append(job(ladder[1], comp_a, a_s, a_e))
        jobs.append(job(ladder[1], comp_b, b_s, b_e))
        # a gap: nothing between 2023 and 2025, then a role with unusable dates
        jobs.append(job(ladder[2], _pick(rng, companies), date(2025, 1, 1), end,
                        date_str="Μάρτιος ?? – Σήμερα" if lang == "el" else "March ?? – Present"))
        # a role with a nonsense year range
        jobs.append(job(ladder[0], _pick(rng, companies), date(2016, 1, 1), date(2018, 1, 1),
                        date_str="20XX – 20XX"))
    return jobs


def _make_record(index, seed, today):
    block, pos = index // BLOCK, index % BLOCK
    plan = plan_block(seed, block)
    _force_messy(plan, index)
    rng = random.Random(seed * 1_000_003 + index * 104_729 + 5)

    lang = plan["lang"][pos]
    sector = plan["sector"][pos]
    shape = plan["shape"][pos]
    gender = plan["gender"][pos]
    age_ev = plan["age_evidence"][pos]
    degraded = plan["degraded"][pos] == "degraded"

    # experience years
    bucket = plan["exp"][pos]
    if shape == "job_hopping":
        years = rng.randint(2, 4)
    elif bucket == "0-1":
        years = rng.choice([0, 0, 1])
    elif bucket == "2-4":
        years = rng.randint(2, 4)
    elif bucket == "5-9":
        years = rng.randint(5, 9)
    else:
        years = rng.randint(10, 20)

    # age: consistent with years; career changers get a larger slack
    if years == 0:
        slack = rng.choice([0, 1, 2, 3, 5, 8, 12, 17])
    else:
        slack = rng.choice([0, 0, 1, 1, 2, 3, 4, 6, 9])
    age = 21 + years + slack
    age = min(age, 58)

    # names
    if sector in ("it", "marketing") and rng.random() < 0.25:
        first_g, first_l, g = _pick(rng, INTERNATIONAL_NAMES)
        gender = g  # keep gender consistent with the chosen name
    else:
        first_g, first_l, g = _pick(rng, GREEK_NAMES)
        if g != gender:
            # pick a name matching the planned gender
            pool = [n for n in GREEK_NAMES if n[2] == gender]
            first_g, first_l, g = _pick(rng, pool)
    last_g, last_l = _pick(rng, GREEK_SURNAMES)
    city_g, city_l = _pick(rng, CITIES)

    first = first_g if lang == "el" else first_l
    last = last_g if lang == "el" else last_l
    city = city_g if lang == "el" else city_l

    # military: females -> not applicable; males take the per-block male plan
    male_ordinal = sum(1 for g in plan["gender"][:pos] if g == "m")
    military = "female_na" if gender == "f" else plan["military_m"][male_ordinal]

    sec = SECTORS[sector]
    title = _pick(rng, sec["ladder_el"][1:]) if lang == "el" else _pick(rng, sec["ladder_en"][1:])

    jobs = _make_jobs(rng, sector, shape, years, lang, today)

    # education
    degree = _pick(rng, sec["degrees_el"]) if lang == "el" else _pick(rng, sec["degrees_en"])
    uni = _pick(rng, UNIVERSITIES_EL) if lang == "el" else _pick(rng, UNIVERSITIES_EN)
    grad_year = today.year - age + 22  # ~22 at graduation
    edu_years = f"{grad_year - 4} – {grad_year}"

    # summary
    summary_tpl = sec["summary_el"] if lang == "el" else sec["summary_en"]
    summary = " ".join(t.replace("{y}", str(years)) for t in summary_tpl)

    # skills / certs / languages
    skills = _sample(rng, sec["skills_el"] if lang == "el" else sec["skills_en"], rng.randint(5, 8))
    certs = _sample(rng, CERTIFICATIONS_EL if lang == "el" else CERTIFICATIONS_EN, rng.randint(2, 4))
    langs = _sample(rng, LANGUAGES_EL if lang == "el" else LANGUAGES_EN, rng.randint(2, 4))

    return {
        "index": index, "lang": lang, "sector": sector, "shape": shape,
        "gender": gender, "age_evidence": age_ev, "military": military,
        "degraded": degraded, "years": years, "age": age,
        "first": first, "last": last, "city": city, "title": title,
        "first_latin": first_l, "last_latin": last_l,
        "email": _email(first_l, last_l, rng), "phone": _phone(rng),
        "jobs": jobs, "degree": degree, "uni": uni, "edu_years": edu_years,
        "summary": summary, "skills": skills, "certs": certs, "langs": langs,
        "birthdate": None, "military_line": None,
    }


# ---------------------------------------------------------------------------
# Text rendering -> list of (text, kind) lines.
# ---------------------------------------------------------------------------
def _wrap(text, width=92):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


def _render_lines(rec, today):
    el = rec["lang"] == "el"
    present = "Σήμερα" if el else "Present"
    lines = [("SYNTHETIC SAMPLE CV - not a real person", "banner")]
    lines.append((f"{rec['first']} {rec['last']}", "name"))
    lines.append((rec["title"], "title"))
    lines.append((f"{rec['email']} | {rec['phone']} | {rec['city']}, Ελλάδα" if el
                  else f"{rec['email']} | {rec['phone']} | {rec['city']}, Greece", "contact"))

    # header extras: birth date / military (varied placement)
    header_extra = []
    if rec["age_evidence"] == "stated":
        bd = _birthdate(rec, today)
        header_extra.append(f"Ημερομηνία γέννησης: {bd.day:02d}/{bd.month:02d}/{bd.year}" if el
                            else f"Date of birth: {bd.day:02d}/{bd.month:02d}/{bd.year}")
    if rec["military"] == "completed":
        header_extra.append(f"Στρατιωτική θητεία: Εκπληρωθείσα ({rec['age'] - 24 + 2000})" if el
                            else f"Military service: Completed ({rec['age'] - 24 + 2000})")
    elif rec["military"] == "pending":
        header_extra.append("Στρατιωτική θητεία: Εκκρεμεί (αναβολή)" if el
                            else "Military service: Pending (deferment)")
    elif rec["military"] == "exempted":
        header_extra.append("Στρατιωτική θητεία: Απαλλαγή (Ι5)" if el
                            else "Military service: Exempted (medical)")
    if header_extra:
        lines.append((" | ".join(header_extra), "contact"))

    lines.append(("", "spacer"))
    lines.append(("ΕΠΑΓΓΕΛΜΑΤΙΚΟ ΠΡΟΦΙΛ" if el else "PROFESSIONAL SUMMARY", "section"))
    for w in _wrap(rec["summary"]):
        lines.append((w, "body"))
    lines.append(("", "spacer"))

    lines.append(("ΕΚΠΑΙΔΕΥΣΗ" if el else "EDUCATION", "section"))
    lines.append((rec["degree"], "body"))
    lines.append((f"{rec['uni']} | {rec['edu_years']}" if rec["age_evidence"] != "none"
                  else rec["uni"], "body"))
    if rec["age_evidence"] == "inferred":
        lines.append((f"Απολυτήριο Λυκείου ({rec['age'] - 18 + 2000})" if el
                      else f"High School Diploma ({rec['age'] - 18 + 2000})", "body"))
    lines.append(("", "spacer"))

    lines.append(("ΕΠΑΓΓΕΛΜΑΤΙΚΗ ΕΜΠΕΙΡΙΑ" if el else "PROFESSIONAL EXPERIENCE", "section"))
    for j in rec["jobs"]:
        ds = j["date_str"] or (f"{fmt_my(j['start'])} – {present}" if j["end"] is None
                               else f"{fmt_my(j['start'])} – {fmt_my(j['end'])}")
        lines.append((j["title"], "jobtitle"))
        lines.append((f"{j['company']} | {ds}", "jobmeta"))
        for b in j["bullets"]:
            lines.append(("• " + b, "bullet"))
    lines.append(("", "spacer"))

    lines.append(("ΔΕΞΙΟΤΗΤΕΣ" if el else "SKILLS", "section"))
    lines.append((", ".join(rec["skills"]), "body"))
    lines.append(("", "spacer"))

    lines.append(("ΠΙΣΤΟΠΟΙΗΣΕΙΣ" if el else "CERTIFICATIONS", "section"))
    lines.append((", ".join(rec["certs"]), "body"))
    lines.append(("", "spacer"))

    lines.append(("ΞΕΝΕΣ ΓΛΩΣΣΕΣ" if el else "LANGUAGES", "section"))
    lines.append((", ".join(rec["langs"]), "body"))

    if rec["military"] in ("completed", "pending", "exempted") and rec["age_evidence"] != "stated":
        # military already in header for stated; add a section line otherwise
        pass
    lines.append(("", "spacer"))
    lines.append(("ΣΥΣΤΑΣΕΙΣ" if el else "REFERENCES", "section"))
    lines.append(("Διαθέσιμες κατόπιν αιτήματος." if el else "Available upon request.", "body"))

    if rec["degraded"]:
        lines = [(degrade(t), k) for t, k in lines]
    return lines


def _birthdate(rec, today):
    # deterministic pseudo-random month/day derived from the record index
    rng = random.Random(rec["index"] * 31 + 7)
    m = rng.randint(1, 12)
    d = rng.randint(1, 28)
    return date(today.year - rec["age"], m, d)


# ---------------------------------------------------------------------------
# PDF writing.
# ---------------------------------------------------------------------------
def _write_pdf(path, lines, body_font, bold_font):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_font(fontname="body", fontfile=body_font)
    page.insert_font(fontname="bold", fontfile=bold_font)
    x = 56
    y = 70
    bottom = 800
    style = {
        "banner": (8.5, "bold", (0.45, 0.45, 0.45)),
        "name": (16, "bold", (0.0, 0.0, 0.0)),
        "title": (11, "bold", (0.15, 0.15, 0.15)),
        "contact": (9.5, "body", (0.2, 0.2, 0.2)),
        "section": (11.5, "bold", (0.0, 0.0, 0.0)),
        "jobtitle": (10.5, "bold", (0.0, 0.0, 0.0)),
        "jobmeta": (9.5, "body", (0.25, 0.25, 0.25)),
        "bullet": (10, "body", (0.0, 0.0, 0.0)),
        "body": (10, "body", (0.0, 0.0, 0.0)),
        "spacer": (6, "body", (0.0, 0.0, 0.0)),
    }
    for text, kind in lines:
        size, weight, color = style[kind]
        fontname = "bold" if weight == "bold" else "body"
        if kind == "spacer":
            y += size
            continue
        if y + size > bottom:
            page = doc.new_page(width=595, height=842)
            page.insert_font(fontname="body", fontfile=body_font)
            page.insert_font(fontname="bold", fontfile=bold_font)
            y = 70
        page.insert_text((x, y), text, fontname=fontname, fontsize=size, color=color)
        y += size + (3.5 if kind in ("name", "section", "jobtitle") else 2.0)
    doc.set_metadata({"title": f"{lines[1][0]} - CV", "author": "synthetic generator",
                      "creator": "make-sample-cvs.py"})
    doc.subset_fonts()
    doc.save(path, deflate=True, garbage=3)
    return doc.page_count


# ---------------------------------------------------------------------------
# Manifest description (content facts only, no model answers / labels).
# ---------------------------------------------------------------------------
def _profile(rec):
    sec = SECTORS[rec["sector"]]["label"]
    lang = "Greek" if rec["lang"] == "el" else "English"
    shape_desc = {
        "steady_growth": "steady growth at one employer",
        "lateral_moves": "lateral moves across employers",
        "job_hopping": "job hopping (many short roles)",
        "unclear_timeline": "unclear/partial dates",
        "messy": "internally inconsistent dates",
    }[rec["shape"]]
    n_emp = len({j["company"] for j in rec["jobs"]})
    parts = [f"{lang}-language CV", f"{sec}", f"{rec['years']} yrs experience",
             f"{n_emp} employers", shape_desc]
    if rec["age_evidence"] == "stated":
        parts.append("birth date stated")
    elif rec["age_evidence"] == "inferred":
        parts.append("age inferable from dates")
    else:
        parts.append("no age evidence")
    if rec["military"] == "female_na":
        parts.append("female")
    elif rec["military"] != "not_stated":
        parts.append(f"military {rec['military']}")
    if rec["degraded"]:
        parts.append("degraded text layer")
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate a deterministic corpus of synthetic sample CVs.")
    ap.add_argument("--count", type=int, default=40, help="number of CVs (default 40)")
    ap.add_argument("--out", default="fixtures/sample-cvs", help="output directory")
    ap.add_argument("--seed", type=int, default=7, help="random seed (default 7)")
    ap.add_argument("--clean", action="store_true", help="wipe the output directory first")
    ap.add_argument("--today", default=REFERENCE_TODAY.isoformat(),
                    help="reference date YYYY-MM-DD (default fixed 2026-09-17)")
    args = ap.parse_args(argv)

    today = date.fromisoformat(args.today)
    out = os.path.abspath(args.out)
    if args.clean and os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)

    body_font = pick_font(FONT_BODY_CANDIDATES)
    bold_font = pick_font(FONT_BOLD_CANDIDATES)
    print(f"fonts: body={body_font} bold={bold_font}", file=sys.stderr)

    manifest = {
        "generator": "scripts/make-sample-cvs.py",
        "generator_version": GENERATOR_VERSION,
        "seed": args.seed,
        "count": args.count,
        "reference_date": today.isoformat(),
        "files": [],
    }
    for i in range(args.count):
        rec = _make_record(i, args.seed, today)
        # Latin forms, because _slug strips anything outside [A-Za-z0-9] and Greek letters
        # are not transliterated by NFKD: a Greek name would otherwise collapse to "cv"
        # and every Greek CV would overwrite the last one.
        base = f"{_slug(rec['last_latin'])}_{_slug(rec['first_latin'])}"
        fname = f"{base}_CV.pdf"
        n = 1
        while os.path.exists(os.path.join(out, fname)):
            n += 1
            fname = f"{base}_{n}_CV.pdf"
        path = os.path.join(out, fname)
        pages = _write_pdf(path, _render_lines(rec, today), body_font, bold_font)
        manifest["files"].append({
            "file": fname, "pages": pages, "language": rec["lang"],
            "profile": _profile(rec),
        })
        if (i + 1) % 50 == 0 or i == args.count - 1:
            print(f"wrote {i + 1}/{args.count}", file=sys.stderr)

    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print(f"done: {args.count} CVs -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
