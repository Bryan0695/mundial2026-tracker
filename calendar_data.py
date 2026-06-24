"""
Calendario oficial Mundial 2026 - fase de grupos
=================================================
Datos reales de la FIFA: fecha, equipos, grupo y sede de cada partido.
Banderas como emoji por codigo de pais.
"""

# Emoji de bandera por nombre de equipo (ingles, igual que el motor).
FLAGS = {
    "Mexico": "🇲🇽", "Korea Republic": "🇰🇷", "Czechia": "🇨🇿", "South Africa": "🇿🇦",
    "Canada": "🇨🇦", "Switzerland": "🇨🇭", "Bosnia and Herzegovina": "🇧🇦", "Qatar": "🇶🇦",
    "Brazil": "🇧🇷", "Morocco": "🇲🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Haiti": "🇭🇹",
    "USA": "🇺🇸", "Australia": "🇦🇺", "Paraguay": "🇵🇾", "Turkiye": "🇹🇷",
    "Germany": "🇩🇪", "Ivory Coast": "🇨🇮", "Ecuador": "🇪🇨", "Curacao": "🇨🇼",
    "Netherlands": "🇳🇱", "Japan": "🇯🇵", "Sweden": "🇸🇪", "Tunisia": "🇹🇳",
    "Egypt": "🇪🇬", "Iran": "🇮🇷", "Belgium": "🇧🇪", "New Zealand": "🇳🇿",
    "Spain": "🇪🇸", "Uruguay": "🇺🇾", "Cape Verde": "🇨🇻", "Saudi Arabia": "🇸🇦",
    "France": "🇫🇷", "Norway": "🇳🇴", "Senegal": "🇸🇳", "Iraq": "🇮🇶",
    "Argentina": "🇦🇷", "Austria": "🇦🇹", "Algeria": "🇩🇿", "Jordan": "🇯🇴",
    "Colombia": "🇨🇴", "Portugal": "🇵🇹", "Congo DR": "🇨🇩", "Uzbekistan": "🇺🇿",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Ghana": "🇬🇭", "Croatia": "🇭🇷", "Panama": "🇵🇦",
}

def flag(team):
    return FLAGS.get(team, "⚽")


# Codigo ISO de 2 letras para flag-icons (clase CSS: "fi fi-XX").
# Para Inglaterra y Escocia se usa el codigo especial gb-eng / gb-sct.
ISO_CODES = {
    "Mexico": "mx", "Korea Republic": "kr", "Czechia": "cz", "South Africa": "za",
    "Canada": "ca", "Switzerland": "ch", "Bosnia and Herzegovina": "ba", "Qatar": "qa",
    "Brazil": "br", "Morocco": "ma", "Scotland": "gb-sct", "Haiti": "ht",
    "USA": "us", "Australia": "au", "Paraguay": "py", "Turkiye": "tr",
    "Germany": "de", "Ivory Coast": "ci", "Ecuador": "ec", "Curacao": "cw",
    "Netherlands": "nl", "Japan": "jp", "Sweden": "se", "Tunisia": "tn",
    "Egypt": "eg", "Iran": "ir", "Belgium": "be", "New Zealand": "nz",
    "Spain": "es", "Uruguay": "uy", "Cape Verde": "cv", "Saudi Arabia": "sa",
    "France": "fr", "Norway": "no", "Senegal": "sn", "Iraq": "iq",
    "Argentina": "ar", "Austria": "at", "Algeria": "dz", "Jordan": "jo",
    "Colombia": "co", "Portugal": "pt", "Congo DR": "cd", "Uzbekistan": "uz",
    "England": "gb-eng", "Ghana": "gh", "Croatia": "hr", "Panama": "pa",
}

def iso(team):
    return ISO_CODES.get(team, "")

