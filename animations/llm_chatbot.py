from manim import *

BRAND_BLUE = "#3B82F6"
BRAND_PURPLE = "#8B5CF6"
BRAND_GREEN = "#10B981"
BRAND_ORANGE = "#F59E0B"
BRAND_RED = "#EF4444"
DARK_BG = "#0F172A"
CARD_BG = "#1E293B"

TEXTS = {
    "fr": {
        "s1_title":   "1 · L'utilisateur écrit un message",
        "s1_msg":     '"Explique-moi comment fonctionne un LLM"',
        "s1_send":    "Envoyer ↵",
        "s1_note":    "→ Le modèle reçoit le texte brut",
        "s2_title":   "2 · Tokenisation",
        "s2_raw":     '"Explique-moi comment fonctionne un LLM"',
        "s2_tokens":  ["Expli", "que", "-moi", " comment", " fon", "ctionne", " un", " LLM"],
        "s2_ids":     "Token IDs (vocabulaire GPT-4) :",
        "s2_note":    "Chaque token = un sous-mot du vocabulaire (~100k entrées)",
        "s3_title":   "3 · Token → Vecteur (Embedding)",
        "s3_tokens":  [("Expli", BRAND_BLUE), ("-moi", BRAND_GREEN), ("LLM", "#84CC16")],
        "s3_dim":     "768 à 4096 dimensions selon le modèle",
        "s3_pos":     "+ Positional Encoding : on ajoute la position du token dans la phrase",
        "s4_title":   "4 · Transformer — Self-Attention",
        "s4_sub":     "Chaque token calcule un score d'attention avec tous les autres",
        "s4_tokens":  ["Expli", "que", "-moi", "comment", "fonc…", "un", "LLM"],
        "s4_axis_q":  "← regarde",
        "s4_axis_k":  "vers →",
        "s4_focus":   '"LLM" s\'attend fortement sur "comment" (22%) et lui-même (30%)',
        "s4_layers":  "→ Ce calcul se répète sur N couches en parallèle (GPT-4 : 96 couches)",
        "s5_title":   "5 · Sélection du token & Génération",
        "s5_prob":    "Distribution de probabilité — prochain token :",
        "s5_cands":   [("L'", 0.41), ("Un", 0.22), ("Le", 0.18), ("Les", 0.09), ("Ce", 0.06), ("…", 0.04)],
        "s5_win":     '✓ Sélectionné : "L\'"',
        "s5_gen":     "Génération autorégressive — mot par mot :",
        "s5_words":   ["L'", "IA", "est", "un", "système", "qui...", ""],
    },
    "en": {
        "s1_title":   "1 · User types a message",
        "s1_msg":     '"Explain to me how an LLM works"',
        "s1_send":    "Send ↵",
        "s1_note":    "→ The model receives raw text",
        "s2_title":   "2 · Tokenisation",
        "s2_raw":     '"Explain to me how an LLM works"',
        "s2_tokens":  ["Ex", "plain", " to", " me", " how", " an", " LLM", " works"],
        "s2_ids":     "Token IDs (GPT-4 vocabulary):",
        "s2_note":    "Each token = a sub-word from the vocabulary (~100k entries)",
        "s3_title":   "3 · Token → Vector (Embedding)",
        "s3_tokens":  [("plain", BRAND_BLUE), ("me", BRAND_GREEN), ("LLM", "#84CC16")],
        "s3_dim":     "768 to 4096 dimensions depending on the model",
        "s3_pos":     "+ Positional Encoding: position of each token is added to its vector",
        "s4_title":   "4 · Transformer — Self-Attention",
        "s4_sub":     "Each token computes an attention score with every other token",
        "s4_tokens":  ["Ex", "plain", " to", " me", " how", " an", "LLM"],
        "s4_axis_q":  "← attends to",
        "s4_axis_k":  "→ what",
        "s4_focus":   '"LLM" strongly attends to "how" (22%) and itself (30%)',
        "s4_layers":  "→ This repeats across N layers in parallel (GPT-4: 96 layers)",
        "s5_title":   "5 · Token Selection & Generation",
        "s5_prob":    "Probability distribution — next token:",
        "s5_cands":   [("The", 0.41), ("An", 0.22), ("A", 0.18), ("It", 0.09), ("This", 0.06), ("…", 0.04)],
        "s5_win":     '✓ Selected: "The"',
        "s5_gen":     "Autoregressive generation — word by word:",
        "s5_words":   ["The", "AI", "is", "a", "system", "that...", ""],
    },
}

