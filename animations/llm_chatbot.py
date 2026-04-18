from manim import *

BRAND_BLUE = "#3B82F6"
BRAND_PURPLE = "#8B5CF6"
BRAND_GREEN = "#10B981"
BRAND_ORANGE = "#F59E0B"
BRAND_RED = "#EF4444"
DARK_BG = "#0F172A"
CARD_BG = "#1E293B"


# ─── Scene 1 : User types a message ───────────────────────────────────────────
class Scene1_UserInput(Scene):
    def construct(self):
        self.camera.background_color = DARK_BG

        title = Text("1 · L'utilisateur écrit un message",
                     font_size=32, color=WHITE).to_edge(UP, buff=0.5)
        self.play(Write(title))

        # Chat bubble
        bubble_rect = RoundedRectangle(
            corner_radius=0.3, width=9, height=1.5,
            fill_color=CARD_BG, fill_opacity=1,
            stroke_color=BRAND_BLUE, stroke_width=2
        ).shift(UP * 0.5)

        label = Text("User", font_size=18, color=BRAND_BLUE).next_to(bubble_rect, UP, buff=0.1).align_to(bubble_rect, LEFT).shift(RIGHT * 0.3)

        msg_text = Text('"Explique-moi comment fonctionne un LLM"',
                        font_size=22, color=WHITE).move_to(bubble_rect)

        cursor = Rectangle(width=0.03, height=0.35, fill_color=WHITE,
                           fill_opacity=1, stroke_width=0).next_to(msg_text, RIGHT, buff=0.05)

        self.play(FadeIn(bubble_rect), Write(label))
        self.play(AddTextLetterByLetter(msg_text, time_per_char=0.04),
                  run_time=2)
        self.play(FadeIn(cursor))
        self.play(FadeOut(cursor))
        self.wait(1.5)

        enter_key = RoundedRectangle(
            corner_radius=0.1, width=1.6, height=0.5,
            fill_color=BRAND_GREEN, fill_opacity=1, stroke_width=0
        ).shift(DOWN * 1.5 + RIGHT * 3.5)
        enter_label = Text("Envoyer ↵", font_size=16, color=WHITE).move_to(enter_key)
        self.play(FadeIn(enter_key), Write(enter_label))
        self.play(enter_key.animate.scale(0.92), rate_func=there_and_back, run_time=0.3)

        arrow_out = Arrow(start=bubble_rect.get_bottom(), end=bubble_rect.get_bottom() + DOWN * 1,
                          color=BRAND_BLUE, stroke_width=3)
        next_label = Text("→ Le modèle reçoit le texte brut",
                          font_size=20, color=BRAND_BLUE).next_to(arrow_out, DOWN, buff=0.15)
        self.play(GrowArrow(arrow_out), Write(next_label))
        self.wait(2)


# ─── Scene 2 : Tokenisation ───────────────────────────────────────────────────
class Scene2_Tokenization(Scene):
    def construct(self):
        self.camera.background_color = DARK_BG

        title = Text("2 · Tokenisation", font_size=32, color=WHITE).to_edge(UP, buff=0.5)
        self.play(Write(title))

        raw = Text('"Explique-moi comment fonctionne un LLM"',
                   font_size=20, color=GRAY).shift(UP * 2)
        self.play(FadeIn(raw))
        self.wait(0.5)

        tokens_str = ["Expli", "que", "-moi", " comment", " fon", "ctionne", " un", " LLM"]
        colors = [BRAND_BLUE, BRAND_PURPLE, BRAND_GREEN, BRAND_ORANGE,
                  BRAND_RED, "#06B6D4", "#EC4899", "#84CC16"]
        token_ids = [15043, 482, 12, 4724, 1312, 1791, 443, 9468]

        # Token boxes row
        boxes = VGroup()
        for tok, col in zip(tokens_str, colors):
            box = RoundedRectangle(
                corner_radius=0.15,
                width=max(len(tok) * 0.18 + 0.5, 1.0),
                height=0.6,
                fill_color=col, fill_opacity=0.25,
                stroke_color=col, stroke_width=2
            )
            label = Text(tok, font_size=16, color=col).move_to(box)
            boxes.add(VGroup(box, label))

        boxes.arrange(RIGHT, buff=0.15).shift(UP * 0.5)

        self.play(
            raw.animate.set_opacity(0.3),
            LaggedStart(*[FadeIn(b, shift=DOWN * 0.3) for b in boxes], lag_ratio=0.12),
            run_time=1.8
        )

        # Token IDs below
        id_label = Text("Token IDs (vocabulaire GPT-4) :", font_size=18,
                        color=GRAY).shift(DOWN * 0.6).align_to(boxes, LEFT)
        self.play(FadeIn(id_label))

        id_boxes = VGroup()
        for (b, tok_grp), tid, col in zip(enumerate(boxes), token_ids, colors):
            rect = SurroundingRectangle(boxes[b], color=col, buff=0.05, stroke_width=1)
            id_txt = Text(str(tid), font_size=14, color=col)
            id_txt.move_to(boxes[b].get_center() + DOWN * 1.4)
            id_boxes.add(VGroup(rect, id_txt))

        self.play(
            LaggedStart(*[FadeIn(ib) for ib in id_boxes], lag_ratio=0.1),
            run_time=1.5
        )

        note = Text("Chaque token = un sous-mot du vocabulaire (~100k entrées)",
                    font_size=17, color=LIGHT_GRAY).shift(DOWN * 2.4)
        self.play(Write(note))
        self.wait(2.5)


