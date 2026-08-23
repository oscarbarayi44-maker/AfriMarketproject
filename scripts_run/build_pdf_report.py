"""Génère docs/AfriMarket_Rapport_Strategique.pdf — rapport professionnel
suivant la charte graphique AfriMarket (reportlab, contrôle total du design)."""
import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from afrimarket import branding  # noqa: E402

FIGS = PROJECT_ROOT / "figures_brand"
OUT = PROJECT_ROOT / "docs" / "AfriMarket_Rapport_Strategique.pdf"
RESULTS = json.loads((PROJECT_ROOT / "docs" / "resultats_analyses.json").read_text(encoding="utf-8"))
AUDIT = json.loads((PROJECT_ROOT / "docs" / "audit_report.json").read_text(encoding="utf-8"))

DARK_GREEN = colors.HexColor(branding.DARK_GREEN)
BRAND_GREEN = colors.HexColor(branding.BRAND_GREEN)
LIGHT_GREEN = colors.HexColor(branding.LIGHT_GREEN)
PALE_GREEN = colors.HexColor(branding.PALE_GREEN)
WHITE = colors.white
TEXT_DARK = colors.HexColor(branding.TEXT_DARK)
GREY = colors.HexColor(branding.GREY)

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

c = canvas.Canvas(str(OUT), pagesize=A4)
page_no = 0
current_chapter = None


def new_page(chapter=None):
    global page_no, current_chapter
    if page_no > 0:
        footer(current_chapter)
        c.showPage()
    page_no += 1
    current_chapter = chapter


def footer(chapter):
    c.setFillColor(DARK_GREEN)
    c.rect(0, 0, PAGE_W, 1.0 * cm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 8)
    c.drawString(MARGIN, 0.35 * cm, "AfriMarket — Rapport stratégique confidentiel")
    c.drawRightString(PAGE_W - MARGIN, 0.35 * cm, f"Page {page_no}")
    if chapter:
        c.drawCentredString(PAGE_W / 2, 0.35 * cm, chapter)


def header_band(title, subtitle=None, height=2.6 * cm):
    c.setFillColor(DARK_GREEN)
    c.rect(0, PAGE_H - height, PAGE_W, height, fill=1, stroke=0)
    c.setFillColor(BRAND_GREEN)
    c.rect(0, PAGE_H - height - 0.08 * cm, PAGE_W, 0.08 * cm, fill=1, stroke=0)
    if branding.LOGO_PATH:
        img = ImageReader(str(branding.LOGO_PATH))
        iw, ih = img.getSize()
        logo_h = height - 0.7 * cm
        logo_w = logo_h * iw / ih
        c.drawImage(img, PAGE_W - MARGIN - logo_w, PAGE_H - height + 0.35 * cm, width=logo_w, height=logo_h, mask="auto")
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(MARGIN, PAGE_H - 1.15 * cm, title)
    if subtitle:
        c.setFont("Helvetica", 10.5)
        c.setFillColor(LIGHT_GREEN)
        c.drawString(MARGIN, PAGE_H - 1.75 * cm, subtitle)
    return PAGE_H - height - 0.6 * cm


