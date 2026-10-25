"""Build the IEEE-style paper draft PDF.

    ./.venv/Scripts/python.exe build_paper_pdf.py

Two-column US-Letter layout with a full-width title block, Times body text,
booktabs-style tables and two line-art figures. Every number in Tables I-IV is
read from backend/experiments/results.json, so the paper cannot drift away from
the harness output; regenerate the harness first if you change the system.
"""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

HERE = Path(__file__).parent
OUT = HERE / "MindWeave-R_IEEE_Paper_Draft.pdf"
RESULTS = HERE / "backend" / "experiments" / "results.json"

# --------------------------------------------------------------------- geometry
PW, PH = LETTER
M = 0.72 * inch             # side margin
GAP = 0.24 * inch           # column gutter
B = 0.62 * inch             # bottom margin
CW = (PW - 2 * M - GAP) / 2  # single column width
FULL = 2 * CW + GAP

# ------------------------------------------------------------------------ fonts
FONT = "TNR"
try:
    pdfmetrics.registerFont(TTFont("TNR", "C:/Windows/Fonts/times.ttf"))
    pdfmetrics.registerFont(TTFont("TNR-Bold", "C:/Windows/Fonts/timesbd.ttf"))
    pdfmetrics.registerFont(TTFont("TNR-Italic", "C:/Windows/Fonts/timesi.ttf"))
    pdfmetrics.registerFont(TTFont("TNR-BoldItalic", "C:/Windows/Fonts/timesbi.ttf"))
    pdfmetrics.registerFontFamily(
        "TNR", normal="TNR", bold="TNR-Bold", italic="TNR-Italic", boldItalic="TNR-BoldItalic"
    )
except Exception:  # pragma: no cover - fallback for machines without Times
    FONT = "Times-Roman"

def _s(name, size, leading, font="TNR", align=TA_JUSTIFY, **kw):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading, alignment=align, **kw)

ST = {
    "title": _s("title", 18, 21.5, "TNR-Bold", TA_CENTER, spaceAfter=10),
    "author": _s("author", 10.5, 13, "TNR", TA_CENTER, spaceAfter=2),
    "affil": _s("affil", 8.8, 10.5, "TNR-Italic", TA_CENTER, spaceAfter=1),
    "abshead": _s("abshead", 8.8, 10.6, "TNR-Bold", TA_LEFT, spaceAfter=2),
    "abstract": _s("abstract", 8.8, 10.5, "TNR", TA_JUSTIFY, spaceAfter=6),
    "H1": _s("H1", 9.4, 11.4, "TNR-Bold", TA_CENTER, spaceBefore=10, spaceAfter=4),
    "H2": _s("H2", 9.2, 11, "TNR-Italic", TA_LEFT, spaceBefore=6, spaceAfter=2),
    "B": _s("B", 9.2, 11.2, "TNR", TA_JUSTIFY, spaceAfter=4),
    "B1": _s("B1", 9.2, 11.2, "TNR", TA_JUSTIFY, spaceAfter=4, leftIndent=11),
    "EQ": _s("EQ", 9.2, 11.4, "TNR", TA_CENTER, spaceBefore=2, spaceAfter=5),
    "CAP": _s("CAP", 7.8, 9.3, "TNR", TA_JUSTIFY, spaceAfter=8),
    "TCAP": _s("TCAP", 7.8, 9.3, "TNR", TA_CENTER, spaceAfter=2),
    "TH": _s("TH", 6.8, 7.8, "TNR-Bold", TA_CENTER, spaceBefore=0, spaceAfter=0),
    "TD": _s("TD", 6.8, 7.8, "TNR", TA_CENTER, spaceBefore=0, spaceAfter=0),
    "TDL": _s("TDL", 6.8, 7.8, "TNR", TA_LEFT, spaceBefore=0, spaceAfter=0),
    "REF": _s("REF", 7.4, 8.8, "TNR", TA_JUSTIFY, spaceAfter=1.6, leftIndent=13, firstLineIndent=-13),
}

STORY: list[Flowable] = []


def P(text: str, style: str = "B"):
    STORY.append(Paragraph(text, ST[style]))


def H1(text: str):
    STORY.append(Paragraph(text.upper(), ST["H1"]))


def H2(text: str):
    STORY.append(Paragraph(text, ST["H2"]))


def EQ(text: str):
    STORY.append(Paragraph(text, ST["EQ"]))


