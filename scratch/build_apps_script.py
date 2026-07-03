import os
import json
import re

papers = [
    { "id": "2305.19951", "title": "Not All Neuro-Symbolic Concepts Are Created Equal: Analysis and Mitigation of Reasoning Shortcuts" },
    { "id": "2005.11401", "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" },
    { "id": "2402.12240", "title": "bears MAKE NEURO-SYMBOLIC MODELS AWARE OF THEIR REASONING SHORTCUTS" },
    { "id": "2401.15884", "title": "Corrective Retrieval Augmented Generation" },
    { "id": "2401.05224", "title": "Do Vision and Language Encoders Represent the World Similarly?" }
]

notes_data = []

def extract_key_sections(text):
    lines = text.split('\n')
    sections = {}
    current_section = None
    current_content = []
    
    for line in lines:
        # Match headings like # Summary or ## Main Contribution
        match = re.match(r'^(#{1,4})\s+(.*)$', line)
        if match:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = match.group(2).strip().lower()
            current_content = [line]  # Keep the heading
        elif current_section:
            current_content.append(line)
            
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
        
    extracted = []
    
    # 1. Summary
    summary_key = next((k for k in sections if 'summary' in k), None)
    if summary_key:
        extracted.append(sections[summary_key])
        
    # 2. Main Contribution
    contrib_key = next((k for k in sections if 'contribution' in k), None)
    if contrib_key:
        extracted.append(sections[contrib_key])
        
    # 3. Key Results
    results_key = next((k for k in sections if 'result' in k), None)
    if results_key:
        extracted.append(sections[results_key])
        
    # 4. Limitations
    limit_key = next((k for k in sections if 'limitation' in k), None)
    if limit_key:
        extracted.append(sections[limit_key])
        
    if not extracted:
        # Fallback to stripped raw text if parsing failed
        yaml_pattern = re.compile(r'^---\s*\n.*?\n---\s*\n', re.DOTALL)
        return yaml_pattern.sub('', text)
        
    return '\n\n'.join(extracted)

notes_dir = 'data/generated_notes'
for p in papers:
    pid = p['id']
    filepath = os.path.join(notes_dir, f"{pid}.md")
    content = "Note not found."
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            raw_text = f.read()
            content = extract_key_sections(raw_text)
    
    notes_data.append({
        "id": pid,
        "title": p['title'],
        "arxiv_url": f"https://arxiv.org/abs/{pid}",
        "pdf_url": f"https://arxiv.org/pdf/{pid}.pdf",
        "note_content": content
    })

# Now generate Code.gs
code_gs = """/**
 * Google Apps Script Backend for RQ4 Evaluation Portal
 */
function doGet() {
  return HtmlService.createTemplateFromFile('Index')
      .evaluate()
      .setTitle('RQ4: Expert Evaluation Portal')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/**
 * Saves Emile's responses to a Google Sheet and sends an email notification
 */
function submitEvaluation(responses) {
  try {
    var ssName = 'RQ4_Evaluation_Responses';
    var files = DriveApp.getFilesByName(ssName);
    var ss;
    if (files.hasNext()) {
      ss = SpreadsheetApp.open(files.next());
    } else {
      ss = SpreadsheetApp.create(ssName);
      var sheet = ss.getSheets()[0];
      sheet.appendRow([
        'Timestamp', 'Paper ID', 'Paper Title', 
        'Q1: Faithfulness', 'Q2: Coverage', 'Q3: Readability', 'Q4: Utility', 
        'Feedback'
      ]);
      // Freeze header row
      sheet.setFrozenRows(1);
    }
    
    var sheet = ss.getSheets()[0];
    var parsed = JSON.parse(responses);
    
    for (var i = 0; i < parsed.length; i++) {
      var r = parsed[i];
      sheet.appendRow([
        new Date(),
        r.id,
        r.title,
        r.q1,
        r.q2,
        r.q3,
        r.q4,
        r.feedback || ''
      ]);
    }
    
    // Send Email Notification to you (the script creator)
    var myEmail = Session.getActiveUser().getEmail();
    MailApp.sendEmail({
      to: myEmail,
      subject: '🚨 RQ4 Evaluation Portal: Emile Submitted Responses!',
      body: `Hello,

Emile van Krieken has successfully submitted his expert ratings for the RQ4 evaluation.

You can view the spreadsheet with the responses here:
\${ss.getUrl()}

Best regards,
Ingestion Pipeline Portal`
    });
    
    return { success: true, sheetUrl: ss.getUrl() };
  } catch (e) {
    return { success: false, error: e.toString() };
  }
}
"""

