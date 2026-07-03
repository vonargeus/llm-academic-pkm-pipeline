/**
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