# ------------------------------------------------------------------- references
REFS: list[tuple[str, str]] = [
    ("deelman", 'E. Deelman, K. Vahi, M. Rynge, R. Mayani, R. Ferreira da Silva, G. Papadimitriou, and M. Livny, '
                '"The evolution of the Pegasus workflow management software," <i>Computing in Science &amp; Engineering</i>, '
                'vol. 21, no. 4, pp. 22-36, 2019.'),
    ("li2021", 'Z. Li <i>et al.</i>, "Real-time and dynamic fault-tolerant scheduling for '
               'scientific workflows in clouds," <i>Information Sciences</i>, vol. 568, pp. 13-39, 2021.'),
    ("baylor", 'D. Baylor <i>et al.</i>, "TFX: A TensorFlow-based production-scale machine learning platform," in '
               '<i>Proc. 23rd ACM SIGKDD</i>, 2017, pp. 1387-1395.'),
    ("schelter", 'S. Schelter, D. Lange, P. Schmidt, M. Celikel, F. Biessmann, and A. Grafberger, "Automating '
                 'large-scale data quality verification," <i>Proc. VLDB Endow.</i>, vol. 11, no. 12, pp. 1781-1794, 2018.'),
    ("caveness", 'E. Caveness, P. Suganthan G. C., Z. Peng, N. Polyzotis, S. Roy, and M. Zinkevich, "TensorFlow Data '
                 'Validation: Data analysis and validation in continuous ML pipelines," in <i>Proc. ACM SIGMOD</i>, '
                 '2020, pp. 2793-2796.'),
    ("tu", 'D. Tu, Y. He, W. Cui, S. Ge, H. Zhang, S. Han, D. Zhang, and S. Chaudhuri, "Auto-Validate by-History: '
           'Auto-program data quality constraints to validate recurring data pipelines," in <i>Proc. 29th ACM SIGKDD</i>, '
           '2023, pp. 4991-5003.'),
    ("curino", 'C. A. Curino, H. J. Moon, and C. Zaniolo, "Graceful database schema evolution: the PRISM workbench," '
               '<i>Proc. VLDB Endow.</i>, vol. 1, no. 1, pp. 761-772, 2008.'),
    ("rupprecht", 'L. Rupprecht, J. C. Davis, C. Arnold, Y. Gur, and D. Bhagwat, "Improving reproducibility of data '
                  'science pipelines through transparent provenance capture," <i>Proc. VLDB Endow.</i>, vol. 13, no. 12, '
                  'pp. 3354-3368, 2020.'),
    ("yao", 'S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. Narasimhan, and Y. Cao, "ReAct: Synergizing reasoning and '
            'acting in language models," in <i>Proc. ICLR</i>, 2023.'),
    ("wu", 'Q. Wu, G. Bansal, J. Zhang, <i>et al.</i>, "AutoGen: Enabling next-gen LLM applications via multi-agent '
           'conversation," arXiv:2308.08155, 2023.'),
    ("hong", 'S. Hong, M. Zhuge, J. Chen, <i>et al.</i>, "MetaGPT: Meta programming for a multi-agent collaborative '
             'framework," in <i>Proc. ICLR</i>, 2024.'),
    ("cemri", 'M. Cemri, M. Z. Pan, S. Yang, <i>et al.</i>, "Why do multi-agent LLM systems fail?" in <i>Proc. NeurIPS '
              'Datasets and Benchmarks</i>, 2025.'),
    ("shinn", 'N. Shinn, F. Cassano, E. Berman, A. Gopinath, K. Narasimhan, and S. Yao, "Reflexion: Language agents with '
              'verbal reinforcement learning," in <i>Proc. NeurIPS</i>, 2023.'),
    ("madaan", 'A. Madaan, N. Tandon, P. Gupta, <i>et al.</i>, "Self-Refine: Iterative refinement with self-feedback," '
               'in <i>Proc. NeurIPS</i>, 2023.'),
    ("gou", 'Z. Gou, Z. Shao, Y. Gong, Y. Shen, Y. Yang, N. Duan, and W. Chen, "CRITIC: Large language models can '
            'self-correct with tool-interactive critiquing," in <i>Proc. ICLR</i>, 2024.'),
    ("ruan", 'Y. Ruan, H. Dong, A. Wang, <i>et al.</i>, "Identifying the risks of LM agents with an LM-emulated '
             'sandbox," in <i>Proc. ICLR</i>, 2024.'),
    ("legoues", 'C. Le Goues, M. Pradel, and A. Roychoudhury, "Automated program repair," <i>Communications of the '
                'ACM</i>, vol. 62, no. 12, pp. 56-65, 2019.'),
    ("zhang", 'Q. Zhang, C. Fang, Y. Ma, <i>et al.</i>, "A survey of learning-based automated program repair," <i>ACM '
              'Trans. Softw. Eng. Methodol.</i>, vol. 33, no. 2, art. 55, 2024.'),
    ("scala", 'E. Scala, "Plan repair for resource constrained tasks via numeric macro actions," in <i>Proc. ICAPS</i>, '
              'vol. 24, no. 1, 2014, pp. 280-288.'),
    ("fahland", 'D. Fahland and W. M. P. van der Aalst, "Model repair - aligning process models to reality," '
                '<i>Information Systems</i>, vol. 47, pp. 220-243, 2015.'),
    ("polyvyanyy", 'A. Polyvyanyy, W. M. P. van der Aalst, A. H. M. ter Hofstede, and M. T. Wynn, "Impact-driven process '
                   'model repair," <i>ACM Trans. Softw. Eng. Methodol.</i>, vol. 25, no. 4, art. 28, 2016.'),
    ("moreau", 'L. Moreau, P. Groth, J. Cheney, T. Lebo, and S. Miles, "The rationale of PROV," <i>Journal of Web '
               'Semantics</i>, vol. 35, pp. 235-257, 2015.'),
    ("schneier", 'B. Schneier and J. Kelsey, "Secure audit logs to support computer forensics," <i>ACM Trans. Inf. Syst. '
                 'Secur.</i>, vol. 2, no. 2, pp. 159-176, 1999.'),
    ("green", 'B. Green, "The flaws of policies requiring human oversight of government algorithms," <i>Computer Law '
              '&amp; Security Review</i>, vol. 45, art. 105681, 2022.'),
    ("cobbe", 'J. Cobbe, M. S. A. Lee, and J. Singh, "Reviewable automated decision-making: A framework for accountable '
              'algorithmic systems," in <i>Proc. ACM FAccT</i>, 2021.'),
]
REF_NUM: dict[str, int] = {}


def cite(*keys: str) -> str:
    out = []
    for k in keys:
        if k not in dict(REFS):
            raise KeyError(f"unknown reference key: {k}")
        if k not in REF_NUM:
            REF_NUM[k] = len(REF_NUM) + 1
        out.append(f"[{REF_NUM[k]}]")
    return ", ".join(out)


# ---------------------------------------------------------------------- figures
GRAY = colors.Color(0.28, 0.28, 0.28)


def _box(c, x, y, w, h, lines, size=6.1):
    c.setLineWidth(0.65)
    c.setStrokeGray(0.15)
    c.roundRect(x, y, w, h, 2.5, stroke=1, fill=0)
    c.setFillGray(0.12)
    n = len(lines)
    for i, line in enumerate(lines):
        yy = y + h / 2 - 2.6 + (n - 1 - i) * (size + 1.4) - (size + 1.4) / 2 + (size + 1.4) / 2
        c.setFont(FONT, size)
        c.drawCentredString(x + w / 2, y + h / 2 - 2.6 + ((n - 1) / 2 - i) * (size + 1.4), line)


def _arrow(c, x1, y1, x2, y2, head=3.4):
    import math

    c.setLineWidth(0.65)
    c.setStrokeGray(0.15)
    c.line(x1, y1, x2, y2)
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    px, py = -uy * head * 0.42, ux * head * 0.42
    c.setFillGray(0.15)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - head * ux + px, y2 - head * uy + py)
    p.lineTo(x2 - head * ux - px, y2 - head * uy - py)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.setFillGray(0)


