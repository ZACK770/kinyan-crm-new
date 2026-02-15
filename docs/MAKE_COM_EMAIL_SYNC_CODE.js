/**
 * Make.com Code Module - Email Sync to Kinyan CRM
 * 
 * הוראות שימוש:
 * 1. צור מודול "Code" ב-Make.com
 * 2. העתק את הקוד הזה לתוך המודול
 * 3. הגדר את API_KEY (ערך WEBHOOK_API_KEY מה-.env שלך)
 * 4. חבר את המודול למקור המיילים שלך
 */

// ═══════════════════════════════════════════════════════════════
// הגדרות - ערוך רק את API_KEY
// ═══════════════════════════════════════════════════════════════

const API_KEY = 'YOUR_WEBHOOK_API_KEY_HERE';  // ערך WEBHOOK_API_KEY מה-.env
const WEBHOOK_URL = 'https://kinyan-crm-new-1.onrender.com/webhooks/inbound-email';
const BATCH_SIZE = 100;  // כמה מיילים לשלוח בכל פעם
const MAX_RETRIES = 3;   // כמה ניסיונות חוזרים במקרה של שגיאה

// ═══════════════════════════════════════════════════════════════
// פונקציות עזר
// ═══════════════════════════════════════════════════════════════

/**
 * שולח חבילת מיילים ל-webhook
 */
async function sendEmailBatch(emails, retryCount = 0) {
    try {
        // Make sure emails is an array of objects, not strings
        const emailsArray = Array.isArray(emails) ? emails : [emails];
        
        const response = await fetch(WEBHOOK_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify(emailsArray)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const result = await response.json();
        console.log(`✅ נשלחו ${emails.length} מיילים בהצלחה`);
        console.log(`   - נוצרו: ${result.created}`);
        console.log(`   - דולגו (קיימים): ${result.skipped}`);
        console.log(`   - שגיאות: ${result.errors}`);
        
        return result;
        
    } catch (error) {
        console.error(`❌ שגיאה בשליחת מיילים (ניסיון ${retryCount + 1}/${MAX_RETRIES}):`, error.message);
        
        // retry logic
        if (retryCount < MAX_RETRIES) {
            const waitTime = Math.pow(2, retryCount) * 1000; // exponential backoff
            console.log(`⏳ ממתין ${waitTime}ms לפני ניסיון חוזר...`);
            await new Promise(resolve => setTimeout(resolve, waitTime));
            return sendEmailBatch(emails, retryCount + 1);
        }
        
        throw error;
    }
}

/**
 * ממיר מייל בודד לפורמט הנדרש
 */
function formatEmail(emailData) {
    return {
        id: emailData.id,
        threadId: emailData.threadId,
        direction: emailData.labelIds?.includes('SENT') ? 'outbound' : 'inbound',
        fromEmail: emailData.fromEmail,
        fromName: emailData.fromName,
        to: emailData.to || [],
        bcc: emailData.bcc || [],
        subject: emailData.subject || null,
        snippet: emailData.snippet,
        fullTextBody: emailData.fullTextBody,
        htmlBody: emailData.htmlBody,
        hasAttachment: emailData.hasAttachment,
        attachmentsCount: emailData.hasAttachment ? (emailData.attachments?.length || 1) : 0,
        labelIds: emailData.labelIds,
        sysFolders: emailData.sysFolders || [],
        headers: emailData.headers,
        internalDate: emailData.internalDate,
        sizeEstimate: emailData.sizeEstimate,
        historyId: emailData.historyId
    };
}

/**
 * מחלק מערך למקטעים
 */
function chunkArray(array, size) {
    const chunks = [];
    for (let i = 0; i < array.length; i += size) {
        chunks.push(array.slice(i, i + size));
    }
    return chunks;
}

// ═══════════════════════════════════════════════════════════════
// קוד ראשי - זה מה שרץ ב-Make.com
// ═══════════════════════════════════════════════════════════════

// קבל את המיילים מהמודול הקודם
// במודול Code ב-Make.com, הגדר משתנה input בשם "emails" 
// ומפה אותו למערך המיילים מהמודול הקודם
let allEmails = input.emails || [];

// Debug: בדוק אם המיילים הם strings או objects
console.log(`📧 מעבד ${allEmails.length} מיילים...`);
console.log(`🔍 סוג הנתונים: ${typeof allEmails[0]}`);

// אם המיילים הם strings (JSON), המר אותם לאובייקטים
if (allEmails.length > 0 && typeof allEmails[0] === 'string') {
    console.log('⚠️  המיילים הם strings - ממיר ל-JSON...');
    allEmails = allEmails.map(email => {
        try {
            return JSON.parse(email);
        } catch (e) {
            console.error(`❌ שגיאה בהמרת מייל: ${e.message}`);
            return null;
        }
    }).filter(email => email !== null);
}

// שלח את המיילים כמו שהם (הקוד בצד השרת מצפה לפורמט Gmail)
const batches = chunkArray(allEmails, BATCH_SIZE);
console.log(`📦 מחולק ל-${batches.length} חבילות של עד ${BATCH_SIZE} מיילים`);

const results = {
    totalEmails: allEmails.length,
    totalBatches: batches.length,
    successfulBatches: 0,
    failedBatches: 0,
    created: 0,
    skipped: 0,
    errors: 0,
    details: []
};

// שלח כל חבילה
for (let i = 0; i < batches.length; i++) {
    const batch = batches[i];
    console.log(`\n📤 שולח חבילה ${i + 1}/${batches.length} (${batch.length} מיילים)...`);
    
    try {
        const result = await sendEmailBatch(batch);
        results.successfulBatches++;
        results.created += result.created || 0;
        results.skipped += result.skipped || 0;
        results.errors += result.errors || 0;
        results.details.push({
            batchNumber: i + 1,
            success: true,
            result
        });
        
        // המתנה קצרה בין חבילות כדי לא להעמיס על השרת
        if (i < batches.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
    } catch (error) {
        console.error(`❌ חבילה ${i + 1} נכשלה:`, error.message);
        results.failedBatches++;
        results.details.push({
            batchNumber: i + 1,
            success: false,
            error: error.message
        });
    }
}

// סיכום
console.log('\n' + '═'.repeat(60));
console.log('📊 סיכום סנכרון מיילים:');
console.log('═'.repeat(60));
console.log(`סה"כ מיילים: ${results.totalEmails}`);
console.log(`חבילות שנשלחו: ${results.successfulBatches}/${results.totalBatches}`);
console.log(`✅ נוצרו: ${results.created}`);
console.log(`⏭️  דולגו (קיימים): ${results.skipped}`);
console.log(`❌ שגיאות: ${results.errors}`);
console.log('═'.repeat(60));

// החזר את התוצאות למודול הבא ב-Make.com
return results;
