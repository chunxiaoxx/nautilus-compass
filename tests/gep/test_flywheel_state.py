def test_state_symbols_are_directly_importable_and_legacy_reexports_identical():
    from gep.flywheel_state import EpisodeState, reduce_episode_states
    from gep.flywheel_log import (
        EpisodeState as LegacyEpisodeState,
        reduce_episode_states as legacy_reduce_episode_states,
    )

    assert LegacyEpisodeState is EpisodeState
    assert legacy_reduce_episode_states is reduce_episode_states
