from datetime import timedelta

sexualdelikte_zumessungskriterien = {
    "Hauptdelikt": {
        "possible_options": ["Vergewaltigung", "Sexuelle Nötigung", "Andere Sexualdelikte"],
        "selected_option": "Vergewaltigung"
    },
    "mehrfache Begehung": {
        "possible_options": [True, False],
        "selected_option": False
    },
    # nur wenn einfache Begehung
    "deliktsdauer": {
        "possible_options": timedelta,
        "selected_option": timedelta(minutes=30)
    },
    # nur wenn mehrfache Begehung
    "Zahl der Delikte": {
        "possible_options": int,
        "selected_option": null
    },
    # nur wenn mehrfache Begehung
    "Deliktsperiode": {
        "possible_options": timedelta,
        "selected_option": timedelta(days=345)
    },
    "zusätzliche Sexualdelikte": {
        "possible_options": [
            "Sexuelle Nötigung",
            "Sexuelle Nötigung, mehrfache"
            "Sexuelle Handlungen mit Kindern",
            "Sexuelle Handlungen mit Kindern, mehrfache",
            "Schändung",
            "Schändung, mehrfache"
            "Keine weiteren Sexualdelikte",
            "Andere Sexualdelikte"
        ],
        "selected_option": "keine weiteren Sexualdelikte"
    },

    "number_of_offenses": {
        "possible_options": ["Einzeltat", "Mehrfachtat"],
        "selected_option": "Einzeltat"
    },
    "offense_period": {
        "possible_options": ["Einzeltat", "Mehrfache Tatbegehung über einen Zeitraum"],
        "selected_option": "Einzeltat"
    },
    "means_of_commitment": {
        "possible_options": [
            "Bedrohung",
            "Gewalt",
            "Psychischer Druck",
            "Unfähigkeit des Opfers, Widerstand zu leisten"
        ],
        "selected_options": ["Gewalt", "Psychischer Druck", "Unfähigkeit des Opfers, Widerstand zu leisten"]
    },
    "confession": {
        "possible_options": [True, False],
        "selected_option": False
    },
    "violation_of_speedy_trial_principle": {
        "possible_options": [True, False],
        "selected_option": False
    },
    "foreign_national": {
        "possible_options": [True, False],
        "selected_option": True
    },
    "prior_convictions": {
        "possible_options": [True, False],
        "selected_option": False
    },
    "victim_offender_relationship": {
        "possible_options": ["Ehegatte/Partner", "Elternteil/Kind", "Bekannte", "Unbekannt"],
        "selected_option": "Bekannte"
    }
}