class FigArchitecture(Flowable):
    """Request path and the four components the engine invokes per edge."""

    def __init__(self):
        super().__init__()
        self.width, self.height = CW, 112

    def draw(self):
        c = self.canv
        _box(c, 0, 74, 62, 30, ["Workflow canvas", "React + React Flow"])
        _box(c, 84, 74, 50, 30, ["REST API", "FastAPI"])
        _box(c, 156, 74, 87, 30, ["Execution engine", "NetworkX topological order"])
        _arrow(c, 62, 89, 84, 89)
        _arrow(c, 134, 89, 156, 89)

        xs = [0, 62.5, 125, 187.5]
        labels = [["Static", "validator"], ["Contract", "check"], ["Repair", "selector"], ["Certificate", "+ SQLite"]]
        for x, lab in zip(xs, labels):
            _box(c, x, 12, 55.5, 32, lab)

        # distribution bus from the engine down to the four per-edge components
        c.setLineWidth(0.5)
        c.setStrokeGray(0.35)
        c.line(199.5, 74, 199.5, 62)
        c.line(27.7, 62, 199.5, 62)
        for x in xs:
            c.line(x + 27.7, 62, x + 27.7, 44)
        c.setStrokeGray(0.15)
        c.setFont(FONT, 5.6)
        c.setFillGray(0.35)
        c.drawString(2, 65.5, "per edge")


class FigRepairLoop(Flowable):
    """Detect, generate, filter, select, apply."""

    def __init__(self):
        super().__init__()
        self.width, self.height = CW, 100

    def draw(self):
        c = self.canv
        _box(c, 0, 62, 40, 28, ["artifact", "a"], 6.4)
        _box(c, 56, 62, 58, 28, ["check C(e)", "six predicates"])
        _box(c, 146, 62, 62, 28, ["downstream", "node executes"])
        _arrow(c, 40, 76, 56, 76)
        _arrow(c, 114, 76, 146, 76)
        c.setFont(FONT, 5.6)
        c.setFillGray(0.3)
        c.drawString(119, 78.6, "pass")

        xs = [0, 49.5, 99, 148.5, 198]
        labels = [["failure", "codes"], ["repair", "candidates"], ["budget", "filter"], ["weighted", "selection"], ["apply to", "artifact"]]
        for x, lab in zip(xs, labels):
            _box(c, x, 12, 44, 30, lab, 5.9)
        for i in range(4):
            _arrow(c, xs[i] + 44, 27, xs[i + 1], 27)

        # fail branch
        _arrow(c, 85, 62, 85, 42)
        c.setFont(FONT, 5.6)
        c.setFillGray(0.3)
        c.drawString(88, 50, "violated")

        # repaired artifact returns to the check
        c.setLineWidth(0.55)
        c.setStrokeGray(0.45)
        c.setDash([1.7, 1.5])
        c.line(220, 42, 220, 52)
        c.line(110, 52, 220, 52)
        c.setDash([])
        c.setStrokeGray(0.15)
        _arrow(c, 110, 52, 110, 62)
        c.setFont(FONT, 5.6)
        c.setFillGray(0.3)
        c.drawString(196, 54.2, "a'")


# ---------------------------------------------------------------------- helpers
def table(num: str, title: str, header: list[str], rows: list[list[str]], widths: list[float], left_first=True):
    data = [[Paragraph(h, ST["TH"]) for h in header]]
    for r in rows:
        cells = []
        for i, cell in enumerate(r):
            cells.append(Paragraph(str(cell), ST["TDL"] if (left_first and i == 0) else ST["TD"]))
        data.append(cells)
    t = Table(data, colWidths=widths, hAlign="CENTER")
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1.25),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.25),
                ("LEFTPADDING", (0, 0), (-1, -1), 1.6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1.6),
                ("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.45, colors.black),
                ("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.black),
            ]
        )
    )
    block = [
        Paragraph(f"TABLE {num}", ST["TCAP"]),
        Paragraph(title, ST["CAP"]),
        t,
        Spacer(1, 9),
    ]
    STORY.append(KeepTogether(block))


def figure(flowable: Flowable, caption: str):
    STORY.append(KeepTogether([Spacer(1, 2), flowable, Spacer(1, 2.5), Paragraph(caption, ST["CAP"])]))


# ---------------------------------------------------------------------- numbers
R = json.loads(RESULTS.read_text(encoding="utf-8"))
META = R["meta"]
E1 = R["e1_end_to_end"]
E2 = R["e2_gate_ablation"]
E3 = R["e3_compound"]
E4 = R["e4_selection"]
E5 = R["e5_healthy"]
HEALTHY = f"{E5['healthy_runs']} healthy control runs produced {E5['repairs']} repairs and {E5['violations']} violations at {E5['credits']:.0f} credits, equal to the nominal workflow cost"
OVERHEAD = sorted({r["repair_overhead_pct"] for r in E1})
CREDITS = sorted({r["credits"] for r in E1})


def yn(v) -> str:
    return "yes" if v else "no"


# ------------------------------------------------------------------------ title
TITLE_BLOCK = [
    Paragraph("MindWeave-R: Contract-Aware Detection and Budgeted Repair of Artifacts in Multi-Agent Workflows",
              ST["title"]),
    Paragraph("Minal Barhate, [Author 2], [Author 3]", ST["author"]),
    Paragraph("Vishwakarma Institute of Technology, Pune, Maharashtra, India", ST["affil"]),
    Paragraph("[author emails to be added]", ST["affil"]),
    Spacer(1, 10),
    Paragraph(
        "<b><i>Abstract</i></b>&mdash;Multi-agent workflows chain language-model agents through a directed graph, and every connection "
        "silently assumes something about the data crossing it: that fields exist, that confidence is high "
        "enough, that provenance is intact, that the payload is fresh and within budget. When an assumption "
        "breaks, most orchestrators either continue with degraded data or abort the run. We present MindWeave-R, "
        "a system in which each edge carries an executable contract and a failed check triggers a budgeted repair "
        "decision instead of termination. On failure the engine classifies the violation into one of six codes, "
        "generates the repair operators that cover every violated code, selects among budget-feasible candidates by "
        "a weighted cost, latency, privacy and residual-risk score, applies the repair to the artifact, and commits "
        "a Merkle-rooted certificate over the trace. We evaluate a seven-node research workflow under 180 synthetic "
        "fault injections across six classes. All 180 were detected, and every repaired artifact satisfied its "
        "contract when re-checked, at "
        "4.5 to 18.2 percent credit overhead, with no repair on 30 healthy control runs. Disabling the gate exposed "
        "the violation in all six classes and every violating artifact was consumed downstream while the run still "
        "reported completion. Three negative findings matter more than the positive one: single-code faults always "
        "admit exactly one candidate, so the ranking rule is never exercised by the deployed catalogue; compound "
        "violations admit no candidate at all; and 'repaired' does not mean 'valid', because five of our six "
        "operators leave the payload untouched and the sixth inserts a placeholder. We argue that contract "
        "satisfaction must be re-checked after repair, "
        "and we report the places where our own implementation does not.",
        ST["abstract"],
    ),
    Paragraph("<b><i>Index Terms</i></b>&mdash;Multi-agent systems, workflow orchestration, data contracts, "
              "automated repair, provenance, auditability.", ST["abstract"]),
    Spacer(1, 4),
]


