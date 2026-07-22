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


# --- figure-beat gating: the real person only appears where the beat is about them -------
# In the new format the recurring figure is a REAL person (the author). "any beat with a
# person" put them into every crowd — the fix is to key on the figure's NAME in the beat.
AUTHOR = {"name": "Steven Levitt", "description": "a lean economist, glasses"}


def test_figure_beat_true_when_surname_in_narration():
    assert images._is_figure_beat("And Levitt ran the numbers himself.", "a man at a desk", AUTHOR) is True


def test_figure_beat_true_when_surname_in_prompt():
    assert images._is_figure_beat("The data told a different story.", "Levitt at a chalkboard", AUTHOR) is True


def test_generic_person_beat_is_not_a_figure_beat():
    # a daycare pickup, a sumo ring, a crowd — people, but NOT the author. He must not
    # be forced into them (that is how Frankl ended up on a modern couch).
    assert images._is_figure_beat("a parent rushes in late to collect a child", "a woman at a daycare door", AUTHOR) is False
    assert images._is_figure_beat("two wrestlers grapple in the ring", "a sumo bout, crowd watching", AUTHOR) is False


def test_no_figure_means_never_a_figure_beat():
    assert images._is_figure_beat("Levitt did the math", "a man", None) is False
