"""agent/tools/normalisation.py — Cœur de normalisation texte partagé.

Utilisé par les différentes fonctions de résolution/recherche déterministes
(sql_tool.py, recherche_tool.py) qui ont chacune besoin d'un texte
comparable indépendamment des accents et de la casse, avant d'appliquer
leur propre traitement spécifique par-dessus (préfixe institutionnel,
tirets, etc.) — factorisé ici pour n'avoir qu'un seul endroit où corriger
l'algorithme d'accent-fold si un cas limite apparaît.
"""

import unicodedata


def normaliser_texte_base(texte: str) -> str:
    """Accents supprimés (NFKD -> ASCII) et minuscules. Ne traite ni les
    espaces superflus ni la ponctuation, laissés aux appelants selon leur
    besoin propre (cf. sql_tool._normaliser_nom, sql_tool._normaliser_zone_administrative)."""
    return unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii").lower()