# ------------------------------------------------------------------------- body
H1("I. Introduction")
P("Multi-agent workflows have become a standard way to build applications on top of large language models. A "
  "reasoning agent gathers evidence, a second validates it, a third drafts, a fourth checks the draft, and a human "
  "approves the result before release " + cite("yao", "wu", "hong") + ". Canvas-based orchestrators have followed, "
  "letting a user wire such agents into a directed acyclic graph and run it, which makes the composition itself the "
  "object of design rather than the prompt.")
P("Composition introduces a failure mode that single-agent work does not have. Each connection carries assumptions "
  "about the data crossing it: that a field exists, that confidence exceeds some threshold, that the payload is "
  "recent, that provenance is intact, that it is not too expensive, and that it is not classified more sensitively "
  "than the receiving side may handle. In most systems none of these assumptions is expressed where the runtime can "
  "check it. When one breaks, the artifact moves on. A recent empirical taxonomy of multi-agent failures places "
  "verification and inter-agent misalignment among the dominant causes " + cite("cemri") + ", and role-based agent "
  "pipelines report hallucination cascading through unverified intermediate outputs " + cite("hong") + ".")
P("Systems research offers two adjacent answers, and neither fits. Orchestrators handle infrastructure faults such "
  "as lost workers, timeouts and host failure with retries, replication and rescheduling " + cite("deelman", "li2021") +
  "; but a task that completes successfully and emits unusable data is not a fault in that sense, and retrying it "
  "reproduces the same artifact. Data-validation systems evaluate expectations at pipeline boundaries "
  + cite("schelter", "caveness") + " and can learn constraints from execution history " + cite("tu") + "; but they "
  "report and halt, leaving the next decision to a person.")
P("The repair literature is mature in three neighbouring domains. Automated program repair localises a fault, "
  "generates candidate patches and validates against an oracle " + cite("legoues", "zhang") + ". Plan repair "
  "restores a plan that has become infeasible, including under numeric resource constraints " + cite("scala") +
  ". Process-model repair aligns a model with observed behaviour " + cite("fahland", "polyvyanyy") + ". All three "
  "share the pipeline shape we adopt; none operates on a runtime data artifact at a graph edge, and none selects a "
  "remedy under a hard spend budget with privacy exposure and residual failure risk as competing costs.")
P("This paper presents MindWeave-R, a workflow system in which connections are executable contracts and a failed "
  "check produces a budgeted repair decision rather than a termination. Our contributions are:")
P("<b>(C1)</b> a formulation of edge contracts as first-class runtime predicates with a six-code failure taxonomy, "
  "evaluated against the artifact rather than against the agent;", "B1")
P("<b>(C2)</b> a repair pipeline, comprising code classification, coverage-filtered candidate generation, "
  "budget-feasible weighted selection and artifact-level application that preserves acyclicity by construction, in "
  "which the selection objective trades spend against latency, privacy exposure and residual failure risk;", "B1")
P("<b>(C3)</b> an audit certificate that commits, under a single Merkle root, to the execution trace, the repair "
  "decisions and the final artifact, making the decision replayable rather than only the outcome inspectable;", "B1")
P("<b>(C4)</b> an empirical characterisation over " + str(META["total_injections"]) + " injected faults in six "
  "classes, including a gate ablation, a healthy control, and two negative results that bound what the system "
  "actually establishes.", "B1")
P("We are explicit about scope. We do not propose a new repair algorithm, and we claim no novelty in ranking, in "
  "hash trees or in approval gates. Our claim is about the combination and about where the decision boundary is "
  "drawn. Sections VII and VIII report where our implementation falls short of its own design.")

H1("II. Related Work")
H2("A. Workflow Orchestration and Fault Tolerance")
P("Workflow management systems separate the description of a computation from its execution, which is what allows "
  "an abstract graph to be mapped onto available resources; Pegasus has done so in production for two decades "
  + cite("deelman") + ". Production machine-learning platforms extend the model to analysis, validation and serving "
  "stages " + cite("baylor") + ". Fault tolerance in this tradition is about availability: replication, checkpointing "
  "and dynamic rescheduling keep a workflow alive when infrastructure fails " + cite("li2021") + ".")
P("Our faults differ in kind. The node succeeds, the edge is traversed, and what crosses it is wrong. No amount of "
  "retrying discovers this, because the retry is deterministic in the same way. This is why we locate the check at "
  "the edge rather than at the scheduler, and why uptime and completion rate are the wrong instruments for "
  "measuring it.")

H2("B. Data Validation and Contracts")
P("Declarative, expectation-based validation is well established. Deequ computes data-quality constraints at scale "
  "and frames them as unit tests for data " + cite("schelter") + "; TensorFlow Data Validation infers and enforces "
  "schemas at pipeline boundaries " + cite("caveness") + "; Auto-Validate learns validation programs from the "
  "history of recurring pipelines " + cite("tu") + ". Schema evolution has its own body of work, of which PRISM is a "
  "canonical system " + cite("curino") + ", and provenance capture for reproducibility is addressed by systems such "
  "as Ursprung " + cite("rupprecht") + ".")
P("What this literature does not provide is a decision procedure after detection, and constraints are generally "
  "attached to a pipeline rather than to a connection. The distinction matters for agent graphs: two edges leaving "
  "the same node may legitimately require different confidence thresholds, and it is the edge, not the pipeline, "
  "that carries the assumption.")