def wrap_text(text, font, size, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if c.stringWidth(trial, font, size) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def paragraph(text, x, y, width, size=10.5, leading=14.5, color=TEXT_DARK, font="Helvetica", bold_font="Helvetica-Bold"):
    c.setFont(font, size)
    c.setFillColor(color)
    lines = wrap_text(text, font, size, width)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def section_title(text, x, y, size=13, color=DARK_GREEN):
    c.setFont("Helvetica-Bold", size)
    c.setFillColor(color)
    c.drawString(x, y, text)
    return y - size * 1.2


def bullet_list(items, x, y, width, size=10, leading=14, gap=6, color=TEXT_DARK):
    for item in items:
        c.setFillColor(BRAND_GREEN)
        c.circle(x + 2, y + 3, 1.6, fill=1, stroke=0)
        y = paragraph(item, x + 12, y, width - 12, size=size, leading=leading, color=color)
        y -= gap
    return y


def kpi_row(kpis, x, y, width, height=2.2 * cm):
    n = len(kpis)
    gap = 0.25 * cm
    card_w = (width - gap * (n - 1)) / n
    for i, (label, value) in enumerate(kpis):
        cx = x + i * (card_w + gap)
        c.setFillColor(DARK_GREEN if i == 0 else BRAND_GREEN)
        c.roundRect(cx, y - height, card_w, height, 4, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(cx + card_w / 2, y - height * 0.42, value)
        c.setFont("Helvetica", 8)
        c.drawCentredString(cx + card_w / 2, y - height * 0.75, label)
    return y - height


def fit_image(path, x, y, max_w, max_h, align="left"):
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    ratio = min(max_w / iw, max_h / ih)
    w, h = iw * ratio, ih * ratio
    if align == "center":
        x = x + (max_w - w) / 2
    c.drawImage(img, x, y - h, width=w, height=h, mask="auto")
    return h


# ============================================================== COVER PAGE ===
new_page()
c.setFillColor(DARK_GREEN)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
c.setFillColor(BRAND_GREEN)
c.rect(0, PAGE_H / 2 - 0.05 * cm, PAGE_W, 0.1 * cm, fill=1, stroke=0)

if branding.LOGO_PATH:
    img = ImageReader(str(branding.LOGO_PATH))
    iw, ih = img.getSize()
    logo_h = 4.0 * cm
    logo_w = logo_h * iw / ih
    c.drawImage(img, (PAGE_W - logo_w) / 2, PAGE_H / 2 + 0.6 * cm, width=logo_w, height=logo_h, mask="auto")
else:
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 1.5 * cm, "AfriMarket")

c.setFillColor(WHITE)
c.setFont("Helvetica-Bold", 20)
c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 1.4 * cm, "Rapport stratégique — Analyse des données commerciales")
c.setFillColor(LIGHT_GREEN)
c.setFont("Helvetica", 12)
c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 2.1 * cm, "6 mois d'activité — Résultats, enseignements clés et recommandations")
c.setFillColor(WHITE)
c.setFont("Helvetica", 10.5)
c.drawCentredString(PAGE_W / 2, 3 * cm, "Préparé pour la Direction Générale  |  Data Analyst")

# ============================================================= SOMMAIRE =====
new_page("Sommaire")
y = header_band("Sommaire")
y -= 0.6 * cm
toc = [
    "1.  Contexte et mission", "2.  Méthodologie : audit et data cleaning", "3.  Feature engineering",
    "4.  Performance globale", "5.  Analyse par catégorie", "6.  Analyse géographique",
    "7.  Analyse marketing", "8.  Analyse clients", "9.  Recommandations stratégiques",
    "10. Conclusion business orientée action",
]
for line in toc:
    c.setFont("Helvetica", 12)
    c.setFillColor(TEXT_DARK)
    c.drawString(MARGIN + 0.3 * cm, y, line)
    y -= 0.85 * cm

