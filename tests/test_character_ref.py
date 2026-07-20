from cogni import images

CHAR = {"name": "Elias Vance", "description": "a gaunt man in a grey coat"}


def test_person_shot_detected_by_name():
    assert images._shot_has_person("Elias stares at the fence", CHAR) is True


def test_person_shot_detected_by_pronoun_or_noun():
    assert images._shot_has_person("a man alone on a bunk", CHAR) is True
    assert images._shot_has_person("his hands, close up", CHAR) is True


def test_pure_object_shot_is_not_a_person_shot():
    # object/landscape shots must NOT get a face reference — it biases them toward
    # inserting a person that the beat never asked for
    assert images._shot_has_person("A single worn boot in the snow, no one around", CHAR) is False
    assert images._shot_has_person("An empty barracks corridor at dawn", CHAR) is False


def test_no_character_means_no_person_match_on_name():
    assert images._shot_has_person("A cold grey sky over wire", None) is False