H2("C. Reliability of LLM Agents")
P("Agent design has been improved from several directions: the reason-act-observe loop " + cite("yao") + ", "
  "conversational multi-agent frameworks " + cite("wu") + ", role-specialised pipelines with standardised operating "
  "procedures " + cite("hong") + ", self-critique " + cite("shinn", "madaan") + ", and critique grounded in external "
  "tools " + cite("gou") + ". Risk evaluation for tool-using agents has been studied in emulated environments "
  + cite("ruan") + ". The MAST taxonomy " + cite("cemri") + " is the most direct evidence that verification is where "
  "these systems break, grouping fourteen failure modes into system design, inter-agent misalignment and task "
  "verification.")
P("Almost all of this work improves the agent. We take agents as given and constrain their handoffs, which makes "
  "the approach composable with any of it. It is also why our checker does not ask the agent to assess itself: "
  "self-assessment has repeatedly been shown weaker than external verification " + cite("gou") + ".")

H2("D. Automated Repair")
P("The structure of program repair, localise then generate then validate, is the template we follow "
  + cite("legoues") + ", and its literature is a warning as much as a guide: a patch that satisfies the oracle may "
  "still be wrong, which is the central open problem of the field " + cite("zhang") + ". Plan repair under numeric "
  "resource constraints " + cite("scala") + " is the closest formal precedent for our budget constraint. "
  "Process-model repair operates offline against event logs " + cite("fahland", "polyvyanyy") + " and addresses "
  "structure rather than data.")
P("We borrow the pipeline and the caution. Our repair acts on a single artifact, the candidate set is derived from "
  "the violated codes rather than from a search over patches, and the objective combines four costs under one hard "
  "constraint.")

H2("E. Provenance, Audit and Oversight")
P("PROV supplies the vocabulary of entities, activities and agents that we deliberately simplify " + cite("moreau") +
  ". Tamper-evident logging by hash chaining is old and well understood, including its limits: without a trusted "
  "time source or a key, a hash chain establishes integrity and nothing more " + cite("schneier") + ". On oversight, "
  "Green shows that mandating a human in the loop does not by itself produce meaningful review " + cite("green") +
  ", and Cobbe <i>et al.</i> frame reviewability as the property that makes a decision interrogable after the fact "
  + cite("cobbe") + ".")
P("We take the last point as a design requirement: what should be committed is not only the output but the reason a "
  "particular remedy was chosen.")

H2("F. Positioning")
P("Three gaps follow. <b>G1:</b> validators detect but do not decide, and enforcement is a deployment policy rather "
  "than a specified procedure at runtime and per connection. <b>G2:</b> repair exists for code, plans and process "
  "models, but no prior work selects among artifact-level repair operators under a hard spend budget together with "
  "privacy and residual-failure risk. <b>G3:</b> provenance and tamper-evident logging exist separately from "
  "repair, so the <i>choice</i> of remedy is not typically auditable. MindWeave-R addresses the three as one "
  "mechanism; nothing below should be read as a claim that any single component is new.")

H1("III. Problem Formulation")
P("<b>Definition 1 (workflow).</b> A workflow is a pair W = (V, E) where E is a subset of V x V and (V, E) is a "
  "directed acyclic graph. Each node v has a kind k(v) drawn from a fixed catalogue, and each kind declares an "
  "output field set O(k).")
P("<b>Definition 2 (artifact).</b> An artifact is a tuple a = (kind, payload, prov, conf, priv, t, cost, h), where "
  "payload is a mapping from field names to values, prov is a list of lineage tokens, conf is in [0, 1], priv is "
  "one of public, internal or confidential with the order 0 &lt; 1 &lt; 2, t is a creation timestamp, cost is "
  "expressed in credits, and h is a SHA-256 digest over the canonical JSON encoding of the other seven members.")
P("<b>Definition 3 (contract).</b> Each edge e = (u, v) carries a contract c = (F, \u03c4, \u03c0, \u0394, B, "
  "\u03c1) where F is a set of required field names, \u03c4 a minimum confidence, \u03c0 a maximum privacy "
  "classification, \u0394 a freshness window in seconds, B a cost ceiling in credits, and \u03c1 a Boolean "
  "requirement that provenance be non-empty.")
P("<b>Definition 4 (violation).</b> An artifact a violates c if its code set is non-empty, where")
EQ("codes(a, c) = { schema if F is not a subset of fields(payload);<br/>"
   "confidence if conf &lt; \u03c4; privacy if priv(a) &gt; \u03c0;<br/>"
   "freshness if now - t &gt; \u0394; budget if cost(a) &gt; B;<br/>"
   "provenance if \u03c1 and prov is empty }.")
P("<b>Definition 5 (repair operator).</b> An operator is a tuple o = (id, \u03ba, \u03bb, p, r, X), where \u03ba is "
  "its cost in credits, \u03bb a latency class, p a privacy-exposure risk, r a residual failure risk, and X a "
  "non-empty subset of codes it is declared to fix. Operator o covers a violation with code set K if K is a subset "
  "of X, and is feasible if \u03ba(o) does not exceed the remaining budget.")
P("<b>Problem (repair selection).</b> Given a violating artifact a, a contract c and a remaining budget, choose")
EQ("o* = arg min over feasible covering o of<br/>"
   "\u03b1\u00b7\u03ba(o) + \u03b2\u00b7\u03bb(o) + \u03b3\u00b7p(o) + \u03b4\u00b7r(o)")
P("and if no feasible covering operator exists, block the edge. The four weights encode a deliberately asymmetric "
  "loss: blocking is safe but consumes human attention, whereas repairing is cheap but injects risk, so r is "
  "weighted above \u03ba by a factor of six. Our implementation uses (\u03b1, \u03b2, \u03b3, \u03b4) = "
  "(1, 0.2, 4, 6). These are design weights, not a calibrated utility model, and we do not claim they are optimal.")
P("<b>Definition 6 (certificate).</b> A run produces leaves L = {H(x) for x in trace} plus {H(y) for y in "
  "repairs} plus {h_final}. The certificate root is the Merkle reduction of L under pairwise SHA-256, "
  "duplicating the final leaf when the layer length is odd.")

