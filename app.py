import streamlit as st
import json
import re
import nest_asyncio
import time
from collections import defaultdict
from difflib import SequenceMatcher
from typing import List

# Nieuw voor Excel-ondersteuning:
import pandas as pd
import os

# Zorg ervoor dat er een event loop is voordat je nest_asyncio toepast
import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
nest_asyncio.apply()


############################################################
# 1. Hulpfuncties voor JSON-bestanden inladen en verwerken
############################################################

def load_multiple_files():
    """
    Laadt alle JSON-bestanden (omgevingsplannen en de besluiten) in één dict genaamd 'cache'.
    """
    files = [
        'omgevingsplannen_1.json',
        'omgevingsplannen_2.json',
        'bal.json',
        'bbl.json',
        'bkl.json'
    ]
    cache = {}
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as cache_file:
                data = json.load(cache_file)
                cache.update(data)  # Voeg inhoud van elk bestand toe aan de cache
        except FileNotFoundError:
            st.warning(f"Bestand '{file_path}' niet gevonden. Controleer of het bestand aanwezig is.")
    return cache


def search_paragraphs(content, term):
    """
    Zoekt naar paragrafen, afdelingen, hoofdstukken, artikelen in de content.
    Vindt matches die de zoekterm bevatten (case-insensitive) en sluit 'Artikel' uits.
    """
    paragraphs = set()
    lower_term = term.lower()
    # Regex zoekt o.a. naar 'Paragraaf 22.3.19', '§ 5.2', etc., en sluit 'Artikel' uit
    regex = r"(?<!Artikel\s)(Artikel|paragraaf|Paragraaf|§|Afdeling|Hoofdstuk) \d+(?:\.\d+)*.*?" + re.escape(lower_term)
    for match in re.finditer(regex, content, re.IGNORECASE):
        clean_title = re.sub(r'<[^>]+>', '', match.group().strip())
        # Controleer expliciet dat het niet begint met 'Artikel' of 'artikel'
        if not re.match(r'^(Artikel|artikel)\b', clean_title, re.IGNORECASE):
            paragraphs.add(clean_title)
    return list(paragraphs)


