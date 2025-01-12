
# MBA Zoekmachine

**MBA Zoekmachine** is een interactieve webapplicatie ontwikkeld met Streamlit die gebruikers in staat stelt om snel en efficiënt te zoeken binnen verschillende juridische documenten, zoals omgevingsplannen en besluiten. De applicatie biedt geavanceerde zoekmogelijkheden, waaronder het doorzoeken van subparagrafen en het genereren van directe hyperlinks naar specifieke paragrafen binnen de documenten.

## Inhoudsopgave

- [Over het Project](#over-het-project)
- [Functies](#functies)
- [Technologieën](#technologieën)
- [Installatie](#installatie)
- [Gebruik](#gebruik)
- [Bestandsstructuur](#bestandsstructuur)
- [Bijdragen](#bijdragen)
- [Licentie](#licentie)
- [Contact](#contact)
- [Aanvullende Informatie](#aanvullende-informatie)
- [Veelgestelde Vragen (FAQ)](#veelgestelde-vragen-faq)

## Over het Project

Het **MBA Zoekmachine** project is ontworpen om professionals en geïnteresseerden in milieubelastende activiteiten (MBA) te helpen bij het snel vinden van relevante informatie binnen omvangrijke juridische documenten. Door het implementeren van geavanceerde zoekalgoritmes en het gebruik van natuurlijke sortering, biedt de applicatie een gebruiksvriendelijke interface voor het navigeren door complexe regelgeving.

## Functies

- **Geavanceerd Zoekmechanisme:** Zoek niet alleen naar exacte termen, maar ook naar alle woorden binnen een zoekopdracht, ongeacht de volgorde.
- **Subparagraaf Zoekopdrachten:** Doorzoek paragraaftitels en subparagrafen binnen omgevingsplannen.
- **Dynamische Hyperlinks:** Genereer directe hyperlinks naar specifieke paragrafen binnen documenten, inclusief subparagrafen en artikelen.
- **Categorie Selectie:** Kies uit verschillende categorieën zoals "Besluit activiteiten leefomgeving", "Omgevingsplan", "Besluit bouwwerken leefomgeving", en "Besluit kwaliteit leefomgeving".
- **Gemeente Specifieke Zoekopdrachten:** Specificeer de gemeente voor omgevingsplannen om gerichte zoekresultaten te krijgen.
- **Duplicaatpreventie:** Voorkom dubbele resultaten door vergelijkbare of identieke paragrafen te filteren.
- **Alternatieve Bestandsbronnen:** Gebruik de directe downloadmogelijkheden van BAL, BKL en BBL via wetten.overheid.nl of download XML-bestanden voor omgevingsplannen via Google.

## Technologieën

- **Python 3.x**
- **Streamlit:** Voor het bouwen van de webinterface.
- **JSON:** Voor het opslaan en laden van juridische documenten.
- **Reguliere Expressies (re):** Voor het zoeken naar paragrafen.
- **Difflib (SequenceMatcher):** Voor het filteren van vergelijkbare resultaten.
- **Asyncio en nest_asyncio:** Voor asynchrone functionaliteit.
- 
## Installatie

Volg de onderstaande stappen om de MBA Zoekmachine op je lokale machine te installeren en uit te voeren.

### Vereisten

- Python 3.7 of hoger
- Pip (Python package manager)

### Stappen

1. **Clone de Repository**

    ```bash
    git clone https://github.com/jouwgebruikersnaam/mba-zoekmachine.git
    cd mba-zoekmachine
    ```

2. **Maak een Virtuele Omgeving (optioneel maar aanbevolen)**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Voor Unix of MacOS
    venv\Scripts ctivate     # Voor Windows
    ```

3. **Installeer de Benodigde Pakketten**

    ```bash
    pip install -r requirements.txt
    ```

    *Als je geen `requirements.txt` hebt, kun je de volgende pakketten installeren:*

    ```bash
    pip install streamlit nest_asyncio
    ```

4. **Verkrijg de Benodigde Bestanden**

    - Voor BAL, BKL en BBL:
        - Ga naar [wetten.overheid.nl](https://wetten.overheid.nl) en download de JSON-bestanden via de knop naast "Printen".
    - Voor Omgevingsplannen:
        - Zoek op Google naar: `"xml omgevingsplan gemeente NAAM"`.
        - Selecteer de link die begint met `https://lokaleregelgeving-acc.overheid.nl/CVDR`.
       
5. **Start de Streamlit Applicatie**

    ```bash
    streamlit run app.py
    ```

    *Vervang `app.py` door de naam van jouw Python-bestand als dat anders is.*

## Gebruik

1. **Open de Applicatie**

    Na het starten van de applicatie, wordt er een lokale webserver gestart. Open de URL die in de terminal wordt weergegeven (meestal `http://localhost:8501`) in je webbrowser.

2. **Voer een Zoekterm In**

    - Gebruik het invoerveld om de gewenste zoekterm in te voeren.
    - Je kunt meerdere woorden invoeren; alle ingevoerde woorden moeten voorkomen in de titel voor een match.

3. **Selecteer Categorieën**

    - Kies de juridische documenten waarin je wilt zoeken via de categorie-selectie.
    - Opties zijn onder andere:
        - Besluit activiteiten leefomgeving
        - Omgevingsplan
        - Besluit bouwwerken leefomgeving
        - Besluit kwaliteit leefomgeving

4. **Selecteer Gemeente (indien van toepassing)**

    - Als "Omgevingsplan" is geselecteerd, kies dan de gewenste gemeente om de zoekopdracht te beperken tot dat specifieke omgevingsplan.

5. **Bekijk de Resultaten**

    - Na het indienen van de zoekopdracht, worden de resultaten weergegeven per categorie.
    - Elke resultaat is een hyperlink die direct verwijst naar de relevante paragraaf binnen het document.
    - Indien er geen resultaten worden gevonden, wordt een bericht weergegeven.

## Bestandsstructuur

```
mba-zoekmachine/
├── omgevingsplannen_1.json
├── omgevingsplannen_2.json
├── bal.json
├── bbl.json
├── bkl.json
├── app.py
├── requirements.txt
├── README.md
└── ...
```

- **JSON Bestanden:** Bevatten de juridische documenten en worden door de applicatie geladen voor zoekfunctionaliteit.
- **app.py:** Hoofd Python-script dat de Streamlit-applicatie runt.
- **requirements.txt:** Lijst van Python-pakketten die nodig zijn voor het project.
- **README.md:** Dit bestand.

## Bijdragen

Bijdragen aan het project zijn altijd welkom! Volg deze stappen om bij te dragen:

1. **Fork de Repository**
2. **Maak een Nieuwe Branch**

    ```bash
    git checkout -b feature/nieuwe-functie
    ```

3. **Commit je Wijzigingen**

    ```bash
    git commit -m "Voeg nieuwe functie toe"
    ```

4. **Push naar de Branch**

    ```bash
    git push origin feature/nieuwe-functie
    ```

5. **Open een Pull Request**

    Beschrijf de wijzigingen en waarom ze nodig zijn.

## Licentie

Dit project is gelicentieerd onder de [MIT License](LICENSE).

## Contact

Voor vragen, opmerkingen of suggesties kun je contact met me opnemen via:

- **Email:** denieuwstraat@gmail.com
- **GitHub:** [Denieuwstraat]([https://github.com/Denieuwstraat]

## Aanvullende Informatie

### JSON Bestandsstructuur

Om ervoor te zorgen dat de applicatie correct functioneert, moeten de JSON-bestanden een specifieke structuur hebben. Hieronder een voorbeeld van de verwachte structuur:

```json
{
    "url_1": {
        "name": "Gemeente Voorbeeld",
        "category": "Omgevingsplan",
        "content": "Inhoud van het omgevingsplan met paragrafen..."
    },
    "url_2": {
        "name": "Besluit Activiteiten Leefomgeving",
        "category": "Besluit activiteiten leefomgeving",
        "content": "Inhoud van het besluit activiteiten leefomgeving..."
    },
    ...
}
```

- **URL Sleutels:** Elke sleutel in de hoofddictionary is een unieke URL die verwijst naar een document.
- **Name:** Naam van de gemeente of het besluit.
- **Category:** Categorie van het document.
- **Content:** Tekstuele inhoud van het document waarin gezocht wordt.

### Requirements.txt

Zorg ervoor dat je een `requirements.txt` bestand hebt met de benodigde pakketten om het installeren te vergemakkelijken. Hier is een voorbeeld:

```
streamlit
nest_asyncio
```

Je kunt extra pakketten toevoegen indien nodig.

## Veelgestelde Vragen (FAQ)

**1. Wat doe ik als een JSON-bestand ontbreekt?**

De applicatie toont een waarschuwing als een JSON-bestand niet wordt gevonden. Controleer of alle vereiste JSON-bestanden zich in de hoofdmap bevinden en herstart de applicatie.

**2. Waarom worden sommige resultaten nog steeds dubbel weergegeven?**

De duplicaatfiltering kan worden aangepast door de `similarity_threshold` in de `filter_similar_results` functie. Als je nog steeds duplicaten ziet, kun je deze drempel verlagen (bijvoorbeeld naar `0.95`) om flexibeler overeenkomsten toe te staan.

**3. Hoe kan ik nieuwe categorieën toevoegen?**

Voeg de nieuwe categorieën toe aan de `ordered_categories` lijst in de `main` functie en implementeer indien nodig specifieke logica in de `generate_anchor_link` functie.

---