H1("IV. Method")
figure(FigArchitecture(),
       "<b>Fig. 1.</b> System structure. The canvas issues REST calls; the engine orders nodes topologically and, "
       "per edge, invokes the static validator once per graph and the contract check, repair selector and "
       "certificate builder per completed artifact.")
H2("A. Contracts on Edges")
P("A contract belongs to the connection, not to the node, because the handoff is where the assumption lives. The "
  "same artifact may be checked against several outgoing contracts with different thresholds, and may satisfy one "
  "while violating another; that case is handled by repairing per edge, so the downstream node receives an "
  "artifact conforming to the contract it actually traversed.")
P("Before execution, a static pass rejects graphs that are cyclic, that reference a missing endpoint, that carry a "
  "malformed contract, that require a field the source cannot produce, whose edge privacy exceeds the receiving "
  "node's declared maximum, or in which some output node is not reachable from an approval node. Confidence, "
  "freshness and budget are properties of a concrete artifact and are therefore not statically decidable; they are "
  "enforced only at runtime.")

H2("B. Detection")
P("After a node completes, its artifact is tested against each outgoing contract. The six predicates are evaluated "
  "independently and reported together, so one artifact can carry several codes at once. This matters for "
  "candidate generation below, and it is where our design turns out to be weakest.")

H2("C. Candidate Generation")
P("The pool is every operator whose fix set is a superset of the violated codes. The coverage rule is "
  "intentional: it prevents a partial remedy from being applied to a compound violation and then reported as a "
  "repair. Its consequence is that a violation whose codes no single operator covers yields an empty pool and "
  "blocks the run. Section VII-D measures exactly this case.")

H2("D. Selection")
P("Feasible candidates are ordered by the weighted score of Section III. Ties break on catalogue order rather than "
  "at random, because a deterministic choice is what makes a certificate replayable: the same artifact, contract and "
  "budget must always select the same operator.")
figure(FigRepairLoop(),
       "<b>Fig. 2.</b> Per-edge repair loop. A completed artifact is checked against the outgoing contract; on "
       "failure the codes select operators from the catalogue, the budget filter removes unaffordable ones, the "
       "weighted rule picks one, and the repaired artifact a' is what the downstream node consumes "
       "(dashed path). The certificate commits to the whole sequence.")

H2("E. Application")
P("A repair rewrites the artifact, appends a lineage token naming the operator, recomputes the digest and passes "
  "the result downstream. Because no node or edge is added, the graph remains acyclic: the DAG invariant is "
  "preserved by construction rather than re-established by a reachability check. The alternative, inserting a "
  "repair subgraph, would require such a check before the artifact could be routed, and we do not implement it; "
  "our operators are artifact-local.")

H2("F. Certificate")
P("Each completed run with at least one repair stores a certificate: the ordered trace hashes, the repair records "
  "(before hash, after hash, codes, chosen operator, cost) and the final artifact hash, reduced to one root. The "
  "encoding is canonical JSON with sorted keys and no insignificant whitespace, so independent reimplementation "
  "yields the same root.")
P("What the root establishes is narrow, and we state it in the same terms as the audit-log literature "
  + cite("schneier") + ": it proves that the recorded sequence has not been altered since it was hashed. It does "
  "not prove authenticity, because nothing is signed; it does not prove completeness, because a run may simply "
  "record fewer events; and it says nothing about whether the repair was correct. It is a record, not a warranty.")

H2("G. The Approval Gate")
P("Independently of repair, the engine halts before any final output and waits for an explicit approval or "
  "rejection, recorded as an execution status change. This is a structural policy, enforced as reachability in the "
  "static pass. We note Green's argument " + cite("green") + " that a mandated human step is not by itself "
  "meaningful oversight, and we therefore claim only that our gate produces an auditable pause, not that it "
  "produces good review.")

H1("V. Implementation")
P("The engine and HTTP API are a single Python module of about 230 lines built on FastAPI and Pydantic v2, with "
  "NetworkX for topological ordering and SQLite for users, workflows, executions, artifacts and certificates. The "
  "client is a React and TypeScript canvas on React Flow with thirteen node kinds, a palette, an inspector for "
  "node guardrails and edge contracts, a trace strip and a wallet panel. Module nodes nest a saved workflow and "
  "recurse through the same engine with approvals disabled, which is what allows workflows to be composed "
  "hierarchically.")
P("Two implementation choices shape the evaluation. First, a wallet meter: each node kind has a credit price, a run "
  "is refused when the balance cannot cover the nominal cost, and a repair is charged on top. Second, a "
  "deterministic demo mode in which every agent emits synthetic, stable payloads and no model is called. Demo mode "
  "is what makes the fault-injection experiments below exactly reproducible by hand or by script; it is also the "
  "largest threat to the validity of those experiments, and we return to this in Section VIII.")
P("All numbers reported here are produced by a harness of about 300 lines that imports the engine, injects faults, "
  "and writes the result tables; it runs in seconds with no network access. The seven unit tests shipped with the "
  "system cover authentication, workflow ownership, static validation, topological ordering, repair planning, "
  "certificate persistence and Merkle sensitivity.")

H1("VI. Experimental Setup")
P("We organise the study around four hypotheses, each of which our design can falsify:")
P("<b>H1.</b> The gate detects and repairs every single-code fault class it defines.", "B1")
P("<b>H2.</b> With the gate disabled, a violating artifact reaches downstream agents and the run still completes.", "B1")
P("<b>H3.</b> Single-code faults admit exactly one candidate, and compound faults admit none.", "B1")
P("<b>H4.</b> The weighted rule differs from cost-only, risk-only and order-first baselines on the same pool.", "B1")
P("The subject is the Evidence Research template: seven nodes and six edges, from topic input through researcher, "
  "curator, validator, writer and approval to final output, at a nominal cost of " +
  str(META["nominal_workflow_cost"]) + " credits against a wallet of " + str(int(META["wallet"])) + ". A fault is "
  "injected at the researcher's output by a backdoor field on the node, and the contract on the researcher to "
  "curator edge is tightened so that the injected condition is the condition violated. The six classes are: low "
  "confidence (0.10 against a threshold of 0.80); a dropped required field; emptied provenance with provenance "
  "required; a confidentiality downgrade from the artifact's classification to a public contract; a stale "
  "timestamp against a one-second window; and an artifact cost above a contract ceiling.")
