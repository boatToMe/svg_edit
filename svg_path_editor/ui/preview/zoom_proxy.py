class PreviewZoomProxy:
    def __init__(self, preview, renderer, padding: int = 24):
        self.preview = preview
        self.renderer = renderer
        self.padding = padding
        self.target_width_px: int | None = None
        self.zoom_multiplier = 1.0

    def reset(self):
        self.target_width_px = None
        self.zoom_multiplier = 1.0

    def ensure_default_target_width(self, session):
        if self.target_width_px is not None and self.target_width_px > 0:
            return self.target_width_px
        viewport_width, viewport_height = self.preview.get_preview_viewport_size()
        _min_x, _min_y, width, height = self.renderer.get_bounds(session)
        if viewport_width > 0 and viewport_height > 0:
            usable_width = max(1, viewport_width - self.padding * 2)
            usable_height = max(1, viewport_height - self.padding * 2)
            aspect = width / max(height, 1.0)
            fit_width = min(usable_width, int(round(usable_height * aspect)))
            self.target_width_px = max(64, fit_width)
        else:
            self.target_width_px = max(64, int(round(width)))
        self.preview.set_target_width(self.target_width_px)
        return self.target_width_px

    def apply_target_width(self, width_px: int):
        self.target_width_px = max(1, int(round(width_px)))
        self.zoom_multiplier = 1.0
        self.preview.set_target_width(self.target_width_px)

    def scale_by(self, factor: float, session):
        self.ensure_default_target_width(session)
        self.zoom_multiplier = max(0.1, min(16.0, self.zoom_multiplier * factor))

    def get_render_args(self, session):
        width_px = self.ensure_default_target_width(session)
        return width_px, self.zoom_multiplier