# ==================================================== CONTEXTE & METHODO ===
new_page("Contexte et méthodologie")
y = header_band("1. Contexte et mission")
y -= 0.3 * cm
y = paragraph(
    "AfriMarket est une entreprise e-commerce panafricaine opérant dans 4 catégories (Électronique, "
    "Mode, Beauté, Maison) sur 8 grandes villes d'Afrique francophone. La direction constatait des "
    "variations importantes de chiffre d'affaires, un taux de retour préoccupant, des dépenses "
    "marketing élevées et des écarts de performance selon les villes. Ce rapport répond à quatre "
    "questions stratégiques : quelle catégorie prioriser, où investir géographiquement, quel canal "
    "marketing renforcer ou réduire, et comment améliorer la rétention client.",
    MARGIN, y, CONTENT_W,
)
y -= 0.5 * cm
y = section_title("2. Méthodologie : audit et data cleaning", MARGIN, y)
y -= 0.2 * cm
y = paragraph(
    f"Le dataset brut ({AUDIT['n_lignes']:,} commandes) contenait des anomalies significatives : "
    f"{AUDIT['doublons_id_commande']} doublons, {AUDIT['remises_negatives']} remises négatives, "
    f"{AUDIT['prix_negatifs']} prix négatifs, {AUDIT['quantites_nulles']} quantités nulles et "
    f"{AUDIT['prix_outliers_iqr']} valeurs de prix extrêmes, ainsi que des incohérences de saisie "
    "(ville « Kinshassa » au lieu de « Kinshasa », catégorie « electronique » sans accent/majuscule, "
    "statut « retournée » en minuscule). Après nettoyage et normalisation, le dataset exploitable "
    "(df_clean) contient 9 400 commandes valides et 1 734 clients uniques.".replace(",", " "),
    MARGIN, y, CONTENT_W,
)
y -= 0.5 * cm
y = section_title("3. Feature engineering", MARGIN, y)
y -= 0.2 * cm
y = paragraph(
    "En l'absence de coût d'achat produit dans les données, une marge brute forfaitaire de 35% du "
    "chiffre d'affaires est retenue (hypothèse usuelle pour un e-commerce généraliste multi-catégories, "
    "à ajuster si un coût matière réel est communiqué). Variables créées : chiffre_affaires, "
    "marge_brute, profit_net, mois, indicateur_retour, nombre_commandes_par_client et valeur_vie_client "
    "(CLV simplifiée).",
    MARGIN, y, CONTENT_W,
)

# ===================================================== PERFORMANCE GLOBALE =
new_page("Performance globale")
y = header_band("4. Performance globale", "Vue d'ensemble sur 6 mois d'activité")
y -= 0.4 * cm
perf = RESULTS["performance_globale"]
kpis = [
    ("CA total", f"{perf['ca_total']/1e6:.2f} M$"),
    ("Profit net estimé", f"{perf['profit_net_total']/1e3:.0f} k$"),
    ("Panier moyen", f"{perf['panier_moyen']:.0f} $"),
    ("Taux d'annulation", f"{perf['taux_annulation']*100:.1f} %"),
    ("Taux de retour", f"{perf['taux_retour']*100:.1f} %"),
]
y = kpi_row(kpis, MARGIN, y, CONTENT_W)
y -= 0.7 * cm
y = paragraph(
    "Sur 6 mois, AfriMarket génère 2,51 M$ de chiffre d'affaires pour un profit net estimé de 754 k$ "
    "(≈30% de marge nette sur le CA non annulé). Le taux d'annulation reste faible (1,9%), mais le "
    "taux de retour (8,3%) constitue un point de vigilance direct sur la rentabilité (coûts de "
    "traitement, remboursement, logistique retour).",
    MARGIN, y, CONTENT_W,
)


def figure_page(chapter, title, subtitle, image_name, insight_title, insight_paragraphs, img_h=8.5 * cm):
    new_page(chapter)
    y0 = header_band(title, subtitle)
    y0 -= 0.3 * cm
    fit_image(FIGS / image_name, MARGIN, y0, CONTENT_W, img_h, align="center")
    y0 -= img_h + 0.7 * cm
    y0 = section_title(insight_title, MARGIN, y0, size=12)
    y0 -= 0.15 * cm
    for para in insight_paragraphs:
        y0 = paragraph(para, MARGIN, y0, CONTENT_W)
        y0 -= 0.35 * cm
    return y0


# ============================================================== CATEGORIE ==
figure_page(
    "Analyse par catégorie", "5. Analyse par catégorie",
    "Question stratégique : quelle catégorie doit être priorisée ou optimisée ?",
    "ca_par_categorie.png", "Constat et recommandation",
    [
        "L'Électronique porte 74,6% du CA total (1,87 M$) et 82% du profit net (615 k$) : c'est le "
        "moteur de croissance de l'entreprise, à prioriser en investissement.",
        "Mode et Beauté ont un profit quasi nul rapporté à leur marge brute théorique : les coûts de "
        "livraison et marketing absorbent respectivement 57% et 88% de leur marge (contre 6% pour "
        "l'Électronique). Leur panier moyen trop faible ne couvre pas le coût fixe par commande.",
    ],
)

