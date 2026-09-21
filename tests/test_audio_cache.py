import unittest
from tempfile import TemporaryDirectory

from src.audio_cache import InvalidMelodosAudioUrl, MelodosAudioCache


class _Response:
    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        yield b"first-"
        yield b"download"


class _Session:
    def __init__(self):
        self.calls = 0

    def get(self, url, *, stream, timeout):
        self.calls += 1
        return _Response()


class MelodosAudioCacheTests(unittest.TestCase):
    def test_downloads_once_then_reads_the_persistent_cache(self):
        with TemporaryDirectory() as temporary:
            session = _Session()
            cache = MelodosAudioCache(temporary, session=session)
            source = "https://melodos.com/akolouthies/mousika/orthros/test.mp3"

            first = cache.get(source)
            second = cache.get(source)

            self.assertEqual(first, second)
            self.assertEqual(first.read_bytes(), b"first-download")
            self.assertEqual(session.calls, 1)

    def test_only_melodos_music_mp3_urls_are_accepted(self):
        with TemporaryDirectory() as temporary:
            cache = MelodosAudioCache(temporary, session=_Session())
            for source in (
                "https://example.invalid/akolouthies/mousika/test.mp3",
                "http://melodos.com/akolouthies/mousika/test.mp3",
                "https://melodos.com/other/test.mp3",
                "https://melodos.com/akolouthies/mousika/test.pdf",
                "https://melodos.com/akolouthies/mousika/test.mp3?redirect=x",
            ):
                with self.subTest(source=source), self.assertRaises(InvalidMelodosAudioUrl):
                    cache.get(source)


if __name__ == "__main__":
    unittest.main()