# Calendario oficial: cada partido con fecha, jornada, grupo, equipos y sede.
# matchday = jornada real (1, 2 o 3).
OFFICIAL_CALENDAR = [
    # JORNADA 1
    {"date":"2026-06-11","jor":1,"group":"A","home":"Mexico","away":"South Africa","venue":"Ciudad de México"},
    {"date":"2026-06-11","jor":1,"group":"A","home":"Korea Republic","away":"Czechia","venue":"Guadalajara"},
    {"date":"2026-06-12","jor":1,"group":"B","home":"Canada","away":"Bosnia and Herzegovina","venue":"Toronto"},
    {"date":"2026-06-12","jor":1,"group":"D","home":"USA","away":"Paraguay","venue":"Los Ángeles"},
    {"date":"2026-06-13","jor":1,"group":"B","home":"Qatar","away":"Switzerland","venue":"San Francisco"},
    {"date":"2026-06-13","jor":1,"group":"C","home":"Brazil","away":"Morocco","venue":"Nueva York/NJ"},
    {"date":"2026-06-13","jor":1,"group":"C","home":"Haiti","away":"Scotland","venue":"Boston"},
    {"date":"2026-06-13","jor":1,"group":"D","home":"Australia","away":"Turkiye","venue":"Vancouver"},
    {"date":"2026-06-14","jor":1,"group":"E","home":"Germany","away":"Curacao","venue":"Houston"},
    {"date":"2026-06-14","jor":1,"group":"F","home":"Netherlands","away":"Japan","venue":"Dallas"},
    {"date":"2026-06-14","jor":1,"group":"E","home":"Ivory Coast","away":"Ecuador","venue":"Filadelfia"},
    {"date":"2026-06-14","jor":1,"group":"F","home":"Sweden","away":"Tunisia","venue":"Monterrey"},
    {"date":"2026-06-15","jor":1,"group":"H","home":"Spain","away":"Cape Verde","venue":"Atlanta"},
    {"date":"2026-06-15","jor":1,"group":"G","home":"Belgium","away":"Egypt","venue":"Seattle"},
    {"date":"2026-06-15","jor":1,"group":"H","home":"Saudi Arabia","away":"Uruguay","venue":"Miami"},
    {"date":"2026-06-15","jor":1,"group":"G","home":"Iran","away":"New Zealand","venue":"Los Ángeles"},
    {"date":"2026-06-16","jor":1,"group":"I","home":"France","away":"Senegal","venue":"Nueva York/NJ"},
    {"date":"2026-06-16","jor":1,"group":"I","home":"Iraq","away":"Norway","venue":"Boston"},
    {"date":"2026-06-16","jor":1,"group":"J","home":"Argentina","away":"Algeria","venue":"Kansas City"},
    {"date":"2026-06-16","jor":1,"group":"J","home":"Austria","away":"Jordan","venue":"San Francisco"},
    {"date":"2026-06-17","jor":1,"group":"K","home":"Portugal","away":"Congo DR","venue":"Houston"},
    {"date":"2026-06-17","jor":1,"group":"L","home":"England","away":"Croatia","venue":"Dallas"},
    {"date":"2026-06-17","jor":1,"group":"L","home":"Ghana","away":"Panama","venue":"Toronto"},
    {"date":"2026-06-17","jor":1,"group":"K","home":"Uzbekistan","away":"Colombia","venue":"Ciudad de México"},
    # JORNADA 2
    {"date":"2026-06-18","jor":2,"group":"A","home":"Czechia","away":"South Africa","venue":"Atlanta"},
    {"date":"2026-06-18","jor":2,"group":"B","home":"Switzerland","away":"Bosnia and Herzegovina","venue":"Los Ángeles"},
    {"date":"2026-06-18","jor":2,"group":"B","home":"Canada","away":"Qatar","venue":"Vancouver"},
    {"date":"2026-06-18","jor":2,"group":"A","home":"Mexico","away":"Korea Republic","venue":"Guadalajara"},
    {"date":"2026-06-19","jor":2,"group":"D","home":"USA","away":"Australia","venue":"Seattle"},
    {"date":"2026-06-19","jor":2,"group":"C","home":"Scotland","away":"Morocco","venue":"Boston"},
    {"date":"2026-06-19","jor":2,"group":"C","home":"Brazil","away":"Haiti","venue":"Filadelfia"},
    {"date":"2026-06-19","jor":2,"group":"D","home":"Turkiye","away":"Paraguay","venue":"San Francisco"},
    {"date":"2026-06-20","jor":2,"group":"F","home":"Netherlands","away":"Sweden","venue":"Houston"},
    {"date":"2026-06-20","jor":2,"group":"E","home":"Germany","away":"Ivory Coast","venue":"Toronto"},
    {"date":"2026-06-20","jor":2,"group":"E","home":"Ecuador","away":"Curacao","venue":"Kansas City"},
    {"date":"2026-06-20","jor":2,"group":"F","home":"Tunisia","away":"Japan","venue":"Monterrey"},
    {"date":"2026-06-21","jor":2,"group":"H","home":"Spain","away":"Saudi Arabia","venue":"Atlanta"},
    {"date":"2026-06-21","jor":2,"group":"G","home":"Belgium","away":"Iran","venue":"Los Ángeles"},
    {"date":"2026-06-21","jor":2,"group":"H","home":"Uruguay","away":"Cape Verde","venue":"Miami"},
    {"date":"2026-06-21","jor":2,"group":"G","home":"New Zealand","away":"Egypt","venue":"Vancouver"},
    {"date":"2026-06-22","jor":2,"group":"J","home":"Argentina","away":"Austria","venue":"Dallas"},
    {"date":"2026-06-22","jor":2,"group":"I","home":"France","away":"Iraq","venue":"Filadelfia"},
    {"date":"2026-06-22","jor":2,"group":"I","home":"Norway","away":"Senegal","venue":"Nueva York/NJ"},
    {"date":"2026-06-22","jor":2,"group":"J","home":"Jordan","away":"Algeria","venue":"San Francisco"},
    {"date":"2026-06-23","jor":2,"group":"K","home":"Portugal","away":"Uzbekistan","venue":"Houston"},
    {"date":"2026-06-23","jor":2,"group":"L","home":"England","away":"Ghana","venue":"Boston"},
    {"date":"2026-06-23","jor":2,"group":"L","home":"Panama","away":"Croatia","venue":"Toronto"},
    {"date":"2026-06-23","jor":2,"group":"K","home":"Colombia","away":"Congo DR","venue":"Guadalajara"},
    # JORNADA 3
    {"date":"2026-06-24","jor":3,"group":"B","home":"Switzerland","away":"Canada","venue":"Vancouver"},
    {"date":"2026-06-24","jor":3,"group":"B","home":"Bosnia and Herzegovina","away":"Qatar","venue":"Seattle"},
    {"date":"2026-06-24","jor":3,"group":"C","home":"Scotland","away":"Brazil","venue":"Miami"},
    {"date":"2026-06-24","jor":3,"group":"C","home":"Morocco","away":"Haiti","venue":"Atlanta"},
    {"date":"2026-06-24","jor":3,"group":"A","home":"Czechia","away":"Mexico","venue":"Ciudad de México"},
    {"date":"2026-06-24","jor":3,"group":"A","home":"South Africa","away":"Korea Republic","venue":"Monterrey"},
    {"date":"2026-06-25","jor":3,"group":"E","home":"Curacao","away":"Ivory Coast","venue":"Filadelfia"},
    {"date":"2026-06-25","jor":3,"group":"E","home":"Ecuador","away":"Germany","venue":"Nueva York/NJ"},
    {"date":"2026-06-25","jor":3,"group":"F","home":"Japan","away":"Sweden","venue":"Dallas"},
    {"date":"2026-06-25","jor":3,"group":"F","home":"Tunisia","away":"Netherlands","venue":"Kansas City"},
    {"date":"2026-06-25","jor":3,"group":"D","home":"Turkiye","away":"USA","venue":"Los Ángeles"},
    {"date":"2026-06-25","jor":3,"group":"D","home":"Paraguay","away":"Australia","venue":"San Francisco"},
    {"date":"2026-06-26","jor":3,"group":"I","home":"Norway","away":"France","venue":"Boston"},
    {"date":"2026-06-26","jor":3,"group":"I","home":"Senegal","away":"Iraq","venue":"Toronto"},
    {"date":"2026-06-26","jor":3,"group":"H","home":"Cape Verde","away":"Saudi Arabia","venue":"Houston"},
    {"date":"2026-06-26","jor":3,"group":"H","home":"Uruguay","away":"Spain","venue":"Guadalajara"},
    {"date":"2026-06-26","jor":3,"group":"G","home":"Egypt","away":"Iran","venue":"Seattle"},
    {"date":"2026-06-26","jor":3,"group":"G","home":"New Zealand","away":"Belgium","venue":"Vancouver"},
    {"date":"2026-06-27","jor":3,"group":"L","home":"Panama","away":"England","venue":"Nueva York/NJ"},
    {"date":"2026-06-27","jor":3,"group":"L","home":"Croatia","away":"Ghana","venue":"Filadelfia"},
    {"date":"2026-06-27","jor":3,"group":"K","home":"Colombia","away":"Portugal","venue":"Miami"},
    {"date":"2026-06-27","jor":3,"group":"K","home":"Congo DR","away":"Uzbekistan","venue":"Atlanta"},
    {"date":"2026-06-27","jor":3,"group":"J","home":"Algeria","away":"Austria","venue":"Kansas City"},
    {"date":"2026-06-27","jor":3,"group":"J","home":"Jordan","away":"Argentina","venue":"Dallas"},
]
