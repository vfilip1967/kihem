import unittest

from src.app import (
    _NEANES_SW_KILL_SWITCH,
    _neanes_asset_cache,
    _neanes_reader_fonts,
    _neanes_without_pwa,
)


class NeanesDeliveryTests(unittest.TestCase):
    def test_font_preload_keeps_only_the_score_fonts(self):
        built = (
            "function ee(){let e=new Set;for(let t of Xt.bundledFamilies())for(let n of Xt.getStyles(t))"
            "e.add(b(t,n));return e.add(b(`NeanesRTL`)),e.add(b(`NeanesRTLLegacy`)),[...e]}"
        )
        rewritten = _neanes_reader_fonts(built)
        self.assertIn("for(let t of [`Neanes`])for(let n of Xt.getStyles(t))e.add(b(t,n));", rewritten)
        self.assertIn("e.add(b(`Source Serif`))", rewritten)
        self.assertNotIn("bundledFamilies", rewritten)

    def test_unknown_build_is_left_unchanged(self):
        other = "function f(){return [...fonts]}"
        self.assertEqual(_neanes_reader_fonts(other), other)

    def test_index_never_registers_the_service_worker(self):
        index = (
            '<link rel="manifest" href="/x/manifest.webmanifest">'
            '<script id="vite-plugin-pwa:register-sw" src="/x/registerSW.js"></script>'
        )
        served = _neanes_without_pwa("index.html", index)
        self.assertNotIn("registerSW.js", served)
        self.assertNotIn('rel="manifest"', served)
        self.assertIn("unregister", served)
        self.assertIn("registration.unregister()", _NEANES_SW_KILL_SWITCH)

    def test_hashed_assets_are_cached_for_a_year(self):
        self.assertIn("immutable", _neanes_asset_cache("assets/Home-BuM86A6u.js"))
        self.assertNotIn("immutable", _neanes_asset_cache("index.html"))


if __name__ == "__main__":
    unittest.main()