TOKEN_IDS = [15043, 482, 12, 4724, 1312, 1791, 443, 9468]
TOKEN_COLORS = [BRAND_BLUE, BRAND_PURPLE, BRAND_GREEN, BRAND_ORANGE,
                BRAND_RED, "#06B6D4", "#EC4899", "#84CC16"]
VEC_DATA = [[0.21, -0.83, 0.44, 0.12],
            [-0.55, 0.31, 0.78, -0.20],
            [0.91, 0.07, -0.38, 0.63]]
ATTN = [
    [0.60, 0.15, 0.08, 0.07, 0.04, 0.03, 0.03],
    [0.18, 0.42, 0.14, 0.12, 0.07, 0.04, 0.03],
    [0.10, 0.14, 0.38, 0.18, 0.09, 0.07, 0.04],
    [0.06, 0.10, 0.12, 0.45, 0.14, 0.08, 0.05],
    [0.04, 0.07, 0.08, 0.18, 0.40, 0.14, 0.09],
    [0.03, 0.05, 0.07, 0.12, 0.16, 0.38, 0.19],
    [0.03, 0.12, 0.05, 0.22, 0.18, 0.10, 0.30],
]


def scene1(self, t):
    self.camera.background_color = DARK_BG
    title = Text(t["s1_title"], font_size=32, color=WHITE).to_edge(UP, buff=0.5)
    self.play(Write(title))

    bubble_rect = RoundedRectangle(
        corner_radius=0.3, width=9, height=1.5,
        fill_color=CARD_BG, fill_opacity=1,
        stroke_color=BRAND_BLUE, stroke_width=2
    ).shift(UP * 0.5)
    label = Text("User", font_size=18, color=BRAND_BLUE).next_to(bubble_rect, UP, buff=0.1).align_to(bubble_rect, LEFT).shift(RIGHT * 0.3)
    msg_text = Text(t["s1_msg"], font_size=20, color=WHITE).move_to(bubble_rect)
    cursor = Rectangle(width=0.03, height=0.35, fill_color=WHITE,
                       fill_opacity=1, stroke_width=0).next_to(msg_text, RIGHT, buff=0.05)

    self.play(FadeIn(bubble_rect), Write(label))
    self.play(AddTextLetterByLetter(msg_text, time_per_char=0.04), run_time=2)
    self.play(FadeIn(cursor))
    self.play(FadeOut(cursor))
    self.wait(1.2)

    enter_key = RoundedRectangle(corner_radius=0.1, width=1.6, height=0.5,
                                  fill_color=BRAND_GREEN, fill_opacity=1, stroke_width=0
                                  ).shift(DOWN * 1.5 + RIGHT * 3.5)
    enter_label = Text(t["s1_send"], font_size=16, color=WHITE).move_to(enter_key)
    self.play(FadeIn(enter_key), Write(enter_label))
    self.play(enter_key.animate.scale(0.92), rate_func=there_and_back, run_time=0.3)

    arrow_out = Arrow(bubble_rect.get_bottom(), bubble_rect.get_bottom() + DOWN * 1,
                      color=BRAND_BLUE, stroke_width=3)
    next_label = Text(t["s1_note"], font_size=20, color=BRAND_BLUE).next_to(arrow_out, DOWN, buff=0.15)
    self.play(GrowArrow(arrow_out), Write(next_label))
    self.wait(2)


def scene2(self, t):
    self.camera.background_color = DARK_BG
    title = Text(t["s2_title"], font_size=32, color=WHITE).to_edge(UP, buff=0.5)
    self.play(Write(title))

    raw = Text(t["s2_raw"], font_size=20, color=GRAY).shift(UP * 2)
    self.play(FadeIn(raw))
    self.wait(0.5)

    tokens_str = t["s2_tokens"]
    colors = TOKEN_COLORS[:len(tokens_str)]
    token_ids = TOKEN_IDS[:len(tokens_str)]

    boxes = VGroup()
    for tok, col in zip(tokens_str, colors):
        box = RoundedRectangle(corner_radius=0.15,
                               width=max(len(tok) * 0.18 + 0.5, 1.0), height=0.6,
                               fill_color=col, fill_opacity=0.25,
                               stroke_color=col, stroke_width=2)
        lbl = Text(tok, font_size=15, color=col).move_to(box)
        boxes.add(VGroup(box, lbl))
    boxes.arrange(RIGHT, buff=0.12).shift(UP * 0.5)

    self.play(raw.animate.set_opacity(0.3),
              LaggedStart(*[FadeIn(b, shift=DOWN * 0.3) for b in boxes], lag_ratio=0.12),
              run_time=1.8)

    id_label = Text(t["s2_ids"], font_size=17, color=GRAY).shift(DOWN * 0.6).align_to(boxes, LEFT)
    self.play(FadeIn(id_label))

    id_boxes = VGroup()
    for b_idx, (tid, col) in enumerate(zip(token_ids, colors)):
        rect = SurroundingRectangle(boxes[b_idx], color=col, buff=0.05, stroke_width=1)
        id_txt = Text(str(tid), font_size=13, color=col).move_to(boxes[b_idx].get_center() + DOWN * 1.4)
        id_boxes.add(VGroup(rect, id_txt))

    self.play(LaggedStart(*[FadeIn(ib) for ib in id_boxes], lag_ratio=0.1), run_time=1.5)
    note = Text(t["s2_note"], font_size=16, color=LIGHT_GRAY).shift(DOWN * 2.4)
    self.play(Write(note))
    self.wait(2.5)


