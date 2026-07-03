import matplotlib.pyplot as plt
import numpy as np
import os

# Set style for academic publication
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.linewidth'] = 1.0

# Data
categories = ['Recall@5', 'Precision@5', 'MRR@5']
flat_rag = [0.6958, 0.2350, 0.7292]
structured_rag = [0.6958, 0.2250, 0.7438]
link_expanded = [0.7188, 0.2300, 0.7425]

x = np.arange(len(categories))
width = 0.25

fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=300)

# Colors matching professional academic style
color_flat = '#555555'       # Dark grey
color_struct = '#2b5c8f'     # Slate blue
color_link = '#c44e52'       # Soft red/burgundy

rects1 = ax.bar(x - width, flat_rag, width, label='Flat RAG (Baseline)', color=color_flat, edgecolor='black', linewidth=0.7)
rects2 = ax.bar(x, structured_rag, width, label='Structured RAG (Notes)', color=color_struct, edgecolor='black', linewidth=0.7)
rects3 = ax.bar(x + width, link_expanded, width, label='Link-Expanded RAG', color=color_link, edgecolor='black', linewidth=0.7)

# Title and labels
ax.set_ylabel('Score / Value', fontweight='bold', labelpad=8)
ax.set_title('RQ1: Retrieval Performance Comparison Across Configurations', pad=15, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(categories, fontweight='bold')
ax.set_ylim(0.0, 0.85)

# Grid lines
ax.set_axisbelow(True)
ax.yaxis.grid(True, color='#dddddd', linestyle='--', linewidth=0.5)
ax.xaxis.grid(False)

# Legend
ax.legend(loc='upper right', frameon=True, edgecolor='#cccccc', framealpha=0.9)

# Value labels on top of the bars
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.4f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

autolabel(rects1)
autolabel(rects2)
autolabel(rects3)

plt.tight_layout()

# Save both PNG and PDF for LaTeX inclusion
output_png = 'Thesis_Draft/retrieval_metrics.png'
output_pdf = 'Thesis_Draft/retrieval_metrics.pdf'

plt.savefig(output_png, bbox_inches='tight')
plt.savefig(output_pdf, bbox_inches='tight')
print(f"Generated and saved: {output_png} and {output_pdf}")
