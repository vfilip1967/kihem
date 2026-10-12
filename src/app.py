from __future__ import annotations

import os
from hmac import compare_digest
from datetime import date, timedelta
from urllib.parse import quote

from flask import Flask, Response, abort, jsonify, make_response, render_template, request, send_file, send_from_directory
from markupsafe import Markup
from werkzeug.middleware.proxy_fix import ProxyFix

from src.audio_cache import InvalidMelodosAudioUrl, MelodosAudioCache
from src.anastasimatarion import (
    AnastasimatarionRenderer,
    enrich_service_html,
)
from src.composer import ServiceComposer
from src.digital_scores import DigitalScoreCatalog, DigitalScoreReviewStore
from src.liturgical_calendar import LiturgicalCalendar
from src.melodos import MELODOS_HOME, MelodosClient, MelodosError
from src.isokratis import ISON_NOTES, MODE_LABELS, IsokratisLibrary
from src.scripture_interpretations import ScriptureInterpretationService, add_reading_bookmarks
from src.typesafe_decisions import TypesafeDecisionService


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    # Production is mounted by Nginx below /kihem/.  Trust only the proxy's
    # explicitly configured prefix header, so generated private-asset URLs
    # retain that mount point while local development remains root-mounted.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.config.from_mapping(
        CACHE_DIR=os.environ.get("KIHEM_CACHE_DIR", "/tmp/kihem-cache"),
        BOOKS_DIR=os.environ.get("KIHEM_BOOKS_DIR", "/var/lib/kihem/books"),
        BYZ_DIR=os.environ.get("KIHEM_BYZ_DIR", "/var/lib/kihem/byz"),
        # An explicit environment value is useful for a controlled demo, but
        # regular visits open tomorrow's Orthros by default.
        DEFAULT_DATE=os.environ.get("KIHEM_DEFAULT_DATE"),
        INTERPRETATION_MODEL=os.environ.get("KIHEM_INTERPRETATION_MODEL", "gpt-5.6-luna"),
        TYPESAFE_MODEL=os.environ.get("KIHEM_TYPESAFE_MODEL", "jev-latest"),
        DIGITAL_SCORES_DIR=os.environ.get("KIHEM_DIGITAL_SCORES_DIR", "/var/lib/kihem/digital-scores"),
        DIGITAL_SCORES_CATALOG=os.environ.get(
            "KIHEM_DIGITAL_SCORES_CATALOG",
            os.path.join(app.root_path, "data", "digital_scores.json"),
        ),
        DIGITAL_SCORES_REVIEW_DIR=os.environ.get(
            "KIHEM_DIGITAL_SCORES_REVIEW_DIR", "/var/lib/kihem/digital-score-reviews"
        ),
        NEANES_WEB_DIR=os.environ.get("KIHEM_NEANES_WEB_DIR", "/var/lib/kihem/neanes-web"),
        REVIEW_USERNAME=os.environ.get("KIHEM_REVIEW_USERNAME"),
        REVIEW_PASSWORD=os.environ.get("KIHEM_REVIEW_PASSWORD"),
    )
    if config:
        app.config.update(config)

    composer = app.config.get("COMPOSER") or ServiceComposer(
        MelodosClient(cache_dir=app.config["CACHE_DIR"])
    )
    music_renderer = app.config.get("MUSIC_RENDERER") or AnastasimatarionRenderer(
        app.config["CACHE_DIR"], app.config["BOOKS_DIR"]
    )
    app.extensions["kihem_composer"] = composer
    app.extensions["kihem_music_renderer"] = music_renderer
    melodos_audio_cache = app.config.get("MELODOS_AUDIO_CACHE") or MelodosAudioCache(
        app.config["CACHE_DIR"]
    )
    app.extensions["kihem_melodos_audio_cache"] = melodos_audio_cache
    media_library = app.config.get("ISOKRATIS_LIBRARY") or IsokratisLibrary(
        app.config["BYZ_DIR"]
    )
    app.extensions["kihem_isokratis_library"] = media_library
    interpretation_service = app.config.get("SCRIPTURE_INTERPRETATION_SERVICE") or ScriptureInterpretationService(
        app.config["CACHE_DIR"], model=app.config["INTERPRETATION_MODEL"]
    )
    app.extensions["kihem_scripture_interpretation_service"] = interpretation_service
    typesafe_decisions = app.config.get("TYPESAFE_DECISION_SERVICE") or TypesafeDecisionService(
        app.config["CACHE_DIR"], model=app.config["TYPESAFE_MODEL"]
    )
    app.extensions["kihem_typesafe_decision_service"] = typesafe_decisions
    digital_score_catalog = app.config.get("DIGITAL_SCORE_CATALOG") or DigitalScoreCatalog(
        app.config["DIGITAL_SCORES_CATALOG"], app.config["DIGITAL_SCORES_DIR"]
    )
    app.extensions["kihem_digital_score_catalog"] = digital_score_catalog
    digital_score_review_store = app.config.get("DIGITAL_SCORE_REVIEW_STORE") or DigitalScoreReviewStore(
        app.config["DIGITAL_SCORES_REVIEW_DIR"]
    )
    app.extensions["kihem_digital_score_review_store"] = digital_score_review_store

    review_checks = (
        ("title_tone", "Τίτλος και ήχος συμφωνούν με την έντυπη πηγή."),
        ("lyrics", "Το κείμενο συμφωνεί πλήρως, φράση προς φράση."),
        ("neumes", "Τα νεύματα και οι μαρτυρίες ελέγχθηκαν φράση προς φράση."),
        ("time", "Χρόνος, γοργά και λοιπά χρονικά σημεία ελέγχθηκαν."),
        ("listening", "Έγινε ακουστικός έλεγχος από ψάλτη."),
    )

    def require_review_access() -> Response | None:
        """Keep draft comparison work out of the public Kihem surface."""
        username = app.config.get("REVIEW_USERNAME")
        password = app.config.get("REVIEW_PASSWORD")
        if not isinstance(username, str) or not username or not isinstance(password, str) or not password:
            abort(404)
        credentials = request.authorization
        if credentials and compare_digest(credentials.username or "", username) and compare_digest(
            credentials.password or "", password
        ):
            return None
        response = Response("Απαιτείται ιδιωτική πρόσβαση ελέγχου.", status=401, mimetype="text/plain")
        response.headers["WWW-Authenticate"] = 'Basic realm="Kihem private review", charset="UTF-8"'
        return response

    @app.get("/")
    def index():
        default_date = app.config["DEFAULT_DATE"] or (date.today() + timedelta(days=1)).isoformat()
        selected_raw = request.args.get("date", default_date)
        # The web view deliberately renders one service per request.  This keeps
        # the heavy scanned music excerpts from being downloaded twice on one
        # very long page.  Treat the old ``services=both`` links as the Orthros
        # page so existing bookmarks continue to open a useful result.
        requested_services = request.args.get("services", "orthros")
        selected_services = requested_services if requested_services in {"orthros", "litourgia"} else "orthros"
        refresh = request.args.get("refresh") == "1"
        error = None
        composition = None
        attachment_count = 0
        unmatched_piece_ids: list[str] = []
        music_bookmarks: list[dict[str, str]] = []
        reading_bookmarks: list[dict[str, str]] = []

        try:
            calendar = LiturgicalCalendar(selected_raw)
        except (ValueError, TypeError):
            calendar = LiturgicalCalendar(default_date)
            error = "Η ημερομηνία δεν είναι έγκυρη. Χρησιμοποίησε τη μορφή ΕΕΕΕ-ΜΜ-ΗΗ."

        if not error:
            services = (selected_services,)
            try:
                composition = composer.compose(
                    calendar.current_date, services=services, refresh=refresh
                )
            except (MelodosError, ValueError) as exc:
                error = str(exc)

        documents = []
        if composition:
            for item in composition.documents:
                enriched = enrich_service_html(
                    composition.selected_date,
                    item.service,
                    item.service_html,
                    instance_offset=attachment_count,
                    semantic_reviewer=typesafe_decisions,
                )
                service_html = enriched.html
                service_html = interpretation_service.enrich_service_html(
                    service_html,
                    service=item.service,
                )
                service_html, document_reading_bookmarks = add_reading_bookmarks(
                    service_html,
                    service=item.service,
                )
                attachment_count += enriched.attachment_count
                unmatched_piece_ids.extend(enriched.unmatched_piece_ids)
                music_bookmarks.extend(
                    {
                        "anchor_id": bookmark.anchor_id,
                        "label": bookmark.title,
                    }
                    for bookmark in enriched.bookmarks
                )
                reading_bookmarks.extend(
                    {
                        "anchor_id": bookmark.anchor_id,
                        "label": bookmark.label,
                    }
                    for bookmark in document_reading_bookmarks
                )
                documents.append(
                    {
                        "service": item.service,
                        "label": item.label,
                        "html": Markup(service_html),
                        "tone_label": item.tone_label,
                        "source_day_label": item.source_day_label,
                        "source_tone_label": item.source_tone_label,
                        "day_title": item.day_title,
                        "fetched_at": item.fetched_at,
                        "attachment_count": enriched.attachment_count,
                    }
                )

        return render_template(
            "index.html",
            calendar=calendar,
            selected_services=selected_services,
            documents=documents,
            tone=composition.tone if composition else None,
            attachment_count=attachment_count,
            music_bookmarks=music_bookmarks,
            reading_bookmarks=reading_bookmarks,
            unmatched_count=len(unmatched_piece_ids),
            error=error,
            melodos_url=MELODOS_HOME,
            ison_notes=ISON_NOTES,
            ison_numbers=sorted(media_library.ison_numbers),
            # Kihem is reverse-proxied below /kihem/.  Keep media URLs
            # relative so the browser requests /kihem/isokratis/... rather
            # than the unrelated /isokratis/... at the domain root.
            ison_url_template="isokratis/ison/__number__.mp3",
            prosomia_groups=tuple(
                {
                    "label": MODE_LABELS[mode],
                    "tracks": tuple(
                        {
                            "label": track.label,
                            "url": f"isokratis/prosomia/{quote(track.filename, safe='')}",
                        }
                        for track in tracks
                    ),
                }
                for mode, tracks in media_library.prosomia_by_mode()
            ),
        )

    @app.get("/isokratis/ison/<int:number>.mp3")
    def ison_audio(number: int):
        path = media_library.ison_path(number)
        if path is None:
            abort(404)
        return send_file(path, mimetype="audio/mpeg", max_age=86400)

    @app.get("/isokratis/prosomia/<path:filename>")
    def prosomia_audio(filename: str):
        path = media_library.prosomia_path(filename)
        if path is None:
            abort(404)
        mimetype = "audio/mp4" if path.suffix.lower() == ".m4a" else "audio/mpeg"
        return send_file(path, mimetype=mimetype, max_age=86400)

    @app.get("/melodos-audio")
    def melodos_audio():
        source_url = request.args.get("url", "")
        try:
            path = melodos_audio_cache.get(source_url)
        except InvalidMelodosAudioUrl:
            abort(400, description="Μη έγκυρη διεύθυνση ηχητικού Μελωδού.")
        except Exception as exc:
            app.logger.exception("Could not cache Melodos audio: %s", exc)
            abort(503, description="Το ηχητικό του Μελωδού δεν είναι προσωρινά διαθέσιμο.")
        return send_file(path, mimetype="audio/mpeg", max_age=31536000, conditional=True)

    @app.get("/music/<book_id>/<piece_id>/<int:part>.png")
    def music_excerpt(book_id: str, piece_id: str, part: int):
        try:
            output = music_renderer.render(book_id, piece_id, part)
        except KeyError:
            abort(404)
        except Exception as exc:
            app.logger.exception("Could not render Anastasimatarion excerpt: %s", exc)
            abort(503, description="Το μουσικό απόσπασμα δεν είναι προσωρινά διαθέσιμο.")
        return send_file(output, mimetype="image/png", max_age=86400)

    @app.get("/digital-scores")
    def digital_scores():
        """List verified scores as HTML for readers and JSON for API clients."""
        try:
            scores = digital_score_catalog.verified_scores()
        except ValueError as exc:
            app.logger.error("Could not load digital-score catalogue: %s", exc)
            abort(503, description="Ο κατάλογος ψηφιακών παρτιτούρων δεν είναι διαθέσιμος.")

        base_url = request.script_root.rstrip("/")
        if request.accept_mimetypes.best == "text/html":
            return render_template("digital_scores.html", scores=scores, base_url=base_url)
        return jsonify(
            [
                {
                    "id": score.score_id,
                    "title": score.title,
                    "incipit": score.incipit,
                    "tone": score.tone_label,
                    "source": score.source_description,
                    "reviewed_by": score.reviewed_by,
                    "assets": {
                        kind: f"{base_url}/digital-scores/{score.score_id}/{kind}"
                        for kind in ("byzx", "musicxml", "preview")
                        if digital_score_catalog.asset_path(score, kind) is not None
                    },
                }
                for score in scores
            ]
        )

    @app.get("/digital-scores/<score_id>")
    @app.get("/digital-scores/<score_id>/")
    def digital_score_page(score_id: str):
        """Show one public, verified digital score without source scans."""
        try:
            score = digital_score_catalog.get(score_id)
        except ValueError as exc:
            app.logger.error("Could not load digital-score catalogue: %s", exc)
            abort(503, description="Ο κατάλογος ψηφιακών παρτιτούρων δεν είναι διαθέσιμος.")
        if score is None or not score.is_verified:
            abort(404)
        base_url = request.script_root.rstrip("/")
        asset_urls = {
            kind: f"{base_url}/digital-scores/{score.score_id}/{kind}"
            for kind in ("byzx", "musicxml", "preview")
            if digital_score_catalog.asset_path(score, kind) is not None
        }
        neanes_dir = os.fspath(app.config["NEANES_WEB_DIR"])
        player_available = "byzx" in asset_urls and os.path.isfile(os.path.join(neanes_dir, "index.html"))
        response = Response(
            render_template(
                "digital_score_public.html",
                score=score,
                asset_urls=asset_urls,
                catalogue_url=f"{base_url}/digital-scores",
                player_available=player_available,
                neanes_url=f"{base_url}/digital-scores/neanes/app/",
                score_url=asset_urls.get("byzx"),
                note_labels=digital_score_catalog.note_labels(score),
            ),
            mimetype="text/html",
        )
        response.headers["Cache-Control"] = "no-store, max-age=0"
        return response

    @app.get("/digital-scores/<score_id>/<kind>")
    def digital_score_asset(score_id: str, kind: str):
        if kind not in {"byzx", "musicxml", "preview"}:
            abort(404)
        try:
            score = digital_score_catalog.get(score_id)
        except ValueError as exc:
            app.logger.error("Could not load digital-score catalogue: %s", exc)
            abort(503, description="Ο κατάλογος ψηφιακών παρτιτούρων δεν είναι διαθέσιμος.")
        if score is None or not score.is_verified:
            abort(404)
        path = digital_score_catalog.asset_path(score, kind)
        if path is None:
            abort(404)
        mimetype = {
            "byzx": "application/json",
            "musicxml": "application/vnd.recordare.musicxml+xml",
            "preview": "image/png",
        }[kind]
        return send_file(path, mimetype=mimetype, max_age=86400, conditional=True)

    @app.route("/review/digital-scores/<score_id>", methods=["GET", "POST"])
    @app.route("/review/digital-scores/<score_id>/", methods=["GET", "POST"])
    def digital_score_review(score_id: str):
        denied = require_review_access()
        if denied is not None:
            return denied
        try:
            score = digital_score_catalog.get(score_id)
        except ValueError as exc:
            app.logger.error("Could not load digital-score catalogue: %s", exc)
            abort(503, description="Ο κατάλογος ψηφιακών παρτιτούρων δεν είναι διαθέσιμος.")
        if score is None:
            abort(404)

        saved = False
        error = None
        review = digital_score_review_store.read(score_id)
        if request.method == "POST":
            reviewer = (request.form.get("reviewer") or "").strip()
            notes = (request.form.get("notes") or "").strip()
            if len(reviewer) < 2 or len(reviewer) > 160:
                error = "Γράψε το ονοματεπώνυμο ή την ιδιότητα του ελεγκτή (2–160 χαρακτήρες)."
            elif len(notes) > 8000:
                error = "Οι σημειώσεις δεν μπορούν να υπερβαίνουν τους 8.000 χαρακτήρες."
            else:
                checks = {check_id: check_id in request.form for check_id, _label in review_checks}
                review = digital_score_review_store.save(score_id, reviewer, checks, notes)
                saved = True

        # ``request.path`` is the application-internal path after Nginx has
        # removed ``/kihem``.  ``script_root`` restores that trusted mount
        # prefix for browser-facing asset and download URLs.
        base_asset_url = f"{request.script_root.rstrip('/')}{request.path.rstrip('/')}/asset"
        source_urls = tuple(
            f"{base_asset_url}/source?position={position}"
            for position in range(len(score.source_scan_filenames))
            if digital_score_catalog.source_scan_path(score, position) is not None
        )
        response = make_response(render_template(
            "digital_score_review.html",
            score=score,
            review=review,
            review_checks=review_checks,
            saved=saved,
            error=error,
            preview_url=f"{base_asset_url}/preview",
            ocr_url=f"{base_asset_url}/ocr",
            musicxml_url=f"{base_asset_url}/musicxml",
            byzx_url=f"{base_asset_url}/byzx",
            playback_url=f"{request.script_root.rstrip('/')}{request.path.rstrip('/')}/playback",
            has_preview=digital_score_catalog.asset_path(score, "preview") is not None,
            has_ocr=digital_score_catalog.asset_path(score, "ocr") is not None,
            has_musicxml=digital_score_catalog.asset_path(score, "musicxml") is not None,
            has_byzx=digital_score_catalog.asset_path(score, "byzx") is not None,
            source_urls=source_urls,
            form_reviewer=(request.form.get("reviewer") if request.method == "POST" else None)
            or (review.get("reviewer", "") if review else ""),
            form_notes=(request.form.get("notes") if request.method == "POST" else None)
            or (review.get("notes", "") if review else ""),
        ))
        response.headers["Cache-Control"] = "no-store, max-age=0"
        return response

    @app.get("/review/digital-scores/<score_id>/asset/<kind>")
    def digital_score_review_asset(score_id: str, kind: str):
        denied = require_review_access()
        if denied is not None:
            return denied
        try:
            score = digital_score_catalog.get(score_id)
        except ValueError as exc:
            app.logger.error("Could not load digital-score catalogue: %s", exc)
            abort(503, description="Ο κατάλογος ψηφιακών παρτιτούρων δεν είναι διαθέσιμος.")
        if score is None:
            abort(404)
        if kind == "source":
            try:
                position = int(request.args.get("position", "0"))
            except ValueError:
                abort(404)
            path = digital_score_catalog.source_scan_path(score, position)
            mimetype = "image/png"
        elif kind in {"byzx", "ocr", "musicxml", "preview"}:
            path = digital_score_catalog.asset_path(score, kind)
            mimetype = {
                "byzx": "application/json",
                "ocr": "application/yaml",
                "musicxml": "application/vnd.recordare.musicxml+xml",
                "preview": "image/png",
            }[kind]
        else:
            abort(404)
        if path is None:
            abort(404)
        response = send_file(path, mimetype=mimetype, max_age=0, conditional=True)
        response.headers["Cache-Control"] = "no-store, max-age=0"
        return response

    @app.get("/review/digital-scores/<score_id>/playback")
    @app.get("/review/digital-scores/<score_id>/playback/")
    def digital_score_playback(score_id: str):
        """Embed the unmodified Neanes web player for one protected score."""
        denied = require_review_access()
        if denied is not None:
            return denied
        try:
            score = digital_score_catalog.get(score_id)
        except ValueError as exc:
            app.logger.error("Could not load digital-score catalogue: %s", exc)
            abort(503, description="Ο κατάλογος ψηφιακών παρτιτούρων δεν είναι διαθέσιμος.")
        if score is None or digital_score_catalog.asset_path(score, "byzx") is None:
            abort(404)
        neanes_dir = os.fspath(app.config["NEANES_WEB_DIR"])
        if not os.path.isfile(os.path.join(neanes_dir, "index.html")):
            abort(503, description="Ο ιδιωτικός player Neanes δεν έχει εγκατασταθεί ακόμη.")

        review_url = f"{request.script_root.rstrip('/')}/review/digital-scores/{score_id}"
        byzx_path = digital_score_catalog.asset_path(score, "byzx")
        assert byzx_path is not None
        asset_version = byzx_path.stat().st_mtime_ns
        response = make_response(render_template(
            "digital_score_playback.html",
            score=score,
            embedded=request.args.get("embedded") == "1",
            review_url=review_url,
            neanes_url=f"{request.script_root.rstrip('/')}/review/neanes/app/",
            score_url=f"{review_url}/asset/byzx?v={asset_version}",
            # Neanes persists documents by filename.  A stable filename makes
            # a new private draft look like the old tab, even after the score
            # URL is cache-busted.  Tie it to the asset version as well.
            score_filename=f"{score.score_id}-{asset_version}.byzx",
            note_labels=digital_score_catalog.note_labels(score),
        ))
        response.headers["Cache-Control"] = "no-store, max-age=0"
        return response

    @app.get("/review/neanes/app/")
    @app.get("/review/neanes/app/<path:filename>")
    def neanes_web_app(filename: str = "index.html"):
        """Serve the private, unmodified Neanes web build on the Kihem origin."""
        denied = require_review_access()
        if denied is not None:
            return denied
        directory = os.fspath(app.config["NEANES_WEB_DIR"])
        if not os.path.isfile(os.path.join(directory, "index.html")):
            abort(503, description="Ο ιδιωτικός player Neanes δεν έχει εγκατασταθεί ακόμη.")
        return send_from_directory(directory, filename, conditional=True, max_age=86400)

    @app.get("/digital-scores/neanes/app/")
    @app.get("/digital-scores/neanes/app/<path:filename>")
    def public_neanes_web_app(filename: str = "index.html"):
        """Serve the GPL Neanes app for public verified-score playback only.

        The installed build was compiled for the authenticated review path.
        Text assets are rewritten only at delivery so its own asset and PWA
        URLs stay beneath this public player path. This route never serves a
        score itself; the public score page fetches only a verified `.byzx`.
        """
        directory = os.fspath(app.config["NEANES_WEB_DIR"])
        root = os.path.realpath(directory)
        target = os.path.realpath(os.path.join(directory, filename))
        if not os.path.isfile(os.path.join(directory, "index.html")):
            abort(503, description="Ο player Neanes δεν έχει εγκατασταθεί ακόμη.")
        if target != root and not target.startswith(root + os.sep):
            abort(404)
        if not os.path.isfile(target):
            abort(404)

        text_mimetypes = {
            ".html": "text/html",
            ".js": "application/javascript",
            ".css": "text/css",
            ".json": "application/json",
            ".webmanifest": "application/manifest+json",
            ".svg": "image/svg+xml",
        }
        suffix = os.path.splitext(target)[1].lower()
        if suffix not in text_mimetypes:
            return send_from_directory(directory, filename, conditional=True, max_age=86400)

        private_base = f"{request.script_root.rstrip('/')}/review/neanes/app/"
        public_base = f"{request.script_root.rstrip('/')}/digital-scores/neanes/app/"
        try:
            with open(target, encoding="utf-8") as source:
                content = source.read().replace(private_base, public_base)
        except OSError:
            abort(404)
        return Response(content, mimetype=text_mimetypes[suffix], headers={"Cache-Control": "public, max-age=86400"})

    @app.get("/health")
    def health():
        return {"status": "ok", "calendar": "gregorian", "services": ["orthros", "litourgia"]}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
