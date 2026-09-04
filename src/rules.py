class RuleEngine:
    """
    Determines which fragments are needed for a given day.
    Current implementation is a simplified mock for Sunday 6 Sept.
    """
    
    def get_orthros_structure(self, date):
        """
        Returns a list of fragment keys for the Orthros service.
        Following melodos.com's comprehensive version for Sunday 6 Sept.
        """
        # Sequence for Sunday Sept 6 (Archangel Michael)
        structure = [
            "sunday_plagal1_apolyticion",
            "st_michael_apolyticion",
            "common_theotokion_tone4",
            "sunday_plagal1_kathismata",
            "st_michael_kathismata",
            "sunday_plagal1_canon",
            "st_michael_canon_1",
            "st_michael_canon_2",
            "st_michael_kontakion",
            "st_michael_oikos",
            "common_timiotera",
            "sunday_plagal1_ainoi",
            "st_michael_ainoi",
            "common_doxology"
        ]
        return structure


