import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import textwrap

def draw_card(ax, title, bullet_points, x, y, w, h, bg_color='#ffffff', border_color='#e2e8f0', title_color='#1e3a8a', text_color='#334155'):
    # Draw rounded card container
    bbox = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.008",
        facecolor=bg_color,
        edgecolor=border_color,
        linewidth=1.2,
        mutation_scale=0.3,
        zorder=1
    )
    ax.add_patch(bbox)
    
    # Write Title
    if title:
        ax.text(
            x + 0.015, y + h - 0.03, title,
            fontsize=10.5, fontweight='bold', color=title_color,
            va='top', ha='left', zorder=2
        )
    
    # Write bullet points with wrapping
    current_y = y + h - 0.055
    line_height = 0.017
    
    for bp in bullet_points:
        if bp.startswith('HEADER:'):
            # Section header inside card
            header_text = bp.replace('HEADER:', '').strip()
            ax.text(
                x + 0.015, current_y, header_text,
                fontsize=9, fontweight='bold', color='#0f172a',
                va='top', ha='left', zorder=2
            )
            current_y -= line_height * 1.1
            continue
            
        # Wrap long bullet points (narrow width to fit card)
        wrapped_lines = textwrap.wrap(bp, width=38)
        for idx, line in enumerate(wrapped_lines):
            prefix = "• " if (idx == 0 and not bp.startswith("  ")) else "  "
            ax.text(
                x + 0.015, current_y, prefix + line,
                fontsize=8, color=text_color,
                va='top', ha='left', zorder=2
            )
            current_y -= line_height
        current_y -= line_height * 0.35  # spacing between bullets

def draw_flowchart(ax, x, y, w, h):
    # Center the flowchart in the pipeline card
    # Card coordinate: x=0.03, y=0.32, w=0.29, h=0.245
    flow_y = y + 0.035
    box_w = 0.05
    box_h = 0.03
    spacing = 0.068
    
    stages = ["PDFs", "Text", "Agents", "Notes"]
    for idx, stage in enumerate(stages):
        bx = x + 0.014 + idx * spacing
        # Draw a small rounded stage box
        b_patch = patches.FancyBboxPatch(
            (bx, flow_y), box_w, box_h,
            boxstyle="round,pad=0.003",
            facecolor='#1e3a8a',  # Dark Navy box
            edgecolor='#0284c7',  # Sky Blue border
            linewidth=1,
            zorder=3
        )
        ax.add_patch(b_patch)
        
        # Add label
        ax.text(
            bx + box_w/2, flow_y + box_h/2, stage,
            fontsize=7.5, fontweight='bold', color='#ffffff',
            va='center', ha='center', zorder=4
        )
        
        # Add arrow if not the last block
        if idx < 3:
            arrow_x = bx + box_w + 0.002
            ax.annotate(
                "",
                xy=(arrow_x + 0.012, flow_y + box_h/2),
                xytext=(arrow_x, flow_y + box_h/2),
                arrowprops=dict(arrowstyle="->", color='#0f766e', lw=1.2, shrinkA=0, shrinkB=0),
                zorder=3
            )

