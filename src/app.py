from __future__ import annotations

import os

from flask import Flask, abort, render_template, request, send_file, url_for
from markupsafe import Markup

from src.anastasimatarion import (
    AnastasimatarionRenderer,
    enrich_service_html,
)
from src.composer import ServiceComposer
from src.liturgical_calendar import LiturgicalCalendar
from src.melodos import MELODOS_HOME, MelodosClient, MelodosError
from src.isokratis import ISON_NOTES, MODE_LABELS, IsokratisLibrary


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(
        CACHE_DIR=os.environ.get("KIHEM_CACHE_DIR", "/tmp/kihem-cache"),
        BOOKS_DIR=os.environ.get("KIHEM_BOOKS_DIR", "/var/lib/kihem/books"),
        BYZ_DIR=os.environ.get("KIHEM_BYZ_DIR", "/var/lib/kihem/byz"),
        DEFAULT_DATE="2026-09-09",
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
    media_library = app.config.get("ISOKRATIS_LIBRARY") or IsokratisLibrary(
        app.config["BYZ_DIR"]
    )
    app.extensions["kihem_isokratis_library"] = media_library

    @app.get("/")
    def index():
        selected_raw = request.args.get("date", app.config["DEFAULT_DATE"])
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

        try:
            calendar = LiturgicalCalendar(selected_raw)
        except (ValueError, TypeError):
            calendar = LiturgicalCalendar(app.config["DEFAULT_DATE"])
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
                )
                attachment_count += enriched.attachment_count
                unmatched_piece_ids.extend(enriched.unmatched_piece_ids)
                music_bookmarks.extend(
                    {
                        "anchor_id": bookmark.anchor_id,
                        "label": f"{item.label} · {bookmark.title}",
                    }
                    for bookmark in enriched.bookmarks
                )
                documents.append(
                    {
                        "service": item.service,
                        "label": item.label,
                        "html": Markup(enriched.html),
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
            unmatched_count=len(unmatched_piece_ids),
            error=error,
            melodos_url=MELODOS_HOME,
            ison_notes=ISON_NOTES,
            ison_numbers=sorted(media_library.ison_numbers),
            prosomia_groups=tuple(
                {
                    "label": MODE_LABELS[mode],
                    "tracks": tuple(
                        {
                            "label": track.label,
                            "url": url_for("prosomia_audio", filename=track.filename),
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
        return send_file(path, mimetype="audio/mpeg", max_age=86400)

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

    @app.get("/health")
    def health():
        return {"status": "ok", "calendar": "gregorian", "services": ["orthros", "litourgia"]}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