def generate_anchor_link(category, title, article_number=None):
    """
    Genereert enkel het fragment (beginnend met #), op basis van de categorie (Bal, Omgevingsplan, Bbl, Bkl)
    en de meegegeven titels/paragraafnummers.
    """
    # Besluit activiteiten leefomgeving (Bal)
    if category == "Besluit activiteiten leefomgeving":
        match = re.match(r"(paragraaf|Paragraaf|§|Afdeling|Hoofdstuk|Artikel) (\d+)\.(\d+)(?:\.(\d+))?", title)
        if match:
            if match.group(4):
                return f"#Hoofdstuk{match.group(2)}_Afdeling{match.group(2)}.{match.group(3)}_Paragraaf{match.group(2)}.{match.group(3)}.{match.group(4)}"
            else:
                return f"#Hoofdstuk{match.group(2)}_Paragraaf{match.group(2)}.{match.group(3)}"

    # Omgevingsplan
    elif category == "Omgevingsplan":
        # Als er expliciet een article_number is (bijvoorbeeld "22.263")
        if article_number:
            # bv. "22.263"
            if article_number.startswith('22.'):
                return f"#chp_22__subchp_22.3__subsec_22.3.26__art_{article_number}"
            else:
                return f"#art_{article_number}"
        else:
            # Eerst controleren of we 4 segmenten hebben: paragraaf x.x.x.x
            match_4 = re.match(r"(paragraaf|Paragraaf|§|Afdeling|Hoofdstuk) (\d+)\.(\d+)\.(\d+)\.(\d+)", title)
            if match_4:
                # Voorbeeld: 22.3.4.3 -> #chp_22__subchp_22.3__subsec_22.3.4__subsec_22.3.4.3
                return (
                    f"#chp_{match_4.group(2)}"
                    f"__subchp_{match_4.group(2)}.{match_4.group(3)}"
                    f"__subsec_{match_4.group(2)}.{match_4.group(3)}.{match_4.group(4)}"
                    f"__subsec_{match_4.group(2)}.{match_4.group(3)}.{match_4.group(4)}.{match_4.group(5)}"
                )

            # Daarna (anders) controleren op 3 segmenten: paragraaf x.x.x
            match_3 = re.match(r"(paragraaf|Paragraaf|§|Afdeling|Hoofdstuk) (\d+)\.(\d+)\.(\d+)", title)
            if match_3:
                return (
                    f"#chp_{match_3.group(2)}"
                    f"__subchp_{match_3.group(2)}.{match_3.group(3)}"
                    f"__subsec_{match_3.group(2)}.{match_3.group(3)}.{match_3.group(4)}"
                )
            # (Eventueel kun je hierna nog een match op 2 segmenten of 5 segmenten toevoegen.)

    # Besluit bouwwerken leefomgeving (Bbl)
    elif category == "Besluit bouwwerken leefomgeving":
        match = re.match(r"(Hoofdstuk|Afdeling|§|Artikel) (\d+)(?:\.(\d+))?(?:\.(\d+))?", title)
        if match:
            if match.group(1) == "Hoofdstuk":
                return f"#Hoofdstuk{match.group(2)}"
            elif match.group(1) == "Afdeling":
                return f"#Hoofdstuk{match.group(2)}_Afdeling{match.group(2)}.{match.group(3)}"
            elif match.group(1) == "§":
                return f"#Hoofdstuk{match.group(2)}_Afdeling{match.group(2)}.{match.group(3)}_Paragraaf{match.group(2)}.{match.group(3)}.{match.group(4)}"
            elif match.group(1) == "Artikel":
                article_number = match.group(2)
                return f"#art_{article_number}"

    # Besluit kwaliteit leefomgeving (Bkl)
    elif category == "Besluit kwaliteit leefomgeving":
        match = re.match(r"(Hoofdstuk|Afdeling|§|Artikel) (\d+)(?:\.(\d+))?(?:\.(\d+))?", title)
        if match:
            if match.group(1) == "Hoofdstuk":
                return f"#Hoofdstuk{match.group(2)}"
            elif match.group(1) == "Afdeling":
                return f"#Hoofdstuk{match.group(2)}_Afdeling{match.group(2)}.{match.group(3)}"
            elif match.group(1) == "§":
                return f"#Hoofdstuk{match.group(2)}_Afdeling{match.group(2)}.{match.group(3)}_Paragraaf{match.group(2)}.{match.group(3)}.{match.group(4)}"
            elif match.group(1) == "Artikel":
                article_number = match.group(2)
                return f"#art_{article_number}"

    return ""

    """
    Genereert enkel het fragment (beginnend met #), op basis van de categorie (Bal, Omgevingsplan, Bbl, Bkl)
    en de meegegeven titels/paragraafnummers.
    """

    # ---------------------------------------------
    # 1. Besluit activiteiten leefomgeving (Bal)
    # ---------------------------------------------
    if category == "Besluit activiteiten leefomgeving":
        match = re.match(r"(paragraaf|Paragraaf|§|Afdeling|Hoofdstuk|Artikel)\s+([\d\.]+)", title, re.IGNORECASE)
        if match:
            type_part = match.group(1).lower()  # bv. 'paragraaf' of 'artikel'
            numbers = match.group(2).split('.') # bv. ['3','4','3']

            # Begin altijd met Hoofdstuk + eerste cijfer
            anchor = f"#Hoofdstuk{numbers[0]}"

            # Als er meerdere cijfers zijn, ga opbouwen:
            # - Afdeling of Paragraaf
            # - eventueel extra niveaus etc.
            if len(numbers) >= 2:
                if type_part == "afdeling":
                    anchor += f"_Afdeling{numbers[0]}.{numbers[1]}"
                elif type_part in ["paragraaf", "§"]:
                    anchor += f"_Paragraaf{numbers[0]}.{numbers[1]}"

            # Elke verdere stap is óf paragraaf/§ óf artikel, afhankelijk van wat je wilt
            for i in range(2, len(numbers)):
                if type_part in ["artikel", "artikel"]:
                    # Alleen als echt 'Artikel' is opgegeven
                    anchor += f"_Artikel{'.'.join(numbers[:i+1])}"
                else:
                    anchor += f"_Paragraaf{'.'.join(numbers[:i+1])}"

            return anchor

    # ---------------------------------------------
    # 2. Omgevingsplan
    # ---------------------------------------------
    elif category == "Omgevingsplan":
        # Als er expliciet 'artikel' werd gevonden, gebruik dan de article_number-anker
        # Anders: gebruik de (meermaals) geneste paragraaf-anker
        match = re.match(r"(artikel)\s+([\d\.]+)", title, re.IGNORECASE)
        if match:
            # Gebruiker zocht expliciet op 'artikel x.x'
            article = match.group(2)
            return f"#art_{article}"

        else:
            # We gaan uit van 'paragraaf ...' of '§ ...' of 'Hoofdstuk ...' etc.
            # en bouwen subsections op
            match_para = re.match(r"(paragraaf|Paragraaf|§|Afdeling|Hoofdstuk)\s+([\d\.]+)", title, re.IGNORECASE)
            if match_para:
                numbers = match_para.group(2).split('.')
                # Voorbeeld: 22.3.4.3 -> ['22','3','4','3']

                # Bouw het anker stap voor stap
                if not numbers:
                    return ""

                # Eerste niveau: hoofdstuk
                anchor = f"#chp_{numbers[0]}"

                # Tweede niveau (als het er is): subchp
                if len(numbers) >= 2:
                    anchor += f"__subchp_{numbers[0]}.{numbers[1]}"

                # Derde niveau (als het er is): subsec_22.3.4
                if len(numbers) >= 3:
                    anchor += f"__subsec_{numbers[0]}.{numbers[1]}.{numbers[2]}"

                # Vierde en verdere niveaus: telkens opnieuw subsec_...
                if len(numbers) >= 4:
                    # Van i=3 tot het eind, dus meerdere nested paragrafen
                    for i in range(3, len(numbers)):
                        # Bouwt steeds op als 22.3.4.3 -> '22.3.4.3' etc.
                        partial = '.'.join(numbers[:i+1])
                        anchor += f"__subsec_{partial}"

                return anchor

    # ---------------------------------------------
    # 3. Besluit bouwwerken leefomgeving (Bbl)
    # ---------------------------------------------
    elif category == "Besluit bouwwerken leefomgeving":
        match = re.match(r"(Hoofdstuk|Afdeling|§|Artikel)\s+([\d\.]+)", title, re.IGNORECASE)
        if match:
            type_part = match.group(1).lower()
            numbers = match.group(2).split('.')

            anchor = f"#Hoofdstuk{numbers[0]}"
            if len(numbers) >= 2:
                if type_part == "afdeling":
                    anchor += f"_Afdeling{numbers[0]}.{numbers[1]}"
                elif type_part in ["paragraaf", "§"]:
                    anchor += f"_Paragraaf{numbers[0]}.{numbers[1]}"

            for i in range(2, len(numbers)):
                if type_part == "artikel":
                    anchor += f"_Artikel{'.'.join(numbers[:i+1])}"
                else:
                    anchor += f"_Paragraaf{'.'.join(numbers[:i+1])}"

            return anchor

    # ---------------------------------------------
    # 4. Besluit kwaliteit leefomgeving (Bkl)
    # ---------------------------------------------
    elif category == "Besluit kwaliteit leefomgeving":
        match = re.match(r"(Hoofdstuk|Afdeling|§|Artikel)\s+([\d\.]+)", title, re.IGNORECASE)
        if match:
            type_part = match.group(1).lower()
            numbers = match.group(2).split('.')

            anchor = f"#Hoofdstuk{numbers[0]}"
            if len(numbers) >= 2:
                if type_part == "afdeling":
                    anchor += f"_Afdeling{numbers[0]}.{numbers[1]}"
                elif type_part in ["paragraaf", "§"]:
                    anchor += f"_Paragraaf{numbers[0]}.{numbers[1]}"

            for i in range(2, len(numbers)):
                if type_part == "artikel":
                    anchor += f"_Artikel{'.'.join(numbers[:i+1])}"
                else:
                    anchor += f"_Paragraaf{'.'.join(numbers[:i+1])}"

            return anchor

    # Geen (herkenbare) match
    return ""

    """
    Genereert enkel het fragment (beginnend met #), op basis van de categorie (Bal, Omgevingsplan, Bbl, Bkl)
    en de meegegeven titels/paragraafnummers.
    """
    # Besluit activiteiten leefomgeving (Bal)
    if category == "Besluit activiteiten leefomgeving":
        match = re.match(r"(paragraaf|Paragraaf|§|Afdeling|Hoofdstuk|Artikel) (\d+)(?:\.(\d+))?(?:\.(\d+))?", title)
        if match:
            type_part = match.group(1).lower()
            numbers = [match.group(2)]
            if match.group(3):
                numbers.append(match.group(3))
            if match.group(4):
                numbers.append(match.group(4))
            
            anchor = f"#Hoofdstuk{numbers[0]}"
            if len(numbers) >= 2:
                if type_part == "afdeling":
                    anchor += f"_Afdeling{numbers[0]}.{numbers[1]}"
                else:
                    anchor += f"_Paragraaf{numbers[0]}.{numbers[1]}"
            if len(numbers) >= 3:
                anchor += f"_{type_part.capitalize()}{numbers[0]}.{numbers[1]}.{numbers[2]}"
            if len(numbers) >= 4:
                anchor += f"_{type_part.capitalize()}{numbers[0]}.{numbers[1]}.{numbers[2]}.{numbers[3]}"
            return anchor

    # Omgevingsplan
    elif category == "Omgevingsplan":
        if article_number:
            # bv. "22.263"
            if article_number.startswith('22.'):
                return f"#chp_22__subchp_22.3__subsec_22.3.26__art_{article_number}"
            else:
                return f"#art_{article_number}"
        else:
            # Mogelijk paragraaf x.x.x.x
            match = re.match(r"(paragraaf|Paragraaf|§|Afdeling|Hoofdstuk)\s+(\d+(?:\.\d+)*)", title)
            if match:
                numbers = match.group(2).split('.')
                if len(numbers) < 2:
                    return ""  # Onvoldoende niveaus om een anker te genereren

                anchor = f"#chp_{numbers[0]}"
                if len(numbers) >= 2:
                    subchp = f"{numbers[0]}.{numbers[1]}"
                    anchor += f"__subchp_{subchp}"
                if len(numbers) >= 3:
                    subsec = f"{numbers[0]}.{numbers[1]}.{numbers[2]}"
                    anchor += f"__subsec_{subsec}"
                if len(numbers) >= 4:
                    # Voor elk extra niveau, voeg een nieuwe subsec toe
                    for i in range(3, len(numbers)):
                        subsec = '.'.join(numbers[:i+1])
                        anchor += f"__subsec_{subsec}"
                return anchor

    # Besluit bouwwerken leefomgeving (Bbl)
    elif category == "Besluit bouwwerken leefomgeving":
        match = re.match(r"(Hoofdstuk|Afdeling|§|Artikel) (\d+)(?:\.(\d+))?(?:\.(\d+))?", title)
        if match:
            type_part = match.group(1).lower()
            numbers = [match.group(2)]
            if match.group(3):
                numbers.append(match.group(3))
            if match.group(4):
                numbers.append(match.group(4))
            
            anchor = f"#Hoofdstuk{numbers[0]}"
            if len(numbers) >= 2:
                if type_part == "afdeling":
                    anchor += f"_Afdeling{numbers[0]}.{numbers[1]}"
                else:
                    anchor += f"_Paragraaf{numbers[0]}.{numbers[1]}"
            if len(numbers) >= 3:
                anchor += f"_{type_part.capitalize()}{numbers[0]}.{numbers[1]}.{numbers[2]}"
            if len(numbers) >= 4:
                anchor += f"_{type_part.capitalize()}{numbers[0]}.{numbers[1]}.{numbers[2]}.{numbers[3]}"
            return anchor

    # Besluit kwaliteit leefomgeving (Bkl)
    elif category == "Besluit kwaliteit leefomgeving":
        match = re.match(r"(Hoofdstuk|Afdeling|§|Artikel) (\d+)(?:\.(\d+))?(?:\.(\d+))?", title)
        if match:
            type_part = match.group(1).lower()
            numbers = [match.group(2)]
            if match.group(3):
                numbers.append(match.group(3))
            if match.group(4):
                numbers.append(match.group(4))
            
            anchor = f"#Hoofdstuk{numbers[0]}"
            if len(numbers) >= 2:
                if type_part == "afdeling":
                    anchor += f"_Afdeling{numbers[0]}.{numbers[1]}"
                else:
                    anchor += f"_Paragraaf{numbers[0]}.{numbers[1]}"
            if len(numbers) >= 3:
                anchor += f"_{type_part.capitalize()}{numbers[0]}.{numbers[1]}.{numbers[2]}"
            if len(numbers) >= 4:
                anchor += f"_{type_part.capitalize()}{numbers[0]}.{numbers[1]}.{numbers[2]}.{numbers[3]}"
            return anchor

    return ""
    

