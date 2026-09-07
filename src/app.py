from __future__ import annotations

import os

from flask import Flask, abort, render_template, request, send_file
from markupsafe import Markup

from src.anastasimatarion import (
    AnastasimatarionRenderer,
    catalog_books,
    enrich_service_html,
)
from src.composer import ServiceComposer
from src.liturgical_calendar import LiturgicalCalendar
from src.melodos import MELODOS_HOME, MelodosClient, MelodosError


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(
        CACHE_DIR=os.environ.get("KIHEM_CACHE_DIR", "/tmp/kihem-cache"),
        BOOKS_DIR=os.environ.get("KIHEM_BOOKS_DIR", "/var/lib/kihem/books"),
        DEFAULT_DATE="2026-09-13",
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

    @app.get("/")
    def index():
        selected_raw = request.args.get("date", app.config["DEFAULT_DATE"])
        selected_services = request.args.get("services", "both")
        refresh = request.args.get("refresh") == "1"
        error = None
        composition = None
        attachment_count = 0
        unmatched_piece_ids: list[str] = []

        try:
            calendar = LiturgicalCalendar(selected_raw)
        except (ValueError, TypeError):
            calendar = LiturgicalCalendar(app.config["DEFAULT_DATE"])
            error = "Η ημερομηνία δεν είναι έγκυρη. Χρησιμοποίησε τη μορφή ΕΕΕΕ-ΜΜ-ΗΗ."

        if not error:
            services = {
                "orthros": ("orthros",),
                "litourgia": ("litourgia",),
                "both": ("orthros", "litourgia"),
            }.get(selected_services, ("orthros", "litourgia"))
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
                    composition.selected_date, item.service, item.service_html
                )
                attachment_count += enriched.attachment_count
                unmatched_piece_ids.extend(enriched.unmatched_piece_ids)
                documents.append(
                    {
                        "service": item.service,
                        "label": item.label,
                        "html": Markup(enriched.html),
                        "tone_label": item.tone_label,
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
            unmatched_count=len(unmatched_piece_ids),
            music_books=catalog_books(),
            error=error,
            melodos_url=MELODOS_HOME,
        )

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