def scene3(self, t):
    self.camera.background_color = DARK_BG
    title = Text(t["s3_title"], font_size=32, color=WHITE).to_edge(UP, buff=0.5)
    self.play(Write(title))

    for i, ((tok, col), vec) in enumerate(zip(t["s3_tokens"], VEC_DATA)):
        x_off = (i - 1) * 3.5
        box = RoundedRectangle(corner_radius=0.15, width=1.4, height=0.6,
                               fill_color=col, fill_opacity=0.2,
                               stroke_color=col, stroke_width=2).shift(UP * 1.5 + RIGHT * x_off)
        tok_label = Text(tok, font_size=18, color=col).move_to(box)
        self.play(FadeIn(box, tok_label), run_time=0.4)

        arr = Arrow(box.get_bottom(), box.get_bottom() + DOWN * 0.8, color=col, stroke_width=2)
        self.play(GrowArrow(arr), run_time=0.3)

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

        bar_bg = SurroundingRectangle(bar_group, color=col, buff=0.15, stroke_width=1,
                                      fill_color=CARD_BG, fill_opacity=1)
        bar_bg.set_z_index(-1)
        val_str = "[" + ", ".join(f"{v:.2f}" for v in vec) + ", ...]"
        val_text = Text(val_str, font_size=11, color=col).next_to(bar_group, DOWN, buff=0.15)

        self.play(FadeIn(bar_bg), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bar_group], lag_ratio=0.1), run_time=0.6)
        self.play(Write(val_text), run_time=0.4)

    self.play(Write(Text(t["s3_dim"], font_size=17, color=GRAY).shift(DOWN * 2.8)))
    self.play(Write(Text(t["s3_pos"], font_size=15, color=GRAY).shift(DOWN * 3.3)))
    self.wait(2.5)


def scene4(self, t):
    self.camera.background_color = DARK_BG
    title = Text(t["s4_title"], font_size=32, color=WHITE).to_edge(UP, buff=0.5)
    self.play(Write(title))
    subtitle = Text(t["s4_sub"], font_size=17, color=GRAY).next_to(title, DOWN, buff=0.2)
    self.play(FadeIn(subtitle))

    tokens = t["s4_tokens"]
    N = len(tokens)
    cell_size = 0.72
    grid_w = N * cell_size
    # Shift right to visually center grid+row_labels together (~0.6 = half avg label width + buff)
    origin = LEFT * (grid_w / 2) + RIGHT * 0.6 + DOWN * 0.15

    cells = []
    for r in range(N):
        row_cells = []
        for c in range(N):
            score = ATTN[r][c]
            t_val = score ** 0.5
            cell_color = interpolate_color(ManimColor("#0F2040"), ManimColor("#10B981"), t_val)
            rect = Rectangle(width=cell_size - 0.04, height=cell_size - 0.04,
                             fill_color=cell_color, fill_opacity=1,
                             stroke_color="#1E293B", stroke_width=1)
            rect.move_to(origin + RIGHT * (c + 0.5) * cell_size + DOWN * (r + 0.5) * cell_size)
            pct = int(score * 100)
            val = Text(f"{pct}%", font_size=11, color=WHITE if score > 0.15 else "#334155")
            val.move_to(rect)
            row_cells.append(VGroup(rect, val))
        cells.append(row_cells)

    col_labels = VGroup(*[
        Text(tok, font_size=12, color=GRAY).move_to(origin + RIGHT * (c + 0.5) * cell_size + UP * 0.45)
        for c, tok in enumerate(tokens)
    ])
    row_labels = VGroup(*[
        Text(tok, font_size=12, color=GRAY).next_to(origin + DOWN * (r + 0.5) * cell_size, LEFT, buff=0.15)
        for r, tok in enumerate(tokens)
    ])
    axis_q = Text(t["s4_axis_q"], font_size=11, color="#475569").rotate(PI / 2).next_to(row_labels, LEFT, buff=0.1)
    axis_k = Text(t["s4_axis_k"], font_size=11, color="#475569").next_to(col_labels, UP, buff=0.05)

    self.play(FadeIn(col_labels), FadeIn(row_labels), run_time=0.6)
    self.play(FadeIn(axis_q), FadeIn(axis_k), run_time=0.4)

    for r in range(N):
        self.play(LaggedStart(*[FadeIn(cells[r][c]) for c in range(N)], lag_ratio=0.05), run_time=0.5)

    self.wait(0.5)

    highlight = Rectangle(width=grid_w - 0.04, height=cell_size - 0.04,
                          stroke_color=BRAND_GREEN, stroke_width=2.5, fill_opacity=0)
    highlight.move_to(origin + RIGHT * grid_w / 2 + DOWN * (N - 0.5) * cell_size)
    focus_label = Text(t["s4_focus"], font_size=14, color=BRAND_GREEN).shift(DOWN * 3.3)
    self.play(Create(highlight), Write(focus_label), run_time=0.8)
    self.wait(1.2)

    self.play(Write(Text(t["s4_layers"], font_size=14, color=BRAND_BLUE).shift(DOWN * 3.8)))
    self.wait(2.5)


