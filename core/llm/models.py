"""Model capability table (D4). Add one row per family; query via model_caps.

Converges what used to be scattered `if 'deepseek' in model` style special-casing
across session construction, history handling and request building into one place.
Zero internal dependencies — pure data + a lookup function.
"""

_MODEL_DEFAULTS = dict(context_win=30000, cut_msg_interval=5, trim_keep_rate=0.6, keep_thinking=False,
                       temperature_override=None, temperature_clamp=None, max_tokens_field='max_tokens')
_MODEL_CAPS = [
    (lambda ml: 'deepseek' in ml, dict(context_win=70000, cut_msg_interval=25, trim_keep_rate=0.3, keep_thinking=True)),
    (lambda ml: 'kimi' in ml or 'moonshot' in ml, dict(temperature_override=1)),
    (lambda ml: 'minimax' in ml, dict(temperature_clamp=(0.01, 1.0))),
    (lambda ml: ml.startswith(('gpt-5', 'o1', 'o2', 'o3', 'o4')), dict(max_tokens_field='max_completion_tokens')),
]

def model_caps(model):
    ml = (model or '').lower(); caps = dict(_MODEL_DEFAULTS)
    for match, override in _MODEL_CAPS:
        if match(ml): caps.update(override)
    return caps