# ─── Scene 3 : Embeddings ─────────────────────────────────────────────────────
class Scene3_Embeddings(Scene):
    def construct(self):
        self.camera.background_color = DARK_BG

        title = Text("3 · Token → Vecteur (Embedding)",
                     font_size=32, color=WHITE).to_edge(UP, buff=0.5)
        self.play(Write(title))

        # Show 3 tokens transforming into vectors
        sample_tokens = [("Expli", BRAND_BLUE, [0.21, -0.83, 0.44, 0.12]),
                         ("-moi",  BRAND_GREEN, [-0.55, 0.31, 0.78, -0.20]),
                         ("LLM",   "#84CC16",   [0.91, 0.07, -0.38, 0.63])]

        for i, (tok, col, vec) in enumerate(sample_tokens):
            x_off = (i - 1) * 3.5

            # Token box
            box = RoundedRectangle(corner_radius=0.15, width=1.4, height=0.6,
                                   fill_color=col, fill_opacity=0.2,
                                   stroke_color=col, stroke_width=2).shift(UP * 1.5 + RIGHT * x_off)
            tok_label = Text(tok, font_size=18, color=col).move_to(box)
            self.play(FadeIn(box, tok_label), run_time=0.4)

            # Arrow
            arr = Arrow(box.get_bottom(), box.get_bottom() + DOWN * 0.8,
                        color=col, stroke_width=2)
            self.play(GrowArrow(arr), run_time=0.3)

            # Vector bars
            bar_group = VGroup()
            for j, v in enumerate(vec):
                bar_h = abs(v) * 1.2
                bar = Rectangle(width=0.25, height=bar_h,
                                fill_color=col if v > 0 else RED,
                                fill_opacity=0.8, stroke_width=0)
                bar.shift(RIGHT * (j * 0.32 - 0.48) + DOWN * 0.4 + RIGHT * x_off)
                if v < 0:
                    bar.flip()
                bar_group.add(bar)

            bar_bg = SurroundingRectangle(bar_group, color=col,
                                          buff=0.15, stroke_width=1,
                                          fill_color=CARD_BG, fill_opacity=1)
            bar_bg.set_z_index(-1)

            val_str = "[" + ", ".join(f"{v:.2f}" for v in vec) + ", ...]"
            val_text = Text(val_str, font_size=11, color=col).next_to(bar_group, DOWN, buff=0.15)

            self.play(FadeIn(bar_bg), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bar_group], lag_ratio=0.1), run_time=0.6)
            self.play(Write(val_text), run_time=0.4)

        dim_note = Text("768 à 4096 dimensions selon le modèle",
                        font_size=17, color=GRAY).shift(DOWN * 2.8)
        pos_note = Text("+ Positional Encoding : on ajoute la position du token dans la phrase",
                        font_size=16, color=GRAY).shift(DOWN * 3.3)
        self.play(Write(dim_note))
        self.play(Write(pos_note))
        self.wait(2.5)