def scene5(self, t):
    self.camera.background_color = DARK_BG
    title = Text(t["s5_title"], font_size=32, color=WHITE).to_edge(UP, buff=0.5)
    self.play(Write(title))

    candidates = t["s5_cands"]
    bar_colors = [BRAND_GREEN, BRAND_BLUE, BRAND_PURPLE, BRAND_ORANGE, BRAND_RED, GRAY]

    self.play(Write(Text(t["s5_prob"], font_size=18, color=GRAY).shift(UP * 2)))

    bar_groups = VGroup()
    for i, ((word, prob), col) in enumerate(zip(candidates, bar_colors)):
        x = -4.0 + i * 1.55
        bar_h = prob * 4
        bar = Rectangle(width=1.0, height=bar_h, fill_color=col, fill_opacity=0.85, stroke_width=0)
        bar.align_to(ORIGIN + DOWN * 0.3, DOWN).shift(RIGHT * x)
        word_label = Text(word, font_size=16, color=col).next_to(bar, DOWN, buff=0.1)
        pct_label = Text(f"{int(prob*100)}%", font_size=14, color=col).next_to(bar, UP, buff=0.1)
        bar_groups.add(VGroup(bar, word_label, pct_label))

    self.play(LaggedStart(*[GrowFromEdge(bg, DOWN) for bg in bar_groups], lag_ratio=0.12), run_time=1.5)

    win_box = SurroundingRectangle(bar_groups[0], color=BRAND_GREEN, stroke_width=3, buff=0.1)
    win_text = Text(t["s5_win"], font_size=20, color=BRAND_GREEN).shift(DOWN * 2.3)
    self.play(Create(win_box), Write(win_text))
    self.wait(0.8)

    self.play(Write(Text(t["s5_gen"], font_size=18, color=GRAY).shift(DOWN * 2.9)))

    response_text = ""
    response_mob = None
    for w in t["s5_words"]:
        response_text += w + (" " if w else "")
        new_mob = Text(response_text.strip(), font_size=22, color=WHITE).shift(DOWN * 3.6)
        if response_mob is None:
            self.play(FadeIn(new_mob), run_time=0.3)
        else:
            self.play(Transform(response_mob, new_mob), run_time=0.25)
            self.remove(response_mob)
        response_mob = new_mob
    self.wait(2)


# ─── Individual scenes (FR, for dev/preview) ──────────────────────────────────
class Scene1_UserInput(Scene):
    def construct(self): scene1(self, TEXTS["fr"])

class Scene2_Tokenization(Scene):
    def construct(self): scene2(self, TEXTS["fr"])

class Scene3_Embeddings(Scene):
    def construct(self): scene3(self, TEXTS["fr"])

class Scene4_Attention(Scene):
    def construct(self): scene4(self, TEXTS["fr"])

class Scene5_Generation(Scene):
    def construct(self): scene5(self, TEXTS["fr"])


# ─── Full movies ───────────────────────────────────────────────────────────────
class LLMChatbotFull_FR(Scene):
    def construct(self):
        self.camera.background_color = DARK_BG
        t = TEXTS["fr"]
        for fn in [scene1, scene2, scene3, scene4, scene5]:
            fn(self, t)
            self.clear()
            self.wait(0.3)


class LLMChatbotFull_EN(Scene):
    def construct(self):
        self.camera.background_color = DARK_BG
        t = TEXTS["en"]
        for fn in [scene1, scene2, scene3, scene4, scene5]:
            fn(self, t)
            self.clear()
            self.wait(0.3)