P("Each class is run " + str(META["repetitions_per_class"]) + " times, for " + str(META["total_injections"]) +
  " injections in total, and a further 30 healthy runs form a control. Because the agents are deterministic, all "
  "repetitions of a class are byte-identical; the harness asserts this. We therefore report per-class outcomes "
  "rather than distributional statistics, and " + str(META["total_injections"]) + " injections are six behaviours "
  "repeated, not 180 independent samples. No significance test would be meaningful here and none is reported.")

H1("VII. Results and Discussion")
P("Table I reports the per-class outcome. Every injection was detected with exactly the expected code, the "
  "corresponding operator was selected, and the artifact satisfied its contract when re-checked immediately after "
  "repair. Repair cost ranged from 0.5 to 2 credits against a nominal workflow cost of 11, an overhead of "
  + f"{OVERHEAD[0]:.1f}" + " to " + f"{OVERHEAD[-1]:.1f}" + " percent, and the total charge per repaired run moved "
  "from 11 to " + f"{CREDITS[0]:.0f}-{CREDITS[-1]:.0f}" + " credits.")
table("I", "Per-class outcome over 30 injections per class. All repetitions within a class were identical. "
           "\u201cPost\u201d is the contract check applied to the repaired artifact; \u201cPayload\u201d records "
           "whether the payload content changed at all.",
      ["Fault class", "Selected operator", "Post", "Payload", "Credits", "Overhead"],
      [[r["fault"], r["repair_applied"], yn(r["post_repair_satisfied"]), yn(r["payload_changed"]),
        f"{r['credits']:.0f}", f"{r['repair_overhead_pct']:.1f}%"] for r in E1],
      [42, 62, 26, 30, 32, 36])
P("The aggregate figure, six of six classes repaired, invites a stronger conclusion than the data supports, and "
  "three observations argue against it.")
P("<b>Finding 1 (degenerate selection).</b> The candidate pool contained exactly one operator in every single-code "
  "case. The catalogue maps each code to one operator, so the coverage rule leaves the ranking rule nothing to "
  "rank, and Table I is a table of detections rather than of decisions. Contribution C2's selection stage is "
  "implemented and unit-tested on constructed pools, but the deployed catalogue never exercises it. This is a "
  "property of our operator set, not of the formulation; a realistic catalogue with several operators per code, "
  "or with multi-code operators, would make the score decisive.")
P("<b>Finding 2 (satisfaction is not validity).</b> Re-checking the repaired artifact succeeded in all six classes, "
  "yet the payload changed in only one. The schema class is satisfied by inserting the literal string "
  "\u201crepaired:evidence\u201d in place of the dropped field. The confidence class is satisfied by assigning "
  "\u03c4 + 0.05, moving the artifact from 0.10 to 0.85 without any new evidence being gathered. The freshness "
  "operator rewrites the timestamp and leaves the content untouched. A presence-based schema predicate cannot "
  "distinguish a real field from a placeholder, and a threshold predicate cannot distinguish measured confidence "
  "from asserted confidence. This is the program-repair lesson " + cite("legoues", "zhang") + " reappearing one "
  "level up: passing the oracle is not being correct, and our oracle is weaker than a test suite.")
P("<b>Finding 3 (the gate does not change completion).</b> Table II reports the ablation. With enforcement "
  "disabled, the violation was detected by the same checker, the violating artifact was consumed by the next "
  "agent, and the run completed. With enforcement enabled, no violating artifact reached an agent, and the run "
  "still completed. Completion rate, the metric most commonly reported for orchestration systems, is identical in "
  "both conditions and therefore blind to the mechanism: the gate is an integrity barrier, not a liveness barrier, "
  "and a study measuring only success rate would conclude, wrongly, that contracts do nothing.")
table("II", "Gate ablation. \u201cConsumed\u201d: the violating artifact is used as input by a later node.",
      ["Fault class", "Off: consumed", "Off: repairs", "On: consumed", "On: repairs", "Run completes"],
      [[r["fault"], yn(r["off_consumed"]), str(r["off_repairs"]), yn(r["on_consumed"]), str(r["on_repairs"]),
        yn(r["off_status"] == "completed" and r["on_status"] == "completed")] for r in E2],
      [44, 42, 34, 40, 34, 40])
P("<b>Finding 4 (compound violations are unreachable).</b> Combining two codes on one artifact produced an empty "
  "pool in all three configurations tested, and execution stopped with a contract-repair error rather than "
  "proceeding (Table III). Combined with Finding 1, this means the system can repair exactly the violations for "
  "which it needs no decision, and cannot repair the ones where a decision would matter. The cause is structural: "
  "the coverage rule is a subset test and each operator fixes a single code. The obvious repairs are partial "
  "coverage with a residual code set that triggers a second round, or a compositional operator that is itself a "
  "small repair graph.")
table("III", "Compound violations. The pool is empty because no operator's fix set covers both codes.",
      ["Violated codes", "Candidates", "Outcome"],
      [[" + ".join(r["codes"]), str(r["candidate_pool"]), r["status"]] for r in E3],
      [96, 42, 92])
P("<b>Finding 5 (the rule discriminates when it is given a choice).</b> To exercise the score at all we "
  "constructed a pool of five multi-code operators with deliberately different cost and risk profiles and compared "
  "the proposed rule with three baselines (Table IV). The weighted rule selects an operator at 2.4 times the cost "
  "of the cheapest but with 30 percent of its residual risk; the cost-only baseline takes the cheap option at 0.30 "
  "residual failure risk; the risk-only and order-first baselines both take the most expensive option. The "
  "behaviour matches the intent of the weights, and the pool is constructed, not sampled from a real catalogue, so "
  "this is evidence that the rule is implemented as specified, not that it is a good rule.")
table("IV", "Selection rules on a constructed five-operator pool. All rules operate on the same candidates; only the "
            "choice differs. Score is the weighted objective at the selected point.",
      ["Rule", "Selected operator", "Cost", "Residual", "Score"],
      [[r["rule"].replace(" (proposed)", "").replace(" (catalogue order)", ""),
        r["selected"], f"{r['cost']:.1f}", f"{r['residual_failure_risk']:.2f}", f"{r['score']:.2f}"]
       for r in E4],
      [58, 76, 28, 32, 30])