# ─── Scene 4 : Self-Attention ─────────────────────────────────────────────────
class Scene4_Attention(Scene):
    def construct(self):
        self.camera.background_color = DARK_BG

        title = Text("4 · Transformer — Self-Attention",
                     font_size=32, color=WHITE).to_edge(UP, buff=0.5)
        self.play(Write(title))

        subtitle = Text("Chaque token calcule un score d'attention avec tous les autres",
                        font_size=17, color=GRAY).next_to(title, DOWN, buff=0.2)
        self.play(FadeIn(subtitle))

        tokens = ["Expli", "que", "-moi", "comment", "fonc…", "un", "LLM"]
        N = len(tokens)

        # Attention matrix — rows = "qui regarde", cols = "vers qui"
        # Scores simulés (softmax appliqué mentalement, somme ≈ 1 par ligne)
        attn = [
            [0.60, 0.15, 0.08, 0.07, 0.04, 0.03, 0.03],  # Expli → très fort sur lui-même
            [0.18, 0.42, 0.14, 0.12, 0.07, 0.04, 0.03],  # que
            [0.10, 0.14, 0.38, 0.18, 0.09, 0.07, 0.04],  # -moi
            [0.06, 0.10, 0.12, 0.45, 0.14, 0.08, 0.05],  # comment
            [0.04, 0.07, 0.08, 0.18, 0.40, 0.14, 0.09],  # fonc…
            [0.03, 0.05, 0.07, 0.12, 0.16, 0.38, 0.19],  # un
            [0.03, 0.12, 0.05, 0.22, 0.18, 0.10, 0.30],  # LLM → fort sur "comment" et lui-même
        ]

        cell_size = 0.72
        grid_w = N * cell_size
        grid_h = N * cell_size
        origin = LEFT * (grid_w / 2) + DOWN * 0.15

        # Draw heatmap cells
        cells = []
        for r in range(N):
            row_cells = []
            for c in range(N):
                score = attn[r][c]
                # Color: dark blue (low) → bright green (high)
                t = score ** 0.5  # gamma for better visual contrast
                cell_color = interpolate_color(
                    color1=ManimColor("#0F2040"),
                    color2=ManimColor("#10B981"),
                    alpha=t
                )
                rect = Rectangle(
                    width=cell_size - 0.04, height=cell_size - 0.04,
                    fill_color=cell_color, fill_opacity=1,
                    stroke_color="#1E293B", stroke_width=1
                )
                rect.move_to(origin + RIGHT * (c + 0.5) * cell_size + DOWN * (r + 0.5) * cell_size)

                pct = int(score * 100)
                val = Text(f"{pct}%", font_size=11,
                           color=WHITE if score > 0.15 else "#334155")
                val.move_to(rect)
                row_cells.append(VGroup(rect, val))
            cells.append(row_cells)

        # Token labels — columns (top)
        col_labels = VGroup()
        for c, tok in enumerate(tokens):
            lbl = Text(tok, font_size=12, color=GRAY)
            lbl.move_to(origin + RIGHT * (c + 0.5) * cell_size + UP * 0.45)
            col_labels.add(lbl)

        # Token labels — rows (left)
        row_labels = VGroup()
        for r, tok in enumerate(tokens):
            lbl = Text(tok, font_size=12, color=GRAY)
            lbl.next_to(origin + DOWN * (r + 0.5) * cell_size, LEFT, buff=0.15)
            row_labels.add(lbl)

        axis_q = Text("← regarde", font_size=11, color="#475569").rotate(PI / 2)
        axis_q.next_to(row_labels, LEFT, buff=0.1)
        axis_k = Text("vers →", font_size=11, color="#475569")
        axis_k.next_to(col_labels, UP, buff=0.05)

        self.play(FadeIn(col_labels), FadeIn(row_labels), run_time=0.6)
        self.play(FadeIn(axis_q), FadeIn(axis_k), run_time=0.4)

        # Animate rows one by one
        for r in range(N):
            self.play(
                LaggedStart(*[FadeIn(cells[r][c]) for c in range(N)], lag_ratio=0.05),
                run_time=0.5
            )

        self.wait(0.5)

        # Highlight last row (LLM) with a border
        highlight = Rectangle(
            width=grid_w - 0.04, height=cell_size - 0.04,
            stroke_color=BRAND_GREEN, stroke_width=2.5, fill_opacity=0
        )
        highlight.move_to(origin + RIGHT * grid_w / 2 + DOWN * (N - 0.5) * cell_size)
        focus_label = Text(
            '"LLM" s\'attend fortement sur "comment" (22%) et lui-même (30%)',
            font_size=14, color=BRAND_GREEN
        ).shift(DOWN * 3.3)
        self.play(Create(highlight), Write(focus_label), run_time=0.8)
        self.wait(1.2)

        layers = Text("→ Ce calcul se répète sur N couches en parallèle (GPT-4 : 96 couches)",
                      font_size=14, color=BRAND_BLUE).shift(DOWN * 3.8)
        self.play(Write(layers))
        self.wait(2.5)


