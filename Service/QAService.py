from typing import Dict, List, Tuple, Union

# Owns all QA routing rules and species/part constants for the FastAPI backend.
# Ruleset is sourced from this project's own test.py QA station (22 species,
# including 9 beetle species with dual-pose open/closed logic), NOT the
# smaller 12-species set used by other copies of this backend — this one
# already covers more ground and must not be downgraded.
#
# Note: 'heliocorpis_bucephalus' is spelled to match the trained model's
# actual output class name ("Heliocorpis bucephalus"), which differs from
# the correct taxonomic spelling ("Heliocopris"). A prior version of this
# ruleset used the taxonomically-correct spelling, which meant the rule
# below never matched the model's real output and that species was always
# flagged regardless of part count.
#
# 'graphium_weiskei' is a detectable model class but intentionally has no
# QA rule and is excluded from PARENT_SPECIES — treated as not needed.

PARENT_SPECIES: List[str] = [
    'papilio_ulysses', 'papilio_thoas', 'thysania_agripina', 'phyllium_pulchrifolium',
    'xylotrupes_gideon', 'papilio_blumei', 'papilio_karna', 'papilio_palinurus',
    'papilio_rumanzovia', 'polyura_delphis_concha', 'pomponia_imperatoria', 'idea_lynceus',
    'acrocinus_longimanus', 'chalcosoma_atlas', 'dorcus_alcides', 'heliocorpis_bucephalus',
    'heteropteryx_dilatata', 'hexarthrius_mandibularis', 'odontolabis_siva',
    'phryna_grosseitaitai', 'lamprima_adolphinae', 'prosopocoilus_savagei',
]

PART_CLASSES: List[str] = ['wing', 'antenna', 'leg', 'shell_wing', 'horn']

_GROUP_4W_2A: List[str] = [
    'papilio_thoas', 'thysania_agripina', 'idea_lynceus',
    'polyura_delphis_concha', 'papilio_palinurus', 'papilio_karna',
    'papilio_rumanzovia', 'papilio_blumei', 'papilio_ulysses',
]

# A rule is either a single dict (one valid pose) or a list of dicts
# (multiple valid poses, e.g. open/closed beetle shell — pass if ANY match).
QARule = Union[Dict[str, int], List[Dict[str, int]]]

QA_RULES: Dict[str, QARule] = {sp: {'wing': 4, 'antenna': 2} for sp in _GROUP_4W_2A}
QA_RULES['pomponia_imperatoria']    = {'wing': 4, 'leg': 4}
QA_RULES['phyllium_pulchrifolium']  = {'leg': 6, 'antenna': 2}
QA_RULES['xylotrupes_gideon']       = {'wing': 2, 'shell_wing': 2, 'leg': 4, 'horn': 1}
QA_RULES['heteropteryx_dilatata']   = {'antenna': 2, 'leg': 6, 'wing': 4}
QA_RULES['lamprima_adolphinae']     = {'wing': 2, 'leg': 4, 'shell_wing': 2, 'horn': 2}
QA_RULES['prosopocoilus_savagei']   = {'antenna': 2, 'wing': 2, 'shell_wing': 2, 'leg': 4, 'horn': 2}
QA_RULES['phryna_grosseitaitai']    = {'antenna': 2, 'leg': 6}
QA_RULES['hexarthrius_mandibularis'] = {'wing': 2, 'shell_wing': 2, 'horn': 2, 'antenna': 2, 'leg': 4}
QA_RULES['chalcosoma_atlas']        = {'wing': 2, 'horn': 3, 'shell_wing': 2, 'leg': 4}

# Dual-pose species — beetle may be photographed with shell closed (no
# wings visible) or open (wings extended); either is a valid PASS.
QA_RULES['dorcus_alcides'] = [
    {'leg': 6, 'antenna': 2, 'horn': 2, 'shell_wing': 2, 'wing': 0},  # closed
    {'leg': 4, 'antenna': 2, 'horn': 2, 'shell_wing': 2, 'wing': 2},  # open
]
QA_RULES['odontolabis_siva'] = [
    {'horn': 2, 'antenna': 2, 'leg': 6, 'shell_wing': 2, 'wing': 0},  # closed
    {'horn': 2, 'antenna': 2, 'leg': 4, 'shell_wing': 2, 'wing': 2},  # open
]
QA_RULES['heliocorpis_bucephalus'] = [
    {'shell_wing': 2, 'leg': 6, 'horn': 1, 'wing': 0},  # closed
    {'wing': 2, 'shell_wing': 2, 'leg': 4, 'horn': 1},  # open
]
QA_RULES['acrocinus_longimanus'] = [
    {'antenna': 2, 'leg': 6, 'shell_wing': 2, 'wing': 0},  # closed
    {'antenna': 2, 'leg': 4, 'shell_wing': 2, 'wing': 2},  # open
]


def _matches_pose(found_parts: Dict[str, int], pose: Dict[str, int]) -> bool:
    return all(found_parts.get(part, 0) == count for part, count in pose.items())


def apply_qa_routing(
    species_name: str,
    found_parts: Dict[str, int],
) -> Tuple[str, QARule]:
    rules = QA_RULES.get(species_name)
    if rules is None:
        return 'FLAGGED', {}
    if isinstance(rules, list):
        is_pass = any(_matches_pose(found_parts, pose) for pose in rules)
    else:
        is_pass = _matches_pose(found_parts, rules)
    return ('PASS' if is_pass else 'FLAGGED'), rules


def format_species_name(class_name: str) -> str:
    parts = class_name.split('_')
    if len(parts) >= 2:
        return parts[0].capitalize() + ' ' + ' '.join(parts[1:])
    return class_name.capitalize()
