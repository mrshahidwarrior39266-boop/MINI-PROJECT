"""
Generate 3 high-resolution, ultra-polished UI design mockup PNG images
representing the 3 architectural UI candidates for the Intelligent Tutoring System,
inspired by the dark studio aesthetic of the OpenAI Codex interface.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent

# Load fonts with clean fallbacks
FONT_MAIN = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SEMIBOLD = "C:/Windows/Fonts/seguisb.ttf"
FONT_MONO = "C:/Windows/Fonts/consola.ttf"
FONT_MONO_BOLD = "C:/Windows/Fonts/consolab.ttf"


def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


f_title_xl = get_font(FONT_BOLD, 30)
f_title_lg = get_font(FONT_BOLD, 22)
f_head = get_font(FONT_SEMIBOLD, 16)
f_head_b = get_font(FONT_BOLD, 16)
f_body = get_font(FONT_MAIN, 14)
f_body_b = get_font(FONT_BOLD, 14)
f_small = get_font(FONT_MAIN, 12)
f_small_b = get_font(FONT_BOLD, 12)
f_tiny = get_font(FONT_MAIN, 11)
f_mono = get_font(FONT_MONO, 13)
f_mono_b = get_font(FONT_MONO_BOLD, 13)
f_mono_sm = get_font(FONT_MONO, 11)


def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)


def render_concept1(output_path: Path):
    """Concept 1: Codex Dark Studio (Direct Native Inspiration - Floating Island & Central Cockpit)."""
    w, h = 1440, 900
    im = Image.new("RGB", (w, h), color=(22, 22, 24))
    draw = ImageDraw.Draw(im)

    # 1. Top Window Titlebar
    draw.rectangle([0, 0, w, 44], fill=(18, 18, 20))
    draw.line([0, 44, w, 44], fill=(36, 36, 40), width=1)
    # Mac/App Window dots
    draw.ellipse([18, 15, 30, 27], fill=(248, 113, 113))
    draw.ellipse([38, 15, 50, 27], fill=(251, 191, 36))
    draw.ellipse([58, 15, 70, 27], fill=(52, 211, 153))
    # App Nav
    draw.text((88, 13), "<   >", fill=(110, 110, 120), font=f_head)
    draw.text((140, 14), "File    Edit    View    Help", fill=(130, 130, 142), font=f_body)
    draw.text((w // 2 - 140, 13), "ArchaLearn  //  Codex Dark Studio", fill=(200, 200, 210), font=f_head)
    draw.text((w - 200, 14), "Python 3.13  •  main (013f81b)", fill=(100, 100, 112), font=f_small)

    # 2. Left Icon Rail (Slim vertical strip)
    rail_w = 60
    draw.rectangle([0, 45, rail_w, h], fill=(20, 20, 22))
    draw.line([rail_w, 45, rail_w, h], fill=(34, 34, 38), width=1)

    # Active Home icon pill
    draw_rounded_rect(draw, [10, 60, 50, 100], radius=10, fill=(38, 38, 44), outline=(55, 55, 62))
    draw.text((22, 70), "⌂", fill=(255, 255, 255), font=f_title_lg)

    # Secondary icons
    draw.text((23, 125), "🕒", fill=(120, 120, 130), font=f_head)
    draw.text((22, 175), "⚡", fill=(120, 120, 130), font=f_head)
    draw.text((22, 225), "📊", fill=(120, 120, 130), font=f_head)
    draw.text((22, 275), "📚", fill=(120, 120, 130), font=f_head)
    draw.text((22, h - 50), "⚙", fill=(100, 100, 110), font=f_head)

    # 3. Sidebar: Curriculum Tree & Projects
    side_w = 280
    side_x0 = rail_w
    side_x1 = side_x0 + side_w
    draw.rectangle([side_x0, 45, side_x1, h], fill=(25, 25, 28))
    draw.line([side_x1, 45, side_x1, h], fill=(36, 36, 40), width=1)

    # Title in sidebar
    draw.text((side_x0 + 20, 65), "Codex Tutor ⌵", fill=(240, 240, 245), font=f_head_b)
    draw.text((side_x1 - 40, 65), "🔍", fill=(120, 120, 130), font=f_body)

    # New Session Button
    draw_rounded_rect(draw, [side_x0 + 16, 105, side_x1 - 16, 142], radius=8, fill=(34, 34, 40), outline=(48, 48, 56))
    draw.text((side_x0 + 32, 114), "+   Start Daily Plan (30/60/10)", fill=(220, 220, 230), font=f_body_b)

    # Projects / Curriculum Section
    draw.text((side_x0 + 20, 165), "CURRICULUM DAG", fill=(110, 110, 122), font=f_small_b)

    # Project item active
    draw_rounded_rect(draw, [side_x0 + 14, 190, side_x1 - 14, 250], radius=8, fill=(38, 38, 46), outline=(56, 56, 68))
    draw.text((side_x0 + 26, 200), "📁 python-foundations", fill=(255, 255, 255), font=f_body_b)
    draw.text((side_x0 + 26, 224), "8 concepts • Frontier: Operators", fill=(130, 130, 142), font=f_small)

    # Concepts list
    draw.text((side_x0 + 20, 275), "KNOWLEDGE PROGRESS", fill=(110, 110, 122), font=f_small_b)

    concepts = [
        ("py.variables", "92% Mastered", (52, 211, 153), True),
        ("py.data_types", "88% Mastered", (52, 211, 153), True),
        ("py.operators", "READY (Frontier)", (251, 191, 36), True),
        ("py.conditionals", "Locked", (100, 100, 110), False),
        ("py.while_loops", "Locked", (100, 100, 110), False),
        ("py.for_loops", "Locked", (100, 100, 110), False),
        ("py.lists_sequences", "Locked", (100, 100, 110), False),
        ("py.functions", "Locked", (100, 100, 110), False),
    ]

    c_y = 300
    for cid, status_txt, color, is_unlocked in concepts:
        bg_col = (30, 30, 35) if is_unlocked else (22, 22, 25)
        bdr_col = (251, 191, 36) if "READY" in status_txt else ((42, 42, 48) if is_unlocked else (30, 30, 34))
        draw_rounded_rect(draw, [side_x0 + 14, c_y, side_x1 - 14, c_y + 38], radius=6, fill=bg_col, outline=bdr_col)
        draw.text((side_x0 + 26, c_y + 9), cid, fill=(220, 220, 230) if is_unlocked else (100, 100, 110), font=f_mono)
        draw.text((side_x1 - 120, c_y + 11), status_txt, fill=color, font=f_tiny)
        c_y += 46

    # Bottom Audit Box
    draw_rounded_rect(draw, [side_x0 + 14, h - 90, side_x1 - 14, h - 20], radius=8, fill=(18, 18, 22), outline=(36, 36, 42))
    draw.text((side_x0 + 24, h - 80), "🛡️ SHA-256 Audit Trail: Valid", fill=(52, 211, 153), font=f_small_b)
    draw.text((side_x0 + 24, h - 60), "Learner: Alan Turing  |  Score: 88%", fill=(150, 150, 160), font=f_tiny)
    draw.text((side_x0 + 24, h - 42), "State Hash: 86C09D8BB6567BD0", fill=(6, 182, 212), font=f_mono_sm)

    # 4. Main Center Canvas (OpenAI Codex Central Staging)
    center_w = w - side_x1
    center_cx = side_x1 + center_w // 2

    # Emblem glyph in center
    glyph_y = 210
    draw_rounded_rect(draw, [center_cx - 38, glyph_y, center_cx + 38, glyph_y + 76], radius=20, fill=(32, 32, 38), outline=(52, 52, 62), width=1)
    draw.text((center_cx - 18, glyph_y + 20), ">_", fill=(6, 182, 212), font=f_title_lg)

    # Central Codex-style Hero Text
    title_text = "What should we master in Python Foundations?"
    draw.text((center_cx - 310, glyph_y + 105), title_text, fill=(255, 255, 255), font=f_title_xl)
    # Underline under "Python Foundations"
    draw.line([center_cx + 5, glyph_y + 145, center_cx + 310, glyph_y + 145], fill=(255, 255, 255), width=2)

    subtitle_text = "Dual-Engine Socratic Tutor active. Next unlocked on Frontier: py.operators_expressions"
    draw.text((center_cx - 280, glyph_y + 160), subtitle_text, fill=(145, 145, 158), font=f_body)

    # 3 Socratic Quick Action Cards
    card_y = glyph_y + 215
    actions = [
        ("⚡ Start 30/60/10 Plan", "3 Review, 6 Frontier, 1 Synthesis"),
        ("📦 Hardware RAM Model", "Inspect memory boxes & pointer swaps"),
        ("🧩 Synthesis Capstone", "Multi-concept real-world code challenge"),
    ]
    card_w = 230
    total_cards_w = 3 * card_w + 2 * 18
    start_cx = center_cx - total_cards_w // 2

    for idx, (head, desc) in enumerate(actions):
        cx0 = start_cx + idx * (card_w + 18)
        draw_rounded_rect(draw, [cx0, card_y, cx0 + card_w, card_y + 70], radius=10, fill=(28, 28, 33), outline=(46, 46, 56))
        draw.text((cx0 + 16, card_y + 14), head, fill=(230, 230, 240), font=f_body_b)
        draw.text((cx0 + 16, card_y + 40), desc, fill=(130, 130, 142), font=f_tiny)

    # 5. Floating Bottom Capsule Cockpit (Exact Codex floating dock layout)
    dock_w = 760
    dock_h = 145
    dock_x0 = center_cx - dock_w // 2
    dock_y0 = h - dock_h - 40

    # Main Dock container
    draw_rounded_rect(draw, [dock_x0, dock_y0, dock_x0 + dock_w, dock_y0 + dock_h], radius=18, fill=(32, 32, 38), outline=(58, 58, 70), width=1)

    # Top Pills Bar inside Dock
    # Pill 1: Python environment
    draw_rounded_rect(draw, [dock_x0 + 16, dock_y0 + 14, dock_x0 + 130, dock_y0 + 40], radius=8, fill=(42, 42, 50))
    draw.text((dock_x0 + 26, dock_y0 + 18), "💻 Python 3.13", fill=(210, 210, 220), font=f_small_b)

    # Pill 2: Active Target Concept
    draw_rounded_rect(draw, [dock_x0 + 140, dock_y0 + 14, dock_x0 + 340, dock_y0 + 40], radius=8, fill=(16, 40, 52), outline=(6, 182, 212))
    draw.text((dock_x0 + 152, dock_y0 + 18), "📍 py.operators_expressions", fill=(6, 182, 212), font=f_small_b)

    # Pill 3: Pedagogical Phase
    draw_rounded_rect(draw, [dock_x0 + 350, dock_y0 + 14, dock_x0 + 515, dock_y0 + 40], radius=8, fill=(16, 46, 32), outline=(52, 211, 153))
    draw.text((dock_x0 + 362, dock_y0 + 18), "⚡ 60% Frontier Learning", fill=(52, 211, 153), font=f_small_b)

    # Pill 4: Socratic Mode
    draw_rounded_rect(draw, [dock_x0 + 525, dock_y0 + 14, dock_x0 + 655, dock_y0 + 40], radius=8, fill=(42, 38, 20))
    draw.text((dock_x0 + 538, dock_y0 + 18), "🧠 Socratic Mode", fill=(251, 191, 36), font=f_small_b)

    # Input Field
    draw.text((dock_x0 + 20, dock_y0 + 60), "Type your answer, ask for a 'physical analogy', or run 'memory'...", fill=(120, 120, 132), font=f_head)
    # Cursor
    draw.line([dock_x0 + 550, dock_y0 + 58, dock_x0 + 550, dock_y0 + 80], fill=(6, 182, 212), width=2)

    # Divider line inside Dock
    draw.line([dock_x0 + 16, dock_y0 + 96, dock_x0 + dock_w - 16, dock_y0 + 96], fill=(44, 44, 52), width=1)

    # Bottom Row Controls
    draw_rounded_rect(draw, [dock_x0 + 16, dock_y0 + 106, dock_x0 + 155, dock_y0 + 134], radius=6, fill=(40, 40, 48), outline=(56, 56, 66))
    draw.text((dock_x0 + 26, dock_y0 + 111), "+ Ingest PDF/MD", fill=(210, 210, 220), font=f_small)

    draw_rounded_rect(draw, [dock_x0 + 165, dock_y0 + 106, dock_x0 + 285, dock_y0 + 134], radius=6, fill=(40, 40, 48), outline=(56, 56, 66))
    draw.text((dock_x0 + 175, dock_y0 + 111), "💡 Request Analogy", fill=(210, 210, 220), font=f_small)

    # Model selector badge
    draw_rounded_rect(draw, [dock_x0 + dock_w - 190, dock_y0 + 106, dock_x0 + dock_w - 65, dock_y0 + 134], radius=6, fill=(36, 36, 44))
    draw.text((dock_x0 + dock_w - 180, dock_y0 + 111), "Socratic-LLM (RAG)", fill=(150, 150, 160), font=f_small)

    # Circular Send Button (Just like Codex)
    draw.ellipse([dock_x0 + dock_w - 52, dock_y0 + 102, dock_x0 + dock_w - 16, dock_y0 + 138], fill=(255, 255, 255))
    draw.text((dock_x0 + dock_w - 40, dock_y0 + 107), "↑", fill=(10, 10, 12), font=f_head_b)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(output_path)


def render_concept2(output_path: Path):
    """Concept 2: Dual-Engine Split Studio (Chat + Live Hardware RAM Visualizer)."""
    w, h = 1440, 900
    im = Image.new("RGB", (w, h), color=(18, 18, 22))
    draw = ImageDraw.Draw(im)

    # 1. Top Window Titlebar
    draw.rectangle([0, 0, w, 44], fill=(16, 16, 18))
    draw.line([0, 44, w, 44], fill=(36, 36, 40), width=1)
    draw.ellipse([18, 15, 30, 27], fill=(248, 113, 113))
    draw.ellipse([38, 15, 50, 27], fill=(251, 191, 36))
    draw.ellipse([58, 15, 70, 27], fill=(52, 211, 153))
    draw.text((88, 13), "<   >", fill=(110, 110, 120), font=f_head)
    draw.text((w // 2 - 180, 13), "ArchaLearn  //  Dual-Engine Split Studio", fill=(200, 200, 210), font=f_head)
    draw.text((w - 240, 14), "Live Hardware Sync • Socratic Loop", fill=(52, 211, 153), font=f_small)

    # 3-Column Geometry
    col1_w = 300
    col3_w = 420
    col2_w = w - col1_w - col3_w

    # Column 1: Curriculum & Memory Decay (Left)
    draw.rectangle([0, 45, col1_w, h], fill=(22, 22, 26))
    draw.line([col1_w, 45, col1_w, h], fill=(36, 36, 42), width=1)

    draw.text((20, 65), "FRONTIER & STABILITY", fill=(130, 130, 145), font=f_small_b)
    draw.text((col1_w - 90, 65), "Ebbinghaus", fill=(6, 182, 212), font=f_tiny)

    # Cards in Left Column
    left_items = [
        ("py.variables", "Mastery: 92%", "Stability: 48h (S=2.0)", 92, (52, 211, 153)),
        ("py.data_types", "Mastery: 88%", "Stability: 24h (S=1.5)", 88, (52, 211, 153)),
        ("py.operators", "Mastery: 45%", "Frontier Active (S=0.8)", 45, (251, 191, 36)),
        ("py.conditionals", "Mastery: 0%", "Prereqs Unfinished", 0, (100, 100, 112)),
        ("py.while_loops", "Mastery: 0%", "Locked in DAG", 0, (100, 100, 112)),
    ]

    ly = 100
    for name, m_txt, s_txt, pct, bar_col in left_items:
        draw_rounded_rect(draw, [16, ly, col1_w - 16, ly + 80], radius=8, fill=(28, 28, 34), outline=(44, 44, 52))
        draw.text((28, ly + 10), name, fill=(230, 230, 240), font=f_mono_b)
        draw.text((col1_w - 110, ly + 12), m_txt, fill=bar_col, font=f_tiny)
        draw.text((28, ly + 34), s_txt, fill=(130, 130, 142), font=f_small)

        # Progress bar
        draw_rounded_rect(draw, [28, ly + 58, col1_w - 28, ly + 66], radius=4, fill=(38, 38, 46))
        fill_bar_w = int((col1_w - 56) * (pct / 100))
        if fill_bar_w > 0:
            draw_rounded_rect(draw, [28, ly + 58, 28 + fill_bar_w, ly + 66], radius=4, fill=bar_col)
        ly += 95

    # Column 2: Conversational Socratic Dialogue (Middle)
    col2_x = col1_w
    draw.rectangle([col2_x, 45, col2_x + col2_w, h], fill=(18, 18, 22))
    draw.line([col2_x + col2_w, 45, col2_x + col2_w, h], fill=(36, 36, 42), width=1)

    # Sub-header in chat
    draw.text((col2_x + 30, 65), "SOCRATIC DIALOGUE STREAM", fill=(130, 130, 145), font=f_small_b)
    draw.text((col2_x + col2_w - 150, 65), "Active Session #104", fill=(100, 100, 112), font=f_tiny)

    # Message 1: Tutor Diagnostic Question
    msg1_y = 100
    draw_rounded_rect(draw, [col2_x + 25, msg1_y, col2_x + col2_w - 25, msg1_y + 130], radius=12, fill=(26, 26, 32), outline=(48, 48, 60))
    draw.text((col2_x + 40, msg1_y + 14), "🧠 Socratic Tutor  •  py.operators_expressions", fill=(251, 191, 36), font=f_small_b)
    draw.text((col2_x + 40, msg1_y + 40), "What is the difference between '/' and '//' in Python 3?", fill=(240, 240, 248), font=f_head)
    draw.text((col2_x + 40, msg1_y + 66), "What will 7 / 2 and 7 // 2 evaluate to in memory?", fill=(240, 240, 248), font=f_head)
    # Citation footer
    draw.text((col2_x + 40, msg1_y + 98), "📚 Mandatory Citation: chunk.py.operators.01 (Official Python 3 Docs)", fill=(6, 182, 212), font=f_mono_sm)

    # Message 2: Student Answer
    msg2_y = msg1_y + 150
    draw_rounded_rect(draw, [col2_x + 100, msg2_y, col2_x + col2_w - 25, msg2_y + 90], radius=12, fill=(18, 38, 50), outline=(24, 76, 100))
    draw.text((col2_x + 115, msg2_y + 14), "👤 Learner Alan Turing", fill=(6, 182, 212), font=f_small_b)
    draw.text((col2_x + 115, msg2_y + 38), "7 / 2 gives 3.5 because it's float division, while 7 // 2 gives 3", fill=(220, 240, 255), font=f_body)
    draw.text((col2_x + 115, msg2_y + 58), "because floor division rounds down to the nearest integer!", fill=(220, 240, 255), font=f_body)

    # Message 3: Evaluator Feedback
    msg3_y = msg2_y + 110
    draw_rounded_rect(draw, [col2_x + 25, msg3_y, col2_x + col2_w - 25, msg3_y + 130], radius=12, fill=(16, 36, 26), outline=(32, 92, 58))
    draw.text((col2_x + 40, msg3_y + 14), "✓ Evaluator Assessment: CORRECT (Score: 100%)", fill=(52, 211, 153), font=f_small_b)
    draw.text((col2_x + 40, msg3_y + 38), "Spot on! The true division operator '/' always returns a <float>,", fill=(215, 245, 225), font=f_body)
    draw.text((col2_x + 40, msg3_y + 58), "allocating 24 bytes on the heap. Floor division '//' truncates toward -∞.", fill=(215, 245, 225), font=f_body)
    draw.text((col2_x + 40, msg3_y + 82), "Notice on the right: RAM Visualizer updated with both runtime boxes!", fill=(251, 191, 36), font=f_small_b)
    draw.text((col2_x + 40, msg3_y + 102), "Cited chunk verification passed [doc_control_flow_002, chunk.py.operators.01]", fill=(52, 211, 153), font=f_mono_sm)

    # Bottom Chat Input Box
    input_h = 75
    input_y = h - input_h - 25
    draw_rounded_rect(draw, [col2_x + 25, input_y, col2_x + col2_w - 25, input_y + input_h], radius=14, fill=(28, 28, 34), outline=(48, 48, 58))
    draw.text((col2_x + 42, input_y + 16), "Type your explanation, or ask 'why is 7//-2 equal to -4?'...", fill=(120, 120, 130), font=f_body)
    # Action buttons inside input
    draw_rounded_rect(draw, [col2_x + 40, input_y + 44, col2_x + 130, input_y + 66], radius=4, fill=(36, 36, 44))
    draw.text((col2_x + 48, input_y + 48), "💡 Analogy", fill=(180, 180, 190), font=f_tiny)

    draw_rounded_rect(draw, [col2_x + 140, input_y + 44, col2_x + 230, input_y + 66], radius=4, fill=(36, 36, 44))
    draw.text((col2_x + 148, input_y + 48), "📦 Swap Box", fill=(180, 180, 190), font=f_tiny)

    draw_rounded_rect(draw, [col2_x + col2_w - 110, input_y + 20, col2_x + col2_w - 40, input_y + 56], radius=8, fill=(6, 182, 212))
    draw.text((col2_x + col2_w - 95, input_y + 28), "Send", fill=(10, 10, 14), font=f_body_b)

    # Column 3: Live Hardware RAM Visualizer (Right)
    col3_x = col2_x + col2_w
    draw.rectangle([col3_x, 45, w, h], fill=(22, 22, 26))

    draw.text((col3_x + 20, 65), "HARDWARE RAM VISUALIZER", fill=(130, 130, 145), font=f_small_b)
    draw.text((w - 100, 65), "● Live Sync", fill=(52, 211, 153), font=f_tiny)

    # RAM Box 1
    box1_y = 100
    draw_rounded_rect(draw, [col3_x + 20, box1_y, w - 20, box1_y + 115], radius=10, fill=(28, 28, 34), outline=(46, 46, 56))
    draw.text((col3_x + 35, box1_y + 12), "LABEL: a   |   ADDRESS: 0x7ffe10", fill=(130, 130, 145), font=f_mono)
    draw.text((col3_x + 35, box1_y + 36), "VALUE:  3.5", fill=(6, 182, 212), font=f_title_lg)
    draw.text((col3_x + 35, box1_y + 70), "TYPE:   <class 'float'>", fill=(160, 160, 175), font=f_mono)
    draw.text((col3_x + 35, box1_y + 90), "SIZE:   24 Bytes  |  Refcount: 1", fill=(110, 110, 120), font=f_tiny)

    # RAM Box 2
    box2_y = box1_y + 130
    draw_rounded_rect(draw, [col3_x + 20, box2_y, w - 20, box2_y + 115], radius=10, fill=(28, 28, 34), outline=(46, 46, 56))
    draw.text((col3_x + 35, box2_y + 12), "LABEL: b   |   ADDRESS: 0x7ffe18", fill=(130, 130, 145), font=f_mono)
    draw.text((col3_x + 35, box2_y + 36), "VALUE:  3", fill=(52, 211, 153), font=f_title_lg)
    draw.text((col3_x + 35, box2_y + 70), "TYPE:   <class 'int'>", fill=(160, 160, 175), font=f_mono)
    draw.text((col3_x + 35, box2_y + 90), "SIZE:   28 Bytes  |  Refcount: 2", fill=(110, 110, 120), font=f_tiny)

    # 3-Step Swap Movie Frame
    movie_y = box2_y + 135
    draw_rounded_rect(draw, [col3_x + 20, movie_y, w - 20, movie_y + 220], radius=10, fill=(18, 18, 22), outline=(50, 50, 62))
    draw.text((col3_x + 35, movie_y + 14), "🎬 3-STEP VARIABLE SWAP MOVIE", fill=(251, 191, 36), font=f_small_b)

    steps = [
        ("Step 1:", "temp = a", "Copy value in 'a' into holding box 'temp'"),
        ("Step 2:", "a = b", "Safely overwrite 'a' with contents of 'b'"),
        ("Step 3:", "b = temp", "Move saved 'temp' value into 'b'"),
    ]
    sy = movie_y + 44
    for stp, code, expl in steps:
        draw.text((col3_x + 35, sy), stp, fill=(6, 182, 212), font=f_body_b)
        draw.text((col3_x + 95, sy), code, fill=(255, 255, 255), font=f_mono_b)
        draw.text((col3_x + 35, sy + 20), expl, fill=(140, 140, 150), font=f_tiny)
        sy += 48

    draw.text((col3_x + 35, movie_y + 192), "Verdict: No Data Loss (Safe Swap Proven)", fill=(52, 211, 153), font=f_small_b)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(output_path)


def render_concept3(output_path: Path):
    """Concept 3: Cyber-Lattice Neo-Studio (Topographic Knowledge Mesh + Socratic Capstone Lab)."""
    w, h = 1440, 900
    im = Image.new("RGB", (w, h), color=(14, 14, 18))
    draw = ImageDraw.Draw(im)

    # 1. Top Window Titlebar
    draw.rectangle([0, 0, w, 44], fill=(12, 12, 16))
    draw.line([0, 44, w, 44], fill=(30, 30, 40), width=1)
    draw.ellipse([18, 15, 30, 27], fill=(248, 113, 113))
    draw.ellipse([38, 15, 50, 27], fill=(251, 191, 36))
    draw.ellipse([58, 15, 70, 27], fill=(52, 211, 153))
    draw.text((88, 13), "<   >", fill=(110, 110, 120), font=f_head)
    draw.text((w // 2 - 180, 13), "ArchaLearn  //  Cyber-Lattice Neo-Studio", fill=(200, 200, 210), font=f_head)
    draw.text((w - 240, 14), "Topological DAG  •  Synthesis Mode", fill=(99, 102, 241), font=f_small)

    # 2. Daily Plan Session Header Banner (Glassmorphic)
    ban_y0 = 60
    ban_h = 58
    draw_rounded_rect(draw, [35, ban_y0, w - 35, ban_y0 + ban_h], radius=14, fill=(22, 22, 30), outline=(46, 46, 64))

    draw.text((55, ban_y0 + 12), "TODAY'S ADAPTIVE SESSION: 10 ITEMS", fill=(255, 255, 255), font=f_head_b)
    draw.text((55, ban_y0 + 34), "Goal: Progress from Variables through Control Flow into Functions", fill=(140, 140, 155), font=f_small)

    # Ratio pills
    draw_rounded_rect(draw, [w - 530, ban_y0 + 14, w - 380, ban_y0 + 44], radius=6, fill=(18, 44, 30), outline=(52, 211, 153))
    draw.text((w - 520, ban_y0 + 20), "30% Review (3 items)", fill=(52, 211, 153), font=f_small_b)

    draw_rounded_rect(draw, [w - 365, ban_y0 + 14, w - 200, ban_y0 + 44], radius=6, fill=(44, 38, 16), outline=(251, 191, 36))
    draw.text((w - 355, ban_y0 + 20), "60% Frontier (6 items)", fill=(251, 191, 36), font=f_small_b)

    draw_rounded_rect(draw, [w - 185, ban_y0 + 14, w - 50, ban_y0 + 44], radius=6, fill=(34, 20, 48), outline=(192, 132, 252))
    draw.text((w - 175, ban_y0 + 20), "10% Synthesis (1)", fill=(192, 132, 252), font=f_small_b)

    # 3. Main Split Panels
    split_y = ban_y0 + ban_h + 20
    split_h = h - split_y - 25

    panel1_w = 480
    panel2_w = w - panel1_w - 95

    # Left Panel: 2D Interactive Topological Knowledge Graph
    draw_rounded_rect(draw, [35, split_y, 35 + panel1_w, split_y + split_h], radius=16, fill=(20, 20, 26), outline=(42, 42, 58))
    draw.text((55, split_y + 20), "CURRICULUM TOPOLOGY (DAG)", fill=(200, 200, 215), font=f_head_b)
    draw.text((55, split_y + 44), "Topologically ordered prerequisite dependency graph", fill=(120, 120, 135), font=f_small)

    # Draw Nodes and Directed Edges
    # Edges
    draw.line([275, split_y + 115, 275, split_y + 175], fill=(52, 211, 153), width=3)
    draw.line([275, split_y + 215, 275, split_y + 275], fill=(251, 191, 36), width=3)
    draw.line([240, split_y + 315, 160, split_y + 375], fill=(60, 60, 75), width=2)
    draw.line([310, split_y + 315, 390, split_y + 375], fill=(60, 60, 75), width=2)
    draw.line([160, split_y + 415, 240, split_y + 475], fill=(60, 60, 75), width=2)
    draw.line([390, split_y + 415, 310, split_y + 475], fill=(60, 60, 75), width=2)

    # Nodes
    dag_nodes = [
        (275, split_y + 95, "py.variables", "92% Mastered", (52, 211, 153), (18, 44, 30)),
        (275, split_y + 195, "py.data_types", "88% Mastered", (52, 211, 153), (18, 44, 30)),
        (275, split_y + 295, "⚡ py.operators", "FRONTIER (Ready)", (251, 191, 36), (44, 38, 16)),
        (160, split_y + 395, "🔒 py.conditionals", "Locked", (100, 100, 115), (26, 26, 32)),
        (390, split_y + 395, "🔒 py.lists_sequences", "Locked", (100, 100, 115), (26, 26, 32)),
        (275, split_y + 495, "🔒 py.functions", "Locked (Prereqs: 5)", (100, 100, 115), (26, 26, 32)),
    ]

    for nx, ny, nlabel, nsub, col, bg_col in dag_nodes:
        nw = 190
        nh = 46
        draw_rounded_rect(draw, [nx - nw // 2, ny - nh // 2, nx + nw // 2, ny + nh // 2], radius=10, fill=bg_col, outline=col, width=2)
        draw.text((nx - nw // 2 + 14, ny - nh // 2 + 8), nlabel, fill=(255, 255, 255), font=f_mono_b)
        draw.text((nx - nw // 2 + 14, ny - nh // 2 + 26), nsub, fill=col, font=f_tiny)

    # Frontier Badge on Left Panel bottom
    draw_rounded_rect(draw, [55, split_y + split_h - 90, 35 + panel1_w - 20, split_y + split_h - 20], radius=10, fill=(24, 24, 32), outline=(48, 48, 64))
    draw.text((70, split_y + split_h - 80), "FRONTIER CONDITION:", fill=(251, 191, 36), font=f_small_b)
    draw.text((70, split_y + split_h - 60), "All prerequisites have mastery >= 0.70", fill=(200, 200, 210), font=f_small)
    draw.text((70, split_y + split_h - 40), "Target concept 'py.operators' currently = 0.45", fill=(6, 182, 212), font=f_tiny)

    # Right Panel: Active Synthesis & Socratic Learning Lab
    panel2_x = 35 + panel1_w + 25
    draw_rounded_rect(draw, [panel2_x, split_y, panel2_x + panel2_w, split_y + split_h], radius=16, fill=(20, 20, 26), outline=(42, 42, 58))

    draw.text((panel2_x + 30, split_y + 20), "ACTIVE FRONTIER LAB: py.operators_expressions", fill=(6, 182, 212), font=f_head_b)
    draw.text((panel2_x + panel2_w - 180, split_y + 20), "Item #3 of 10  [Est: 4m]", fill=(130, 130, 145), font=f_small)

    # Diagnostic Question Container
    q_box_y = split_y + 55
    q_box_h = 160
    draw_rounded_rect(draw, [panel2_x + 25, q_box_y, panel2_x + panel2_w - 25, q_box_y + q_box_h], radius=12, fill=(26, 26, 34), outline=(46, 46, 62))
    draw.text((panel2_x + 45, q_box_y + 16), "Socratic Diagnostic Question:", fill=(251, 191, 36), font=f_small_b)
    draw.text((panel2_x + 45, q_box_y + 44), "In Python, suppose you have `count = '10'` and attempt `total = count + 5`.", fill=(240, 240, 250), font=f_head)
    draw.text((panel2_x + 45, q_box_y + 70), "1) Why will Python raise a TypeError at runtime?", fill=(210, 210, 225), font=f_body)
    draw.text((panel2_x + 45, q_box_y + 92), "2) How does explicit type casting `int(count)` prevent this crash?", fill=(210, 210, 225), font=f_body)

    # Physical Analogy Hint Bar
    draw_rounded_rect(draw, [panel2_x + 45, q_box_y + 120, panel2_x + panel2_w - 45, q_box_y + 148], radius=6, fill=(16, 36, 46), outline=(6, 182, 212))
    draw.text((panel2_x + 55, q_box_y + 126), "💡 Physical Model: Strings are alphabet stamps; integers are physical counting marbles.", fill=(6, 182, 212), font=f_small)

    # Code / Solution Sandbox
    code_box_y = q_box_y + q_box_h + 20
    code_box_h = 240
    draw_rounded_rect(draw, [panel2_x + 25, code_box_y, panel2_x + panel2_w - 25, code_box_y + code_box_h], radius=12, fill=(14, 14, 18), outline=(36, 36, 48))
    draw.text((panel2_x + 45, code_box_y + 14), "# Interactive Python 3.13 REPL Sandbox", fill=(100, 100, 115), font=f_mono)

    repl_lines = [
        (">>> count = '10'", (200, 200, 210)),
        (">>> type(count)", (200, 200, 210)),
        ("<class 'str'>", (6, 182, 212)),
        (">>> total = int(count) + 5", (251, 191, 36)),
        (">>> print(total, type(total))", (200, 200, 210)),
        ("15 <class 'int'>  # Safe evaluated result!", (52, 211, 153)),
    ]
    ry = code_box_y + 40
    for line, lcol in repl_lines:
        draw.text((panel2_x + 45, ry), line, fill=lcol, font=f_mono_b)
        ry += 24

    draw.text((panel2_x + 45, code_box_y + 195), "Authoritative Chunk Citations: [doc_control_flow_005, chunk.py.operators.01]", fill=(120, 120, 135), font=f_mono_sm)

    # Floating Bottom Evaluation Dock
    dock_y = split_y + split_h - 90
    draw_rounded_rect(draw, [panel2_x + 25, dock_y, panel2_x + panel2_w - 25, dock_y + 70], radius=14, fill=(28, 28, 38), outline=(62, 62, 85))
    draw.text((panel2_x + 45, dock_y + 24), "Type your answer or explain the type casting mechanics...", fill=(130, 130, 145), font=f_body)

    draw_rounded_rect(draw, [panel2_x + panel2_w - 180, dock_y + 14, panel2_x + panel2_w - 40, dock_y + 56], radius=8, fill=(99, 102, 241))
    draw.text((panel2_x + panel2_w - 162, dock_y + 24), "Submit Answer  ↵", fill=(255, 255, 255), font=f_body_b)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(output_path)


if __name__ == "__main__":
    out_dir = ROOT / "app" / "data" / "ui_concepts"
    render_concept1(out_dir / "concept1_codex_dark_studio.png")
    render_concept2(out_dir / "concept2_dual_engine_split.png")
    render_concept3(out_dir / "concept3_cyber_lattice_cockpit.png")
    print(f"Rendered 3 mockup images to: {out_dir}")
