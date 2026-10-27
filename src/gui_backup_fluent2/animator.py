import customtkinter as ctk

def _parse_hex(hex_str: str):
    """Parses a hex color string like #007AFF or #FFF into an (R, G, B) tuple."""
    hex_str = str(hex_str).lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    if len(hex_str) != 6:
        return (128, 128, 128)
    try:
        return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
    except Exception:
        return (128, 128, 128)

def _rgb_to_hex(rgb_tuple):
    """Converts an (R, G, B) tuple to a #RRGGBB hex string."""
    r = max(0, min(255, int(rgb_tuple[0])))
    g = max(0, min(255, int(rgb_tuple[1])))
    b = max(0, min(255, int(rgb_tuple[2])))
    return f"#{r:02x}{g:02x}{b:02x}"

def _lerp_color(c1, c2, t: float):
    """Linearly interpolates between two RGB colors by factor t (0.0 to 1.0)."""
    return (
        c1[0] + (c2[0] - c1[0]) * t,
        c1[1] + (c2[1] - c1[1]) * t,
        c1[2] + (c2[2] - c1[2]) * t
    )

def _get_mode_color(color_spec):
    """Resolves light/dark tuple based on current appearance mode."""
    if isinstance(color_spec, (tuple, list)):
        mode = ctk.get_appearance_mode().lower()
        return color_spec[1] if mode == "dark" else color_spec[0]
    return str(color_spec)


class UIAnimator:
    """
    Lightweight, high-performance UI micro-animations engine for CustomTkinter.
    Focuses exclusively on buttery-smooth RGB color crossfades on button hover
    and gentle click dimming without causing any layout redraws or stutter.
    """

    @classmethod
    def attach_smooth_hover(cls, button: ctk.CTkButton, normal_color=None, hover_color=None, pressed_color=None, duration_ms: int = 120, steps: int = 5):
        """
        Attaches a smooth RGB color fade transition to a CTkButton on mouse enter, leave, press, and release.
        """
        n_spec = normal_color or button.cget("fg_color")
        h_spec = hover_color or button.cget("hover_color")

        # If already attached to this button, simply update target colors and return!
        if hasattr(button, "_anim_state"):
            button._anim_state["n_spec"] = n_spec
            button._anim_state["h_spec"] = h_spec
            if pressed_color:
                button._anim_state["p_spec"] = pressed_color
            button._anim_state["current_rgb"] = None
            return

        # Disable CTk's default abrupt color pop if supported
        try:
            if hasattr(button, "_hover"):
                button.configure(hover=False)
        except Exception:
            pass

        state = {
            "n_spec": n_spec,
            "h_spec": h_spec,
            "p_spec": pressed_color,
            "current_rgb": None,
            "target_rgb": None,
            "after_id": None,
            "is_hovered": False,
            "is_pressed": False
        }
        button._anim_state = state

        step_delay = max(15, duration_ms // steps)

        def get_current_normal():
            raw = _get_mode_color(state["n_spec"])
            if raw == "transparent":
                mode = ctk.get_appearance_mode().lower()
                return (28, 28, 30) if mode == "dark" else (242, 242, 247)
            return _parse_hex(raw)

        def get_current_hover():
            raw = _get_mode_color(state["h_spec"])
            if raw == "transparent":
                mode = ctk.get_appearance_mode().lower()
                return (44, 44, 46) if mode == "dark" else (229, 229, 234)
            return _parse_hex(raw)

        def get_current_pressed():
            if state["p_spec"]:
                return _parse_hex(_get_mode_color(state["p_spec"]))
            h_rgb = get_current_hover()
            # Subtle 16% dimming on press for tactile feedback
            return (int(h_rgb[0] * 0.84), int(h_rgb[1] * 0.84), int(h_rgb[2] * 0.84))

        def animate_to(target_rgb):
            if state["after_id"]:
                try:
                    button.after_cancel(state["after_id"])
                except Exception:
                    pass
                state["after_id"] = None

            if state["current_rgb"] is None:
                state["current_rgb"] = get_current_normal()

            start_rgb = state["current_rgb"]
            state["target_rgb"] = target_rgb

            def step(i):
                if i > steps:
                    state["current_rgb"] = target_rgb
                    try:
                        button.configure(fg_color=_rgb_to_hex(target_rgb))
                    except Exception:
                        pass
                    state["after_id"] = None
                    return

                t = i / float(steps)
                # Smooth quadratic ease-out
                eased_t = t * (2.0 - t)
                curr = _lerp_color(start_rgb, target_rgb, eased_t)
                state["current_rgb"] = curr
                try:
                    button.configure(fg_color=_rgb_to_hex(curr))
                    state["after_id"] = button.after(step_delay, lambda: step(i + 1))
                except Exception:
                    state["after_id"] = None

            step(1)

        def on_enter(event):
            state["is_hovered"] = True
            if not state["is_pressed"]:
                animate_to(get_current_hover())

        def on_leave(event):
            state["is_hovered"] = False
            state["is_pressed"] = False
            animate_to(get_current_normal())

        def on_press(event):
            state["is_pressed"] = True
            animate_to(get_current_pressed())

        def on_release(event):
            state["is_pressed"] = False
            if state["is_hovered"]:
                animate_to(get_current_hover())
            else:
                animate_to(get_current_normal())

        button.bind("<Enter>", on_enter, add="+")
        button.bind("<Leave>", on_leave, add="+")
        button.bind("<Button-1>", on_press, add="+")
        button.bind("<ButtonRelease-1>", on_release, add="+")
