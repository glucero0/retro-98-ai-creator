"""Gemini grounding helpers."""

from types import SimpleNamespace

from retro_game_creator.gemini_provider import _extract_grounding_sources


def test_extract_grounding_from_chunks():
    response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                grounding_metadata=SimpleNamespace(
                    grounding_chunks=[
                        SimpleNamespace(
                            web=SimpleNamespace(title="MobyGames", uri="https://example.com/doom")
                        )
                    ],
                    search_entry_point=None,
                    web_search_queries=[],
                )
            )
        ]
    )
    sources = _extract_grounding_sources(response)
    assert sources == [{"title": "MobyGames", "url": "https://example.com/doom"}]


def test_extract_grounding_falls_back_to_queries():
    response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                grounding_metadata=SimpleNamespace(
                    grounding_chunks=[],
                    search_entry_point=None,
                    web_search_queries=["Doom MS-DOS release year"],
                )
            )
        ]
    )
    sources = _extract_grounding_sources(response)
    assert len(sources) == 1
    assert sources[0]["title"].startswith("Search:")
    assert "Doom" in sources[0]["url"]
