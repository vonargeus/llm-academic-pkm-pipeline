import os
import random
import re

dirs_to_check = [
    'data/raw_pdfs',
    'data/extracted_text',
    'data/generated_notes'
]

papers = set()
titles = {}

# Simple regex to match arXiv style: e.g. 2305.19951 or 1711.11157 or similar
arxiv_pattern = re.compile(r'^\d{4}\.\d{4,5}$')

for d in dirs_to_check:
    if os.path.exists(d):
        files = os.listdir(d)
        for f in files:
            name, ext = os.path.splitext(f)
            if arxiv_pattern.match(name):
                papers.add(name)

papers_list = sorted(list(papers))
print(f"Total arXiv papers found: {len(papers_list)}")
print("First 10 papers:", papers_list[:10])

# Load titles from generated_notes
notes_dir = 'data/generated_notes'
if os.path.exists(notes_dir):
    for f in os.listdir(notes_dir):
        name, ext = os.path.splitext(f)
        if arxiv_pattern.match(name) and ext == '.md':
            filepath = os.path.join(notes_dir, f)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    if line.startswith('title:'):
                        t = line.replace('title:', '').strip().strip('"').strip("'")
                        titles[name] = t
                        break
                    elif line.startswith('# '):
                        t = line.replace('# ', '').strip()
                        titles[name] = t
                        break

# Select 5 papers randomly using seed 42
random.seed(42)
if len(papers_list) >= 5:
    sampled = random.sample(papers_list, 5)
    print("\nSampled Papers:")
    for i, pid in enumerate(sampled, 1):
        t = titles.get(pid, pid)
        print(f"{i}. ID: {pid} -> Title: {t}")
else:
    print(f"Warning: Only {len(papers_list)} papers found.")