figure_page(
    "Analyse par catégorie", "5. Analyse par catégorie (suite)",
    "Le revers de la médaille : le taux de retour",
    "taux_retour_categorie.png", "Constat et recommandation",
    [
        "Le taux de retour de l'Électronique atteint 14,1%, près de 2 fois la moyenne globale (8,3%). "
        "Chaque point de retour gagné se traduit directement en profit préservé sur la catégorie la "
        "plus rentable.",
        "Recommandation : fiches produits plus précises, contrôle qualité fournisseurs, politique de "
        "retour resserrée sur les motifs évitables.",
    ],
)

# ============================================================= GEOGRAPHIE ==
figure_page(
    "Analyse géographique", "6. Analyse géographique",
    "Question stratégique : où devons-nous investir davantage ?",
    "ca_par_ville.png", "Constat et recommandation",
    [
        "Kinshasa est le marché le plus performant (752 k$ de CA, 227 k$ de profit) avec un taux "
        "d'annulation quasi nul (0,26%) : marché mature, prioritaire pour renforcer l'investissement.",
        "Abidjan et Dakar combinent bon CA et annulation quasi nulle : marchés secondaires à consolider.",
    ],
)

figure_page(
    "Analyse géographique", "6. Analyse géographique (suite)",
    "Une anomalie opérationnelle à traiter en priorité",
    "taux_annulation_ville.png", "Alerte et recommandation",
    [
        "Douala présente une anomalie opérationnelle majeure : un taux d'annulation de 12,9%, contre "
        "moins de 1% dans toutes les autres villes.",
        "Recommandation : auditer la cause racine (méthode de paiement locale, rupture de stock, "
        "fiabilité du livreur partenaire) avant tout investissement marketing supplémentaire.",
    ],
)

# ============================================================== MARKETING ==
figure_page(
    "Analyse marketing", "7. Analyse marketing",
    "Question stratégique : quel canal mérite plus de budget ? Lequel réduire ?",
    "roi_par_canal.png", "ROI = (Revenus − Coût marketing) / Coût marketing",
    [
        "Email affiche un ROI de 230 pour un budget marginal (2 297 $, le plus faible des 4 canaux) : "
        "un canal nettement sous-financé au regard de son efficacité.",
        "Google Ads (ROI 50) reste solide et scalable. Influenceur cumule le pire ROI (21,5) pour un "
        "budget de 16 k$ : c'est le canal à réduire ou réattribuer en priorité vers Email et Google Ads.",
    ],
)

figure_page(
    "Analyse marketing", "7. Analyse marketing (suite)",
    "La rétention client par canal, en complément du ROI",
    "retention_par_canal.png", "Constat et recommandation",
    [
        "Instagram Ads génère le plus de CA (950 k$) et la meilleure rétention (54%), malgré un ROI "
        "plus modéré (25) lié à son budget élevé (37 k$) : canal à conserver pour le volume et la "
        "fidélisation, à optimiser plutôt qu'à augmenter en budget brut.",
        "Influenceur a aussi la pire rétention (42%), confirmant qu'il doit être réduit en priorité.",
    ],
)

# ================================================================ CLIENTS ==
figure_page(
    "Analyse clients", "8. Analyse clients",
    "Question stratégique : comment améliorer la rétention ?",
    "pareto_clients.png", "Constat",
    [
        "La base compte 1 734 clients, dont 73,2% sont récurrents (≥2 commandes) : un socle de "
        "fidélité globalement sain. L'analyse Pareto montre que 31,9% des clients génèrent 80% du CA "
        "— une concentration modérée, plutôt rassurante par rapport à un Pareto classique (20/80).",
    ],
)

figure_page(
    "Analyse clients", "8. Analyse clients (suite)",
    "Segmentation par valeur vie client (quartiles)",
    "segmentation_clients.png", "Constat et recommandation",
    [
        "Le segment Platine (25% des clients) génère 72% du CA total (1,81 M$), contre 1,4% pour le "
        "segment Bronze : une forte polarisation de la valeur client.",
        "Recommandation : programme VIP pour Platine (sécuriser le cœur du revenu), offres "
        "d'activation pour Bronze/Argent (867 clients, 7,8% du CA) pour les faire monter en gamme.",
    ],
    img_h=8.0 * cm,
)