def natural_sort_key(title: str) -> List:
    """
    Verbeterde sorteersleutel voor natuurlijke sortering.
    """
    parts = re.split(r'(\d+)', title)
    sorteersleutel = []
    for part in parts:
        if part.isdigit():
            sorteersleutel.append(int(part))
        elif part:
            sorteersleutel.append((ord(part[0]), part))
    return sorteersleutel


def filter_similar_results(results, similarity_threshold=1):
    """
    Filtert resultaten die sterk op elkaar lijken (>= similarity_threshold).
    """
    filtered_results = []
    seen_titles = set()
    for title, link, name in results:
        if not link or link.endswith("#"):
            continue
        normalized_title = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
        is_similar = False
        for seen_title in seen_titles:
            similarity = SequenceMatcher(None, normalized_title, seen_title).ratio()
            if similarity >= similarity_threshold:
                is_similar = True
                break
        if not is_similar:
            filtered_results.append((title, link, name))
            seen_titles.add(normalized_title)

    # Sorteer op basis van de natuurlijke sorteerfunctie
    filtered_results = sorted(filtered_results, key=lambda x: natural_sort_key(x[0]))
    return filtered_results


def extract_articles(content):
    """
    Dynamisch artikelen extraheren uit de content van JSON (bijv. 'Artikel 22.259 Omgevingsvergunning...').
    Deze functie is al eerder geïntroduceerd.
    """
    articles = []
    # Zoek naar patronen zoals "Artikel 22.259 Omgevingsvergunning..."
    regex = r"Artikel (\d+\.\d+)\s+([^\n<]+)"
    for match in re.finditer(regex, content, re.IGNORECASE):
        article_number = match.group(1)
        title = match.group(2).strip()
        articles.append({'title': f"Artikel {article_number} {title}", 'article_number': article_number})
    return articles


