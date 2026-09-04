import json
import os

class ServiceComposer:
    """
    Assembles liturgical fragments into a final service text
    based on the rules provided by the Rule Engine.
    """
    
    def __init__(self, fragments_path='/root/projects/kihem/data/fragments.json'):
        self.fragments_path = fragments_path
        self.fragments = self._load_fragments()

    def _load_fragments(self):
        if os.path.exists(self.fragments_path):
            with open(self.fragments_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def compose(self, structure):
        """
        Assembles the service based on a provided structure (list of fragment keys).
        :param structure: List of keys to lookup in fragments.
        """
        final_text = []
        for key in structure:
            if key in self.fragments:
                final_text.append(self.fragments[key])
            else:
                final_text.append(f"[Missing Fragment: {key}]")
        
        return "\n\n".join(final_text)