# Now generate Index.html
index_html = """<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <!-- Import Inter Font -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <!-- Marked.js for Markdown Rendering -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    :root {
      --bg-primary: #0f172a;
      --bg-secondary: #1e293b;
      --bg-tertiary: #334155;
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --accent-light: rgba(59, 130, 246, 0.1);
      --success: #10b981;
      --border: #475569;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Inter', sans-serif;
      background-color: var(--bg-primary);
      color: var(--text-primary);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    header {
      background-color: var(--bg-secondary);
      padding: 1rem 2rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-shrink: 0;
    }

    h1 {
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.025em;
    }

    .subtitle {
      font-size: 0.875rem;
      color: var(--text-secondary);
    }

    .main-container {
      display: flex;
      flex-grow: 1;
      overflow: hidden;
      height: calc(100vh - 65px);
    }

    /* Left Side: Note Preview */
    .left-panel {
      width: 55%;
      height: 100%;
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      background-color: #0b0f19;
    }

    .paper-meta {
      padding: 1.5rem;
      background-color: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
    }

    .paper-title {
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
      color: #fff;
    }

    .paper-links a {
      color: var(--accent);
      text-decoration: none;
      font-size: 0.85rem;
      margin-right: 1rem;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .paper-links a:hover {
      text-decoration: underline;
    }

    .note-content-viewer {
      padding: 2rem;
      overflow-y: auto;
      flex-grow: 1;
      line-height: 1.6;
      font-size: 0.95rem;
      color: #e2e8f0;
    }

    /* Markdown styling inside note content */
    .note-content-viewer h1, .note-content-viewer h2, .note-content-viewer h3 {
      color: #fff;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      font-weight: 600;
    }
    .note-content-viewer h1 { font-size: 1.4rem; border-bottom: 1px solid var(--border); padding-bottom: 0.3rem;}
    .note-content-viewer h2 { font-size: 1.2rem; }
    .note-content-viewer h3 { font-size: 1.05rem; }
    .note-content-viewer p { margin-bottom: 1rem; }
    .note-content-viewer ul, .note-content-viewer ol { margin-bottom: 1rem; padding-left: 1.5rem; }
    .note-content-viewer li { margin-bottom: 0.25rem; }
    .note-content-viewer hr { border: 0; border-top: 1px solid var(--border); margin: 1.5rem 0; }
    .note-content-viewer code { background-color: var(--bg-secondary); padding: 2px 4px; border-radius: 4px; font-family: monospace; font-size: 0.85rem; }
    .note-content-viewer pre { background-color: var(--bg-secondary); padding: 1rem; border-radius: 6px; overflow-x: auto; margin-bottom: 1rem; border: 1px solid var(--border); }
    .note-content-viewer pre code { background: none; padding: 0; }

    /* Right Side: Form Panel */
    .right-panel {
      width: 45%;
      height: 100%;
      display: flex;
      flex-direction: column;
      background-color: var(--bg-primary);
    }

    .tabs-bar {
      display: flex;
      background-color: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
      overflow-x: auto;
      flex-shrink: 0;
    }

    .tab-btn {
      flex: 1;
      padding: 1rem;
      background: none;
      border: none;
      color: var(--text-secondary);
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      white-space: nowrap;
      transition: all 0.2s;
    }

    .tab-btn:hover {
      color: var(--text-primary);
      background-color: rgba(255, 255, 255, 0.02);
    }

    .tab-btn.active {
      color: var(--accent);
      border-bottom-color: var(--accent);
      background-color: rgba(59, 130, 246, 0.05);
    }

    .form-scroll-container {
      padding: 2rem;
      overflow-y: auto;
      flex-grow: 1;
    }

    .intro-card {
      background-color: var(--bg-secondary);
      border: 1px solid var(--border);
      padding: 1.25rem;
      border-radius: 8px;
      margin-bottom: 1.5rem;
      font-size: 0.875rem;
      line-height: 1.5;
    }

    .intro-card h3 {
      margin-bottom: 0.5rem;
      color: #fff;
    }

    .question-group {
      margin-bottom: 2rem;
      background-color: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.5rem;
    }

    .question-title {
      font-size: 0.95rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
      color: #fff;
    }

    .question-help {
      font-size: 0.8rem;
      color: var(--text-secondary);
      margin-bottom: 1rem;
      line-height: 1.4;
    }

    /* 1-5 scale buttons */
    .scale-container {
      display: flex;
      justify-content: space-between;
      gap: 8px;
    }

    .scale-btn {
      flex: 1;
      padding: 0.75rem 0;
      background-color: var(--bg-primary);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--text-secondary);
      font-weight: 600;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
    }

    .scale-btn:hover {
      border-color: var(--accent);
      color: #fff;
    }

    .scale-btn.selected {
      background-color: var(--accent);
      border-color: var(--accent);
      color: #fff;
      box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
    }
    
    .scale-label {
      font-size: 0.65rem;
      font-weight: 400;
      color: inherit;
      opacity: 0.8;
    }

    .comment-area {
      width: 100%;
      background-color: var(--bg-primary);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: #fff;
      padding: 0.75rem;
      font-family: inherit;
      font-size: 0.875rem;
      resize: vertical;
      min-height: 80px;
    }

    .comment-area:focus {
      outline: none;
      border-color: var(--accent);
    }

    /* Actions Bar */
    .actions-bar {
      padding: 1.25rem 2rem;
      background-color: var(--bg-secondary);
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-shrink: 0;
    }

    .btn {
      padding: 0.75rem 1.5rem;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.875rem;
      cursor: pointer;
      transition: all 0.2s;
      border: none;
    }

    .btn-secondary {
      background-color: transparent;
      border: 1px solid var(--border);
      color: var(--text-primary);
    }

    .btn-secondary:hover {
      background-color: rgba(255, 255, 255, 0.05);
    }

    .btn-primary {
      background-color: var(--accent);
      color: #fff;
    }

    .btn-primary:hover {
      background-color: var(--accent-hover);
    }

    .btn-primary:disabled {
      background-color: var(--border);
      cursor: not-allowed;
      opacity: 0.6;
    }

    /* Toast notification */
    #toast {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      padding: 1rem 1.5rem;
      border-radius: 6px;
      background-color: var(--success);
      color: #fff;
      font-weight: 600;
      font-size: 0.875rem;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      display: none;
      z-index: 100;
    }
  </style>
</head>
<body>

  <header>
    <div>
      <h1>RQ4: Expert Evaluation Portal</h1>
      <div class="subtitle">Assessor: Emile van Krieken (Supervisor &amp; Domain Expert)</div>
    </div>
  </header>

  <div class="main-container">
    <!-- Left panel (Note Viewer) -->
    <div class="left-panel">
      <div class="paper-meta">
        <div class="paper-title" id="meta-title">Loading...</div>
        <div class="paper-links">
          <a href="#" id="meta-arxiv" target="_blank">🔗 arXiv Link</a>
          <a href="#" id="meta-pdf" target="_blank">📄 PDF Download</a>
        </div>
      </div>
      <div class="note-content-viewer" id="note-viewer">
        <!-- Rendered markdown goes here -->
      </div>
    </div>

    <!-- Right panel (Questionnaire Form) -->
    <div class="right-panel">
      <div class="tabs-bar" id="tabs-bar">
        <!-- Tab buttons populated by JS -->
      </div>

      <div class="form-scroll-container">
        <!-- Welcome Card -->
        <div class="intro-card">
          <h3>Hello Emile,</h3>
          <p style="margin-bottom: 0.5rem;">Thank you for evaluating the generated summaries. For each of the 5 papers, please review the <strong>generated Obsidian Markdown note</strong> on the left, and fill out the ratings on the right.</p>
          <p>Once you have rated all 5 papers, click the <strong>Submit All Evaluations</strong> button at the bottom. This will automatically record your responses in a Google Sheet.</p>
        </div>

        <div id="questions-container">
          <!-- Active paper's questions -->
          
          <div class="question-group">
            <div class="question-title">Q1. Factual Faithfulness</div>
            <div class="question-help">Does the agent-generated note contain false claims, incorrect attributions, or hallucinations compared to the original paper?</div>
            <div class="scale-container">
              <button class="scale-btn" onclick="setScore('q1', 1)">1 <span class="scale-label">Hallucinated</span></button>
              <button class="scale-btn" onclick="setScore('q1', 2)">2 <span class="scale-label">Poor</span></button>
              <button class="scale-btn" onclick="setScore('q1', 3)">3 <span class="scale-label">Fair</span></button>
              <button class="scale-btn" onclick="setScore('q1', 4)">4 <span class="scale-label">Good</span></button>
              <button class="scale-btn" onclick="setScore('q1', 5)">5 <span class="scale-label">Faithful</span></button>
            </div>
          </div>

          <div class="question-group">
            <div class="question-title">Q2. Core Contribution Coverage</div>
            <div class="question-help">Did the note successfully capture the core research problem, methodology, and primary evaluation results?</div>
            <div class="scale-container">
              <button class="scale-btn" onclick="setScore('q2', 1)">1 <span class="scale-label">Missed All</span></button>
              <button class="scale-btn" onclick="setScore('q2', 2)">2 <span class="scale-label">Poor</span></button>
              <button class="scale-btn" onclick="setScore('q2', 3)">3 <span class="scale-label">Fair</span></button>
              <button class="scale-btn" onclick="setScore('q2', 4)">4 <span class="scale-label">Good</span></button>
              <button class="scale-btn" onclick="setScore('q2', 5)">5 <span class="scale-label">Complete</span></button>
            </div>
          </div>

          <div class="question-group">
            <div class="question-title">Q3. Structure and Readability</div>
            <div class="question-help">Is the generated note well-organized, coherent, and easy for a researcher to read and comprehend quickly?</div>
            <div class="scale-container">
              <button class="scale-btn" onclick="setScore('q3', 1)">1 <span class="scale-label">Unreadable</span></button>
              <button class="scale-btn" onclick="setScore('q3', 2)">2 <span class="scale-label">Poor</span></button>
              <button class="scale-btn" onclick="setScore('q3', 3)">3 <span class="scale-label">Fair</span></button>
              <button class="scale-btn" onclick="setScore('q3', 4)">4 <span class="scale-label">Good</span></button>
              <button class="scale-btn" onclick="setScore('q3', 5)">5 <span class="scale-label">Excellent</span></button>
            </div>
          </div>

          <div class="question-group">
            <div class="question-title">Q4. Utility for Rediscovery</div>
            <div class="question-help">Does this generated note provide significant added utility compared to reading the paper's abstract alone (e.g. as a memory aid)?</div>
            <div class="scale-container">
              <button class="scale-btn" onclick="setScore('q4', 1)">1 <span class="scale-label">No Utility</span></button>
              <button class="scale-btn" onclick="setScore('q4', 2)">2 <span class="scale-label">Low</span></button>
              <button class="scale-btn" onclick="setScore('q4', 3)">3 <span class="scale-label">Fair</span></button>
              <button class="scale-btn" onclick="setScore('q4', 4)">4 <span class="scale-label">Good</span></button>
              <button class="scale-btn" onclick="setScore('q4', 5)">5 <span class="scale-label">High</span></button>
            </div>
          </div>

          <div class="question-group">
            <div class="question-title">Optional Feedback / Comments</div>
            <textarea class="comment-area" id="feedback-field" placeholder="Provide any qualitative comments, discovered errors, or layout notes here..." oninput="updateFeedback()"></textarea>
          </div>
        </div>
      </div>

      <div class="actions-bar">
        <button class="btn btn-secondary" id="prev-btn" onclick="prevTab()">Back</button>
        <div style="font-size: 0.85rem; color: var(--text-secondary);" id="progress-text">Paper 1 of 5</div>
        <button class="btn btn-primary" id="next-btn" onclick="nextTab()">Next Paper</button>
      </div>
    </div>
  </div>

  <div id="toast">Evaluation submitted successfully!</div>

  <script>
    // Embed the notes and metadata
    var papersData = <?!= JSON.stringify(papersData) ?>;
    var activeIndex = 0;

    // Track user inputs
    var scores = papersData.map(function(p) {
      return {
        id: p.id,
        title: p.title,
        q1: null,
        q2: null,
        q3: null,
        q4: null,
        feedback: ""
      };
    });

    // Populate Tab Buttons
    var tabsBar = document.getElementById('tabs-bar');
    papersData.forEach(function(p, index) {
      var btn = document.createElement('button');
      btn.className = 'tab-btn' + (index === 0 ? ' active' : '');
      btn.innerText = 'Paper ' + (index + 1);
      btn.id = 'tab-' + index;
      btn.onclick = function() { selectTab(index); };
      tabsBar.appendChild(btn);
    });

    // Initialize display
    selectTab(0);

    // Render markdown and update view
    function selectTab(index) {
      document.getElementById('tab-' + activeIndex).classList.remove('active');
      activeIndex = index;
      document.getElementById('tab-' + activeIndex).classList.add('active');

      // Update metadata & notes view
      var paper = papersData[activeIndex];
      document.getElementById('meta-title').innerText = paper.title;
      document.getElementById('meta-arxiv').href = paper.arxiv_url;
      document.getElementById('meta-pdf').href = paper.pdf_url;
      
      // Render markdown using Marked.js
      document.getElementById('note-viewer').innerHTML = marked.parse(paper.note_content);

      // Restore scores for the form buttons
      restoreButtons();

      // Restore comment text
      document.getElementById('feedback-field').value = scores[activeIndex].feedback;

      // Update progress text
      document.getElementById('progress-text').innerText = 'Paper ' + (activeIndex + 1) + ' of ' + papersData.length;

      // Update Navigation Buttons
      var prevBtn = document.getElementById('prev-btn');
      var nextBtn = document.getElementById('next-btn');

      if (activeIndex === 0) {
        prevBtn.style.visibility = 'hidden';
      } else {
        prevBtn.style.visibility = 'visible';
      }

      if (activeIndex === papersData.length - 1) {
        nextBtn.innerText = 'Submit Evaluations';
        nextBtn.classList.add('btn-success');
      } else {
        nextBtn.innerText = 'Next Paper';
        nextBtn.classList.remove('btn-success');
      }
    }

    function setScore(q, val) {
      scores[activeIndex][q] = val;
      
      // Visual feedback: select correct button
      var btnGroupIndex = {'q1': 0, 'q2': 1, 'q3': 2, 'q4': 3}[q];
      var containers = document.querySelectorAll('.question-group')[btnGroupIndex].querySelectorAll('.scale-btn');
      containers.forEach(function(btn, i) {
        if (i + 1 === val) {
          btn.classList.add('selected');
        } else {
          btn.classList.remove('selected');
        }
      });
    }

    function restoreButtons() {
      var current = scores[activeIndex];
      var qFields = ['q1', 'q2', 'q3', 'q4'];
      
      qFields.forEach(function(q, qIdx) {
        var val = current[q];
        var containers = document.querySelectorAll('.question-group')[qIdx].querySelectorAll('.scale-btn');
        containers.forEach(function(btn, btnIdx) {
          if (val && btnIdx + 1 === val) {
            btn.classList.add('selected');
          } else {
            btn.classList.remove('selected');
          }
        });
      });
    }

    function updateFeedback() {
      scores[activeIndex].feedback = document.getElementById('feedback-field').value;
    }

    function prevTab() {
      if (activeIndex > 0) {
        selectTab(activeIndex - 1);
      }
    }

    function nextTab() {
      if (activeIndex < papersData.length - 1) {
        selectTab(activeIndex + 1);
      } else {
        submitAll();
      }
    }

    function submitAll() {
      // Validate all scores are filled
      for (var i = 0; i < scores.length; i++) {
        var s = scores[i];
        if (s.q1 === null || s.q2 === null || s.q3 === null || s.q4 === null) {
          alert('Please answer all 4 Likert scale questions for Paper ' + (i + 1) + ' before submitting.');
          selectTab(i);
          return;
        }
      }

      var submitBtn = document.getElementById('next-btn');
      submitBtn.disabled = true;
      submitBtn.innerText = 'Submitting...';

      // Call Google Apps Script backend
      google.script.run
        .withSuccessHandler(function(result) {
          if (result.success) {
            var toast = document.getElementById('toast');
            toast.innerText = 'Submitted successfully! Google Sheet generated in your Drive.';
            toast.style.display = 'block';
            setTimeout(function() { toast.style.display = 'none'; }, 6000);
            
            submitBtn.innerText = 'Submitted ✅';
            alert('Thank you Emile! Your evaluation has been saved. You can close this tab now.');
          } else {
            alert('Submission failed: ' + result.error);
            submitBtn.disabled = false;
            submitBtn.innerText = 'Submit Evaluations';
          }
        })
        .withFailureHandler(function(err) {
          alert('Submission failed with server error: ' + err.toString());
          submitBtn.disabled = false;
          submitBtn.innerText = 'Submit Evaluations';
        })
        .submitEvaluation(JSON.stringify(scores));
    }
  </script>
</body>
</html>
"""

# Let's save these to Code.gs and Index.html in scratch directory
with open('scratch/appscript_code.gs', 'w', encoding='utf-8') as f:
    f.write(code_gs)

# Insert the JSON object for papersData into index_html
index_html_final = index_html.replace("<?!= JSON.stringify(papersData) ?>", json.dumps(notes_data, indent=2))

with open('scratch/appscript_index.html', 'w', encoding='utf-8') as f:
    f.write(index_html_final)

print("Google Apps Script code successfully generated!")
print("Location 1: scratch/appscript_code.gs")
print("Location 2: scratch/appscript_index.html")