############################################################
# 2. Aanvullende functies voor Excel doorzoeken
############################################################

@st.cache_resource  # Gebruik st.cache_resource voor het cachen van niet-serialiseerbare objecten
def load_excel_file():
    """
    Laadt het Excel-bestand met rijksactiviteiten en bruidsschat.
    """
    excel_path = "overzicht-rijksactiviteiten-in-omgevingsloket-met-bron-in-regelgeving_v1-3.xlsx"
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel-bestand '{excel_path}' niet gevonden.")
    return pd.ExcelFile(excel_path)


def search_in_excel(search_term, gemeente, cache):
    """
    Doorzoekt de twee werkbladen in het Excel-bestand op de zoekterm.
    - In 'Bruidsschat omgevingsplan': zoek in kolommen 'Naam' en 'Activiteit ID'
    - In 'Overzicht activiteiten Rijk': zoek in kolommen 'Naam activiteit ', 'Activiteit ID'
    - Bij match -> 'Bron in regelgeving' uitlezen en per paragraaf ankerlinks maken.
    - Retourneert results_excel, een dict per categorie.
    """
    results_excel = defaultdict(set)

    try:
        xls = load_excel_file()
    except FileNotFoundError as e:
        st.warning(str(e))
        return results_excel  # leeg dict; we kunnen niks doorzoeken

    term_lower = search_term.lower()

    # Werkbladen die we gaan doorzoeken, met de relevante kolomnamen:
    work_sheets_info = [
        {
            "sheet_name": "Bruidsschat omgevingsplan",
            "cols_to_search": ["Naam", "Activiteit ID"]
        },
        {
            "sheet_name": "Overzicht activiteiten Rijk",
            "cols_to_search": ["Naam activiteit ", "Activiteit ID"]
        }
    ]

    # Haal base-URLs uit de cache, indien aanwezig
    bal_url = None
    bbl_url = None
    bkl_url = None
    omgevingsplan_url = None

    for url, data in cache.items():
        cat = data.get("category")
        if cat == "Besluit activiteiten leefomgeving":
            bal_url = url
        elif cat == "Besluit bouwwerken leefomgeving":
            bbl_url = url
        elif cat == "Besluit kwaliteit leefomgeving":
            bkl_url = url
        elif cat == "Omgevingsplan" and data.get("name").lower() == gemeente.lower():
            omgevingsplan_url = url

    def parse_and_generate_links(bron_regelgeving_str):
        """
        Splits 'Bron in regelgeving' (bijv. "Bal paragraaf 3.3.7, paragraaf 5.2.1 en paragraaf 5.4.3")
        in aparte paragrafen. Maak ankerlinks per paragraaf.
        """
        # We maken er zelf even een simpele splits van.
        # In de praktijk kun je een wat robuustere parse gebruiken.
        raw_parts = re.split(r",| en ", bron_regelgeving_str)  # splits op ',' of ' en '

        links_info = []

        for part in raw_parts:
            part = part.strip()
            # Voorbeeld: "Bal paragraaf 3.3.7"
            # Of "Bruidsschat Omgevingsplan paragraaf 22.3.8.9"
            # Bepaal eerst de categorie
            if part.lower().startswith("bal"):
                # -> Besluit activiteiten leefomgeving
                category_name = "Besluit activiteiten leefomgeving"
                base_url = bal_url
            elif part.lower().startswith("bbl"):
                category_name = "Besluit bouwwerken leefomgeving"
                base_url = bbl_url
            elif part.lower().startswith("bkl"):
                category_name = "Besluit kwaliteit leefomgeving"
                base_url = bkl_url
            elif "omgevingsplan" in part.lower():
                category_name = "Omgevingsplan"
                base_url = omgevingsplan_url
            else:
                # Onbekende categorie, overslaan of vangnet?
                continue

            # Nu proberen we het paragraafnummer te extraheren
            # Voorbeeld: "Bal paragraaf 3.3.7"
            # We zoeken naar "paragraaf (\d+(\.\d+)+)" of "artikel (\d+(\.\d+)?)"
            match_para = re.search(r"(paragraaf|artikel)\s+([\d\.]+)", part, re.IGNORECASE)
            if match_para:
                para_num = match_para.group(2)  # b.v. "3.3.7" of "22.269"
                # Genereer anchor fragment
                # Hier is het belangrijk dat de generate_anchor_link functie correct is
                # Voor paragrafen: "paragraaf x.x.x"
                # Voor artikelen: "artikel x.x"
                if match_para.group(1).lower() == "paragraaf":
                    anchor_fragment = generate_anchor_link(category_name, f"paragraaf {para_num}")
                elif match_para.group(1).lower() == "artikel":
                    anchor_fragment = generate_anchor_link(category_name, f"artikel {para_num}", article_number=para_num)
                else:
                    anchor_fragment = ""

                if base_url and anchor_fragment:
                    full_link = base_url + anchor_fragment
                    link_title = part  # We nemen de originele string als link-naam
                    # Sluit 'Artikel' resultaten uit
                    if not re.match(r'^(Artikel|artikel)\b', link_title, re.IGNORECASE):
                        links_info.append((link_title, full_link, category_name))

        return links_info

    # Doorzoek de aangegeven werkbladen
    for ws_info in work_sheets_info:
        sheet_name = ws_info["sheet_name"]
        cols_to_search = ws_info["cols_to_search"]

        try:
            df = pd.read_excel(xls, sheet_name=sheet_name)
        except ValueError:
            st.warning(f"Werkblad '{sheet_name}' niet gevonden in de Excel.")
            continue

        # Voor de zekerheid kolomnamen opschonen
        df.columns = [str(c).strip() for c in df.columns]

        for idx, row in df.iterrows():
            row_match = False
            for col in cols_to_search:
                if col not in df.columns:
                    continue
                cell_value = str(row[col]).strip().lower()
                if cell_value == term_lower:
                    row_match = True
                    break

            if row_match:
                # Pak de 'Bron in regelgeving'
                # Daar kunnen meerdere paragrafen in staan
                bron_regelgeving = str(row.get("Bron in regelgeving", "")).strip()
                if not bron_regelgeving:
                    # Geen bron, ga door
                    continue
                # Parse en maak links
                link_items = parse_and_generate_links(bron_regelgeving)
                for link_title, link_url, cat_name in link_items:
                    # Toevoegen aan results_excel[cat_name]
                    # 'name' zetten we op "Excel (werkbladnaam)"
                    excel_name = f"Excel ({sheet_name})"
                    results_excel[cat_name].add((link_title, link_url, excel_name))

    return results_excel