# ========================================================= RECOMMANDATIONS =
new_page("Recommandations stratégiques")
y = header_band("9. Recommandations stratégiques", "5 actions prioritaires pour la direction")
y -= 0.5 * cm
recos = [
    ("1", "Prioriser l'Électronique tout en réduisant son taux de retour",
     "74,6% du CA et 82% du profit ; fiches produits plus précises, contrôle qualité fournisseurs, "
     "politique de retour resserrée."),
    ("2", "Revoir l'économie unitaire de Mode et Beauté",
     "Coûts logistiques/marketing consommant 57% et 88% de leur marge ; seuil de livraison gratuite, "
     "bundles produits, renégociation des frais de livraison."),
    ("3", "Auditer en urgence l'anomalie opérationnelle de Douala",
     "12,9% d'annulation vs <1% ailleurs ; vérifier paiement local, rupture de stock, fiabilité du "
     "livreur partenaire avant d'investir davantage."),
    ("4", "Réallouer le budget marketing vers l'efficacité",
     "Renforcer Email (ROI 230) et Google Ads (ROI 50) ; réduire Influenceur (ROI 21,5, pire "
     "rétention)."),
    ("5", "Structurer un programme de fidélisation différencié par segment",
     "VIP pour Platine (72% du CA) ; offres d'activation pour Bronze/Argent (867 clients, 7,8% du CA)."),
]
for num, title, desc in recos:
    c.setFillColor(DARK_GREEN)
    c.roundRect(MARGIN, y - 0.85 * cm, 0.85 * cm, 0.85 * cm, 3, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(MARGIN + 0.425 * cm, y - 0.58 * cm, num)
    c.setFont("Helvetica-Bold", 11.5)
    c.setFillColor(DARK_GREEN)
    c.drawString(MARGIN + 1.15 * cm, y - 0.35 * cm, title)
    paragraph(desc, MARGIN + 1.15 * cm, y - 0.75 * cm, CONTENT_W - 1.15 * cm, size=9.5, leading=12.5, color=TEXT_DARK)
    y -= 2.35 * cm

# ============================================================== CONCLUSION =
new_page("Conclusion")
y = header_band("10. Conclusion business orientée action")
y -= 0.4 * cm
y = paragraph(
    "AfriMarket dispose d'un socle commercial sain : 2,51 M$ de CA sur 6 mois, 754 k$ de profit net "
    "estimé, une base client majoritairement fidèle (73,2% de récurrence) et un taux d'annulation "
    "globalement faible (1,9%). Trois leviers d'action immédiats se dégagent : consolider "
    "l'Électronique en maîtrisant ses retours, corriger la rentabilité structurelle de Mode et Beauté "
    "par le panier moyen plutôt que par le volume, et traiter sans délai l'anomalie opérationnelle de "
    "Douala qui grève silencieusement la performance géographique.",
    MARGIN, y, CONTENT_W,
)
y -= 0.5 * cm
y = paragraph(
    "Sur le plan marketing, un simple réarbitrage de budget — moins d'Influenceur, plus d'Email et de "
    "Google Ads — peut améliorer le ROI global sans augmenter la dépense totale. Enfin, la "
    "fidélisation doit devenir différenciée par segment plutôt qu'uniforme, pour sécuriser le cœur de "
    "revenu (segment Platine) tout en développant la base moins engagée.",
    MARGIN, y, CONTENT_W,
)
y -= 0.6 * cm
c.setFillColor(PALE_GREEN)
c.roundRect(MARGIN, y - 1.6 * cm, CONTENT_W, 1.6 * cm, 4, fill=1, stroke=0)
paragraph(
    "Ces indicateurs sont pilotables mensuellement dans le dashboard Streamlit livré avec cette "
    "analyse, pour un suivi continu par la direction.",
    MARGIN + 0.4 * cm, y - 0.7 * cm, CONTENT_W - 0.8 * cm, size=10.5, color=DARK_GREEN,
)

footer(current_chapter)
c.save()
print(f"Rapport PDF écrit : {OUT}  ({page_no} pages)")
