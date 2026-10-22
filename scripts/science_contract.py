"""Build draft scientific requirements from source text, without inventing facts."""
from __future__ import annotations

import copy


def science_contract(record, step):
    if step.get('science_spec'):
        return copy.deepcopy(step['science_spec'])
    requirements = []
    for identifier, description in (
            ('action', step.get('action') or step.get('instruction', '')),
            ('observation', step.get('observable_target') or step.get('state_after') or step.get('observation', ''))):
        if description:
            requirements.append({'id': identifier, 'description': description,
                'critical': True, 'evidence_kind': 'interval'})
    return {'source_reviewed': False, 'entities': [],
        'preconditions': [step['state_before']] if step.get('state_before') else [],
        'requirements': requirements, 'temporal_order': [],
        'review_notes': 'Draft requirements transcribed from source text. Review event boundaries, observation target, persistent entity IDs and source pages before acceptance.'}
