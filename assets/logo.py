from __future__ import annotations

import sys

try:
    from manim import *
    from manim.utils.color.BS381 import BEIGE
except ImportError:
    print("Seems you don't have Manim installed...")
    print("You can install it by following the instructions at")
    print("https://docs.manim.community/en/stable/installation.html")
    exit(1)


class Logo(Scene):
    def construct(self):
        name = Tex("TJ CSL").scale(1.5)
        full = Tex("Turn-In").scale(3)
        VGroup(name, full).arrange(DOWN)

        subtext = Text("TJHSST's Code Autograder", color=BEIGE).next_to(full, DOWN, buff=2)

        name.to_edge(RIGHT).shift(RIGHT * name.width)
        full.to_edge(LEFT).shift(LEFT * full.width)
        self.play(
            name.animate(rate_func=rate_functions.ease_out_bounce).set_x(0).set_color(GREEN),
            full.animate(rate_func=rate_functions.ease_out_bounce).set_x(0).set_color(BEIGE),
        )
        self.play(Create(subtext))
        self.wait(4)
        self.play(Uncreate(VGroup(name, full, subtext)), run_time=1)
        self.wait(0.1)


def main():
    args: dict[str, bool | str] = {"preview": True}
    DEBUG = "--final" in sys.argv
    if not DEBUG:
        args["format"] = "gif"
        args["transparent"] = True
    with tempconfig(args):
        Logo().render()


if __name__ == "__main__":
    main()