P("<b>Finding 6 (cost is not the obstacle).</b> " + HEALTHY + ". Repair overhead is between "
  f"{OVERHEAD[0]:.1f}" + " and " + f"{OVERHEAD[-1]:.1f}" + " percent, and the most expensive repairs are the two "
  "that plausibly require work, recomputation and refetching. The mechanism is cheap enough that the interesting "
  "question is not its price but its correctness, which is what Findings 2 and 4 are about.")

H1("VIII. Threats to Validity")
P("<b>Construct validity.</b> The agents are deterministic stand-ins that emit synthetic payloads, so a repair "
  "operator that restores information and one that merely rewrites metadata are indistinguishable from the outside. "
  "Our operators are almost entirely of the second kind: five of the six leave the payload untouched and the "
  "sixth inserts a placeholder. The measured quantity is therefore "
  "\u201ccontract satisfaction after repair\u201d, and we have shown independently in Finding 2 that it "
  "over-reports validity. A second, independent validator, ideally one that inspects content rather than "
  "declarations, is required before any claim about repair quality.")
P("<b>Circularity.</b> The repaired artifact is re-checked by the same predicate that motivated the repair. A "
  "predicate can be satisfied by construction, as the schema case demonstrates. We report this rather than "
  "correcting for it, because the correction is exactly the future work.")
P("<b>Internal validity.</b> Faults enter through a backdoor field on the node that is not part of the production "
  "path, so the injected conditions are cleaner than real failures, which tend to be partial and correlated across "
  "a payload. The single template, seven nodes and one graph topology remove structural variation. Determinism "
  "removes variance and therefore also removes the possibility of estimating it; we state per-class behaviour "
  "instead of averages over draws.")
P("<b>External validity.</b> One workflow shape, a small node catalogue, no real model calls and no human "
  "participants. Nothing here licenses a claim about behaviour under production LLM agents, whose outputs vary "
  "between calls, or about the thirteen-node palette beyond the six kinds exercised.")
P("<b>Conclusion validity.</b> We report no comparison against a baseline system, no user study and no effect size, "
  "and we make no claim of improvement over the tools in Section II. The contribution demonstrated is that the "
  "mechanism operates as specified and that two specific design flaws are real and measurable.")
P("One methodological point deserves emphasis. Our first instrumentation recorded only whether a run succeeded, and "
  "by that measure the system repaired 180 of 180 faults with no exceptions. The caveats in Finding 2 exist only "
  "because we added a second, post-repair audit. A paper that stopped at the completion counter would have reported "
  "a cleaner and false result.")

H1("IX. Conclusion and Future Work")
P("We described a workflow system in which every connection carries an executable contract, a violated contract "
  "triggers a repair decision rather than a termination, and the decision is committed to an audit certificate. "
  "The mechanism works as specified on the six fault classes it defines, at a credit overhead of under one fifth of "
  "the nominal run cost, and is invisible to completion-rate measurement because it does not change whether a run "
  "finishes.")
P("The reported negative results define the next steps more sharply than the positive one. First, replace the "
  "simulated operators with real ones: re-execution with a different agent, retrieval refresh for staleness, and "
  "genuine schema enrichment, so that a repair can restore information rather than assert it. Second, re-validate "
  "after repair inside the engine, not only in the harness, and use a validator independent of the contract that "
  "triggered the repair. Third, relax coverage to partial coverage with a residual code set, which makes compound "
  "violations reachable. Fourth, enlarge the catalogue so the selection rule has something to select. Fifth, sign "
  "the certificate, turning an integrity record into an attributable one. Beyond the mechanism, the natural "
  "evaluation is the one we have not run: a within-subject comparison against an unconstrained canvas, measuring "
  "first-run success, invalid connections caught before execution, time to repair, unnecessary agent calls and "
  "user trust, with more than one template and real agents.")

refs = []
for key, text in sorted(REFS, key=lambda kv: REF_NUM.get(kv[0], 999)):
    if key not in REF_NUM:
        continue
    refs.append(Paragraph(f"[{REF_NUM[key]}]&nbsp;&nbsp;{text}", ST["REF"]))
# keep the heading with its first entry so it cannot be orphaned at a column foot
STORY.append(KeepTogether([Paragraph("REFERENCES", ST["H1"]), refs[0]]))
STORY.extend(refs[1:])

# ------------------------------------------------------------------------- build
def footer(canv, doc):
    canv.saveState()
    canv.setFont(FONT, 8)
    canv.setFillGray(0.2)
    canv.drawCentredString(PW / 2, 0.36 * inch, str(doc.page))
    canv.setFont(FONT, 6.4)
    canv.setFillGray(0.55)
    canv.drawString(M, 0.36 * inch, "Working draft - not for distribution")
    canv.restoreState()


def measure(flowables: list[Flowable], width: float) -> float:
    h = 0.0
    for f in flowables:
        _, fh = f.wrap(width, PH)
        h += fh
    return h


def build():
    title_h = measure(TITLE_BLOCK, FULL) + 4
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=LETTER,
        leftMargin=M,
        rightMargin=M,
        topMargin=M,
        bottomMargin=B,
        title="MindWeave-R: Contract-Aware Detection and Budgeted Repair of Artifacts in Multi-Agent Workflows",
        author="M. Barhate et al.",
        subject="Working draft",
    )
    col_h = PH - M - title_h - 6 - B
    pad = dict(leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0)
    frames_first = [
        Frame(M, PH - M - title_h, FULL, title_h, id="full", **pad),
        Frame(M, B, CW, col_h, id="l1", **pad),
        Frame(M + CW + GAP, B, CW, col_h, id="r1", **pad),
    ]
    two_h = PH - 2 * M
    frames_two = [
        Frame(M, B, CW, two_h, id="l2", **pad),
        Frame(M + CW + GAP, B, CW, two_h, id="r2", **pad),
    ]
    doc.addPageTemplates(
        [
            PageTemplate(id="first", frames=frames_first, onPage=footer),
            PageTemplate(id="two", frames=frames_two, onPage=footer),
        ]
    )
    missing = [k for k, _ in REFS if k not in REF_NUM]
    if missing:
        raise SystemExit(f"references never cited: {missing}")
    doc.build(TITLE_BLOCK + [NextPageTemplate("two")] + STORY)
    print(f"wrote {OUT} ({len(REF_NUM)} references cited)")


if __name__ == "__main__":
    build()
