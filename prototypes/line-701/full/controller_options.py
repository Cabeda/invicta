"""One controller configuration mapping for native trials and prefix replays."""


def priority_options(config):
    if 'phase_resequence' in config:
        raise ValueError('Phase resequencing was rejected; only bounded phase-order-preserving priority is supported')
    if not config.get('signal_priority'):
        return None
    return {'early_green': config.get('early_green', False),
            'shorten_served_pedestrian_green': config.get('shorten_served_pedestrian_green', False),
            'extension_limit': config.get('extension_limit', 10),
            'tls_filter': config.get('priority_tls'),
            'minimum_conflicting_green': config.get('priority_min_green', 15)}