def main():
    # Setup canvas (12" x 17" for portrait A2 aspect ratio)
    fig, ax = plt.subplots(figsize=(12, 17), dpi=300)
    ax.set_facecolor('#f8fafc')  # slate-50 light background
    fig.patch.set_facecolor('#f8fafc')
    
    # Hide axes
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    # -------------------------------------------------------------
    # 1. HEADER SECTION (Across the top)
    # -------------------------------------------------------------
    # Title Card
    draw_card(
        ax, "", [],
        0.03, 0.885, 0.94, 0.09,
        bg_color='#ffffff', border_color='#cbd5e1', text_color='#0f172a'
    )
    # Title & Metadata
    ax.text(
        0.5, 0.952, "LLM Agents for Interlinked and Personalised Knowledge Bases",
        fontsize=16, fontweight='bold', color='#1e3a8a',
        va='top', ha='center', zorder=2
    )
    ax.text(
        0.5, 0.923, "Author: Muhammed Furkan Kaya   |   Supervisor: Dr. Emile van Krieken   |   VU Amsterdam",
        fontsize=9.5, fontweight='semibold', color='#0f766e',
        va='top', ha='center', zorder=2
    )
    ax.text(
        0.5, 0.902, "Objective: Evaluates whether LLM-generated structured notes and semantic links improve academic retrieval.",
        fontsize=8.5, color='#475569', fontstyle='italic',
        va='top', ha='center', zorder=2
    )
    
    # -------------------------------------------------------------
    # 2. LEFT COLUMN (Motivation & Pipeline)
    # -------------------------------------------------------------
    motivation_text = [
        "Academic literature is vast, making it hard to connect related research.",
        "Obsidian knowledge bases allow interlinked Markdown notes but require high manual effort to create.",
        "We build and evaluate an automated ingestion pipeline using LLM agents."
    ]
    draw_card(ax, "1. Motivation", motivation_text, 0.03, 0.58, 0.29, 0.285)
    
    pipeline_text = [
        "1. Ingestion: Text is extracted from PDFs.",
        "2. Note Generation: LLM agent extracts metadata and generates structured paper summaries.",
        "3. Linking: The pipeline proposes directional wiki-links to other notes in the local vault.",
        "HEADER:Modular LLM Ingestion Pipeline"
    ]
    # Draw card first, then overlay flowchart shapes
    draw_card(ax, "2. Pipeline Flow", pipeline_text, 0.03, 0.32, 0.29, 0.245)
    draw_flowchart(ax, 0.03, 0.32, 0.29, 0.245)
    
    rq_text = [
        "RQ1: Downstream retrieval performance.",
        "RQ2: Bibliographic and topic extraction accuracy.",
        "RQ4: Expert quality assessment of notes."
    ]
    draw_card(ax, "3. Research Questions", rq_text, 0.03, 0.165, 0.29, 0.14)
    
    # -------------------------------------------------------------
    # 3. CENTER COLUMN (RQ1 Retrieval - MAIN FOCUS)
    # -------------------------------------------------------------
    rq1_text = [
        "HEADER:RAG Configurations Compared",
        "Flat RAG: Raw PDF text chunks (512 tokens) with MaxP aggregation.",
        "Structured RAG: Retrieval over full agent-generated notes.",
        "Link-Expanded RAG: Structured seeds + one-hop wiki-link score boosts (alpha-coefficient cross-validated).",
        "HEADER:Key Retrieval Metrics",
        "Best Recall@5 (Link-Expanded): 0.7188",
        "  (Flat RAG: 0.6958 | Structured RAG: 0.6958)",
        "Best Precision@5 (Flat RAG): 0.2350",
        "  (Structured: 0.2250 | Link-Expanded: 0.2300)",
        "Best MRR@5 (Structured RAG): 0.7438",
        "  (Flat RAG: 0.7292 | Link-Expanded: 0.7425)",
        "HEADER:Main Takeaway",
        "Link expansion achieved the highest observed recall (0.7188), suggesting a modest benefit for coverage.",
        "Structured notes slightly improved the rank of the first relevant result (MRR)."
    ]
    draw_card(ax, "4. RQ1: Retrieval Performance", rq1_text, 0.355, 0.165, 0.29, 0.70, border_color='#0f766e', title_color='#0f766e')
    
    # Draw simple background panels for metrics in center column
    # Metric Recall Highlight
    ax.add_patch(patches.FancyBboxPatch(
        (0.365, 0.355), 0.27, 0.05,
        boxstyle="round,pad=0.003",
        facecolor='#f1f5f9', edgecolor='none', zorder=2
    ))
    # Metric Precision Highlight
    ax.add_patch(patches.FancyBboxPatch(
        (0.365, 0.285), 0.27, 0.05,
        boxstyle="round,pad=0.003",
        facecolor='#f1f5f9', edgecolor='none', zorder=2
    ))
    # Metric MRR Highlight
    ax.add_patch(patches.FancyBboxPatch(
        (0.365, 0.215), 0.27, 0.05,
        boxstyle="round,pad=0.003",
        facecolor='#f1f5f9', edgecolor='none', zorder=2
    ))
    
    # -------------------------------------------------------------
    # 4. RIGHT COLUMN (Extraction Accuracy)
    # -------------------------------------------------------------
    metadata_text = [
        "Title exact match rate: 0.9750",
        "Author-set F1-score: 0.8250",
        "Year exact match rate: 0.7750",
        "Venue fuzzy match rate: 0.5000",
        "HEADER:Analysis",
        "The agent reliably extracts paper titles and authors. Years and venues are more variable due to preprint database differences."
    ]
    draw_card(ax, "5. Bibliographic Metadata", metadata_text, 0.68, 0.51, 0.29, 0.355)
    
    topic_text = [
        "Strict Lexical F1-score: 0.0957",
        "  (Exact overlap comparison on 22 papers)",
        "Canonicalised F1-score (B1c): 0.3831",
        "  (Mapped test set on 15 papers)",
        "HEADER:Vocabulary Variance",
        "Topic alignment is highly sensitive to vocabulary choices rather than extraction failures. Canonicalising tags to a fixed taxonomy improves F1 to 0.3831.",
        "Strict and B1c scores are separate protocols and not directly comparable."
    ]
    draw_card(ax, "6. Topic Alignment Accuracy", topic_text, 0.68, 0.165, 0.29, 0.33)
    
    # Highlight Canonicalised F1
    ax.add_patch(patches.FancyBboxPatch(
        (0.69, 0.315), 0.27, 0.038,
        boxstyle="round,pad=0.003",
        facecolor='#f0fdf4', edgecolor='#bbf7d0', linewidth=0.5, zorder=2
    ))
    
    # -------------------------------------------------------------
    # 5. BOTTOM SECTION (Conclusions & Limitations)
    # -------------------------------------------------------------
    conclusions_text = [
        "Structured summaries do not automatically outperform raw chunks, but link-expansion boosts recall.",
        "Strict lexical evaluations hide true semantic alignment; B1c is required to measure actual topic mapping."
    ]
    draw_card(ax, "7. Conclusions", conclusions_text, 0.03, 0.02, 0.45, 0.125, border_color='#059669', title_color='#059669')
    
    limitations_text = [
        "Evaluation is bounded by a 40-paper corpus and 40 queries.",
        "Topic validation uses one personalized expert vocabulary.",
        "No confidence intervals or significance tests were conducted."
    ]
    draw_card(ax, "8. Limitations & RQ4", limitations_text, 0.52, 0.02, 0.45, 0.125)
    
    # Save the output image
    output_dir = 'Thesis_Draft'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'thesis_poster.png')
    
    plt.tight_layout()
    plt.savefig(output_path, facecolor='#f8fafc', edgecolor='none', bbox_inches='tight', pad_inches=0.1)
    print(f"Poster successfully generated and saved to: {output_path}")

if __name__ == '__main__':
    main()