# ─── Scene 5 : Output & Génération ────────────────────────────────────────────
class Scene5_Generation(Scene):
    def construct(self):
        self.camera.background_color = DARK_BG

        title = Text("5 · Sélection du token & Génération",
                     font_size=32, color=WHITE).to_edge(UP, buff=0.5)
        self.play(Write(title))

        # Probability bars for next token candidates
        candidates = [("L'", 0.41), ("Un", 0.22), ("Le", 0.18),
                      ("Les", 0.09), ("Ce", 0.06), ("…", 0.04)]
        bar_colors = [BRAND_GREEN, BRAND_BLUE, BRAND_PURPLE,
                      BRAND_ORANGE, BRAND_RED, GRAY]

        prob_title = Text("Distribution de probabilité — prochain token :",
                          font_size=18, color=GRAY).shift(UP * 2)
        self.play(Write(prob_title))

        bar_groups = VGroup()
        for i, ((word, prob), col) in enumerate(zip(candidates, bar_colors)):
            x = -4.5 + i * 1.6
            bar_h = prob * 4
            bar = Rectangle(width=1.0, height=bar_h,
                            fill_color=col, fill_opacity=0.85, stroke_width=0)
            bar.align_to(ORIGIN + DOWN * 0.3, DOWN)
            bar.shift(RIGHT * x)

            word_label = Text(word, font_size=16, color=col).next_to(bar, DOWN, buff=0.1)
            pct_label = Text(f"{int(prob*100)}%", font_size=14, color=col).next_to(bar, UP, buff=0.1)

            bar_groups.add(VGroup(bar, word_label, pct_label))

        self.play(
            LaggedStart(*[GrowFromEdge(bg, DOWN) for bg in bar_groups], lag_ratio=0.12),
            run_time=1.5
        )

        # Highlight winning token
        win_box = SurroundingRectangle(bar_groups[0], color=BRAND_GREEN,
                                       stroke_width=3, buff=0.1)
        win_text = Text("✓ Sélectionné : \"L'\"", font_size=20,
                        color=BRAND_GREEN).shift(DOWN * 2.3)
        self.play(Create(win_box), Write(win_text))
        self.wait(0.8)

        # Autoregressive generation
        gen_title = Text("Génération autorégressive — mot par mot :",
                         font_size=18, color=GRAY).shift(DOWN * 2.9)
        self.play(Write(gen_title))

        words = ["L'", "IA", "est", "un", "système", "qui...", ""]
        response_text = ""
        response_mob = None

        for w in words:
            response_text += w + (" " if w else "")
            new_mob = Text(response_text.strip(), font_size=22,
                           color=WHITE).shift(DOWN * 3.6)
            if response_mob is None:
                self.play(FadeIn(new_mob), run_time=0.3)
            else:
                self.play(Transform(response_mob, new_mob), run_time=0.25)
                self.remove(response_mob)
            response_mob = new_mob

        self.wait(2)


# ─── Full movie (all 5 scenes chained) ────────────────────────────────────────
class LLMChatbotFull(Scene):
    """Run this class to render the complete animation."""

    def construct(self):
        self.camera.background_color = DARK_BG
        for SceneClass in [Scene1_UserInput, Scene2_Tokenization,
                            Scene3_Embeddings, Scene4_Attention,
                            Scene5_Generation]:
            SceneClass.construct(self)
            self.clear()
            self.wait(0.3)