############################################################
# 3. Aangepaste process_cache-functie (met Excel-logica)
############################################################

def process_cache(cache, search_term, selected_categories, selected_gemeente=None):
    """
    1) Zoekt in JSON
    2) Als er geen resultaten zijn -> Zoek in Excel
    """
    grouped_results = defaultdict(set)
    all_categories = set()

    # --- (1) EERST ZOEKEN IN JSON ---
    for url, data in cache.items():
        name = data['name']
        category = data['category']
        content = data['content']
        all_categories.add(category)

        # Filter op gemeente
        if category == "Omgevingsplan" and selected_gemeente and name.lower() != selected_gemeente.lower():
            continue

        if category in selected_categories:
            paragraphs = search_paragraphs(content, search_term)
            for para in paragraphs:
                link = generate_anchor_link(category, para)
                if link:
                    full_link = url + link
                    # Sluit resultaten die beginnen met 'Artikel' uit
                    if not re.match(r'^(Artikel|artikel)\b', para, re.IGNORECASE):
                        grouped_results[category].add((para, full_link, name))

    # Check of er iets gevonden is
    found_any_json = any(len(v) > 0 for v in grouped_results.values())

    # --- (2) ZOEKEN IN EXCEL ALS JSON LEEG IS ---
    if not found_any_json:
        excel_results = search_in_excel(search_term, selected_gemeente, cache)
        if excel_results:
            # Sluit resultaten die beginnen met 'Artikel' uit
            for category, items in excel_results.items():
                for item in items:
                    title, link, source = item
                    if not re.match(r'^(Artikel|artikel)\b', title, re.IGNORECASE):
                        grouped_results[category].add(item)
        # anders blijft grouped_results leeg (geen results in JSON en Excel)

    # Eventueel kun je hier nog deduplicatie of fuzzy-check doen
    for category in grouped_results:
        grouped_results[category] = set(filter_similar_results(grouped_results[category]))

    return grouped_results, all_categories


############################################################
# 4. Hoofdfunctie voor de Streamlit-applicatie
############################################################

def main():
    st.title("MBA Zoekmachine")

    # Gebruiksaanwijzing als dropdownmenu
    with st.expander("Gebruiksaanwijzing"):
        st.write("Voer bij **\"Zoekterm\"** de Milieubelastende Activiteit (MBA) in zoals vermeld onder 'Verzoek'. "
                 "De applicatie doorzoekt de geselecteerde wetgeving en het omgevingsplan van de gekozen gemeente op deze term.")
        st.write("**Zoektips:**")
        st.write("- **Vermijd leestekens** in uw zoekterm voor betere resultaten.")
        st.write("- **Gebruik een deel van de term** als er geen resultaten worden gevonden, om de kans op treffers te vergroten.")

    with st.form(key='search_form'):
        search_term = st.text_input("Voer de zoekterm in:")
        submit_button = st.form_submit_button(label="Zoeken")

    # Categorieën in gewenste volgorde
    ordered_categories = [
        "Besluit activiteiten leefomgeving",
        "Omgevingsplan",
        "Besluit bouwwerken leefomgeving",
        "Besluit kwaliteit leefomgeving"
    ]

    selected_categories = st.multiselect("Kies de categorieën:", options=ordered_categories, default=ordered_categories)

    gemeente = None
    if "Omgevingsplan" in selected_categories:
        cache = load_multiple_files()
        gemeenten = sorted({data['name'] for url, data in cache.items() if data['category'] == "Omgevingsplan"})
        gemeente = st.selectbox("Kies de gemeente voor Omgevingsplan:", gemeenten)

    if submit_button:
        if not search_term.strip():
            st.error("Voer een geldige zoekterm in.")
            return

        with st.spinner('Zoeken...'):
            cache = load_multiple_files()
            if not cache:
                st.error("Geen data beschikbaar om te doorzoeken.")
                return

            # Hier doen we eerst de JSON-search, en indien leeg -> Excel
            grouped_results, all_categories = process_cache(
                cache,
                search_term,
                selected_categories,
                selected_gemeente=gemeente
            )

            # Controleer of er resultaten zijn; als niet, zoek in Excel en toon melding
            if not any(len(v) > 0 for v in grouped_results.values()):
                st.write("Geen resultaten gevonden in zowel JSON als Excel.")
            else:
                # Toon resultaten per categorie
                for category in ordered_categories:
                    if category in selected_categories:
                        st.write(f"### {category}")
                        if category in grouped_results and grouped_results[category]:
                            time.sleep(1)
                            for para, link, name in grouped_results[category]:
                                st.markdown(f"[**{para}**]({link}) — {name}")
                        else:
                            st.write("Geen zoekresultaten gevonden.")
                        st.write("---")


if __name__ == "__main__":
    main()
