# RupeeBoss CRM - User Manual
## Complete Guide for Sales Teams

**Version:** 2.0 (Updated May 11, 2026)  
**URL:** https://rupeeboss-crm.pages.dev  
**For:** Sales Representatives & Admin Users

---

## 📑 Table of Contents

1. [Getting Started](#1-getting-started)
2. [Dashboard Overview](#2-dashboard-overview)
3. [Lead Management](#3-lead-management)
4. [Lead Categories](#4-lead-categories)
5. [Viewing Lead Details](#5-viewing-lead-details)
6. [Sentiment Analysis](#6-sentiment-analysis)
7. [Follow-ups System](#7-follow-ups-system)
8. [Document Management](#8-document-management)
9. [Email Generator](#9-email-generator)
10. [Admin Features](#10-admin-features)
11. [Filters & Search](#11-filters--search)
12. [Tips for Sales Success](#12-tips-for-sales-success)

---

## 1. Getting Started

### Login Credentials

**Admin Access:**
- Username: `admin`
- Password: `admin123`
- Full access to all features including delete

**User/Sales Rep Access:**
- Username: `user`
- Password: `user123`
- Can view leads, add follow-ups, upload documents, generate emails

### First Login
1. Visit https://rupeeboss-crm.pages.dev
2. Enter your username and password
3. Click **"Login"**
4. You'll see the leads dashboard immediately

### Change Password
1. Click **"🔑 Change Password"** button (top right)
2. Enter current password
3. Enter new password (minimum 4 characters)
4. Confirm new password
5. Click **"Update Password"**

---

## 2. Dashboard Overview

### Header Section
```
[RupeeBoss Logo]  LEADS CRM
```
- Professional branding with company logo
- Clean, modern interface

### User Info Bar
- Shows your role (Admin or User)
- **"Logout"** button
- **"🔑 Change Password"** button

### Statistics Cards
```
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│   179   │ │    63   │ │   111   │ │    0    │ │    85   │ │    15   │
│  Total  │ │   HOT   │ │  COLD   │ │  EMAIL  │ │ POSITIVE│ │ NEGATIVE│
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

| Stat | Description |
|------|-------------|
| **Total** | Total number of leads in system |
| **🔥 HOT** | High-quality leads (have name + phone) |
| **❄️ COLD** | Basic leads (phone only, no name) |
| **📧 EMAIL** | Email-only leads |
| **😊 POSITIVE** | Leads with positive sentiment |
| **😠 NEGATIVE** | Leads with negative sentiment |

### Filter Buttons
- **All** - Show all leads
- **🔥 HOT** - Show only HOT leads
- **❄️ COLD** - Show only COLD leads
- **📧 EMAIL** - Show email leads
- **📅 DUE** - Show leads with overdue follow-ups
- **😊 POSITIVE** - Show leads with positive sentiment
- **😠 NEGATIVE** - Show leads with negative sentiment

### Search Box
- Type name, email, phone, or topic
- Real-time filtering as you type
- Example: "Krishna" or "8879508890"

---

## 3. Lead Management

### Understanding Lead Cards

Each lead appears as a card:

```
┌──────────────────────────────────────────┐
│  Customer Name                    🔥 HOT   │
│  📱 9876543210 | 📅 2026-05-09 😊 Positive│
│  📞 Personal Loan Inquiry                   │
│                                           │
│  [📋 View Summary] [📖 View Transcript]    │
│  [📅 Follow-Ups] [📄 Docs] [🗑️ Delete]    │
└──────────────────────────────────────────┘
```

### Lead Information Displayed
- **Name** - Customer name (or "Unknown" if not provided)
- **Phone** - Click to call directly
- **Date** - Date of conversation
- **Title** - Brief description of inquiry
- **Category Badge** - HOT/COLD/EMAIL
- **Sentiment Badge** - Positive/Neutral/Negative with interest level

---

## 4. Lead Categories

### 🔥 HOT Leads (63 leads)
**Definition:** Leads with both name AND phone number
- **Priority:** HIGH - Call these first!
- **Characteristics:**
  - Customer provided full name
  - Has valid phone number
  - Higher conversion probability
- **Action:** Contact within 24 hours

### ❄️ COLD Leads (111 leads)
**Definition:** Leads with phone only (no name)
- **Priority:** MEDIUM - Nurture these
- **Characteristics:**
  - Only phone number available
  - No name provided
  - May need more information gathering
- **Action:** Call and collect more details

### 📧 EMAIL Leads (0 leads)
**Definition:** Leads with email only
- **Priority:** LOW - Add to email campaigns
- **Action:** Send email follow-ups

---

## 5. Viewing Lead Details

### View Summary
Click **"📋 View Summary"** to see:
- Condensed version of the conversation
- Key points discussed
- Customer requirements
- Quick overview without reading full transcript

**Example Summary:**
```
Krishna contacted RupeeBoss for a personal loan. 
Riya collected his details: income (₹1 lakh), 
no EMIs, 12 years of experience, and a credit 
score of 850. He is eligible for a loan.
```

### View Transcript
Click **"📖 View Transcript"** to see:
- Complete conversation between AI agent and customer
- Formatted with timestamps
- Shows full dialogue
- Includes sentiment analysis section

**Transcript Format:**
```
[AGENT] Hi, I'm Riya from RupeeBoss Support...
[USER] Yes, I was looking for a personal loan...
[AGENT] Great! I can help you with that...
```

---

## 6. Sentiment Analysis

### Understanding Sentiment

Each lead has AI-analyzed sentiment based on conversation tone:

### Sentiment Badges in Lead List
- **😊 Positive** - Customer showed interest, said yes, ready to proceed
- **😐 Neutral** - Customer gathering information, undecided
- **😠 Negative** - Customer hesitant, said no, concerned about terms

### Detailed Sentiment View (in Transcript)
When you open a transcript, you'll see:

```
💭 Sentiment: 😊 POSITIVE (0.80)
━━━━━━━━━━━━━━━━━━━━ (80%)
Interest: High 🔥
✅ Positive: 9 | ❌ Negative: 1
```

### Sentiment Components
| Element | Description |
|---------|-------------|
| **Score** | -1.0 (negative) to +1.0 (positive) |
| **Bar** | Visual representation of score |
| **Interest** | High 🔥 / Medium / Low ❄️ |
| **Keywords** | Count of positive vs negative words |

### How to Use Sentiment
1. **Call Positive leads first** - They're ready to convert
2. **Handle Negative leads carefully** - Address their concerns
3. **Nurture Neutral leads** - Provide more information

---

## 7. Follow-ups System

### Viewing Follow-ups
Click **"📅 Follow-Ups"** on any lead to see:
- Timeline of all past follow-ups
- Next scheduled follow-up date
- Status (pending/completed)

### Adding a Follow-up
1. Open follow-ups section for a lead
2. Select **Type**:
   - 📝 **Note** - General note or observation
   - 📧 **Email** - Email sent to customer
   - 📞 **Call** - Phone call made
3. Enter **Content** - Details of the interaction
4. Select **Next Follow-up Date** (optional)
5. Click **"Log Follow-Up"**

### Example Follow-up
```
Type: 📞 Call
Content: Called Krishna, he is ready to proceed with 
document submission. Scheduled meeting for tomorrow.
Next Follow-up: 2026-05-12
Status: pending
```

### Due Follow-ups Filter
Click **"📅 DUE"** filter to see:
- Leads with overdue follow-ups
- Leads needing attention today

---

## 8. Document Management

### Uploading Documents
1. Click **"📄 Docs"** on any lead
2. Click **"📤 Upload Document"**
3. Select file(s) from your computer
4. Supported formats: PDF, Images (JPG/PNG), Word documents
5. Maximum file size: 2MB per file

### Supported Documents
- PAN Card
- Aadhaar Card
- Photo
- Company ID
- Residence Proof
- Rent Agreement
- Salary Slips (3 months)
- Form 16
- Appointment Letter
- Bank Statements (6 months)
- Loan Sanction Letters

### Downloading Documents
- Click **"📥 Download"** next to any uploaded document
- Files open in new tab for viewing

### Deleting Documents (Admin only)
1. Open document manager for the lead
2. Click **"🗑️ Delete"** next to the document
3. Confirm deletion

---

## 9. Email Generator

### Generating Email from Transcript
1. Open **transcript view** for any lead
2. Click **"📧 Generate Email Reply"**
3. System automatically creates personalized email based on:
   - Customer name
   - Loan type discussed
   - Amount mentioned
   - Income details
   - Employment type
   - Credit score

### Email Content Includes
- Personalized greeting
- Reference to their specific inquiry
- Eligibility summary
- Next steps
- Required documents list
- Contact information

### Sending Options
1. **📋 Copy to Clipboard** - Copy and paste anywhere
2. **📧 Send via Email Client** - Opens default email app

### Example Generated Email
```
Dear Krishna,

Thank you for contacting RupeeBoss Financial Services 
regarding your Personal Loan inquiry.

We have reviewed your conversation with our AI assistant...

- Loan Amount Required: ₹15 lakhs
- Your Income: ₹1,00,000
- Employment Type: Salaried
- Work Experience: 12 years
- Credit Score: 850

Next Steps:
- Our relationship manager will contact you within 24 hours
- We will schedule a convenient time to discuss your requirements
- You can also reach us directly at 1800267 629 6

Documents Required:
✓ KYC Documents (Aadhaar, PAN)
✓ Income Proof (Salary slips / ITR)
✓ Business Proof (if applicable)
✓ Address Proof

Best regards,
Team RupeeBoss
📞 1800267 629 6 (Toll-Free) | +91 83568 44010
```

---

## 10. Admin Features

### Delete Lead (Admin only)
1. Click **"🗑️ Delete"** on any lead card
2. Confirm deletion
3. Lead is hidden from view
4. Stored in deleted leads log

**Note:** Deleted leads are stored in browser localStorage and can be restored if needed.

### Document Deletion (Admin only)
1. Open document manager
2. Click **"🗑️ Delete"** next to document
3. Confirm deletion

---

## 11. Filters & Search

### Using Filters

| Filter | Shows | When to Use |
|--------|-------|-------------|
| **All** | Every lead | General overview |
| **🔥 HOT** | Named leads | High priority calling |
| **❄️ COLD** | Phone-only leads | Information gathering |
| **📧 EMAIL** | Email leads | Email campaigns |
| **📅 DUE** | Overdue follow-ups | Daily action items |
| **😊 POSITIVE** | Positive sentiment | Quick conversion |
| **😠 NEGATIVE** | Negative sentiment | Needs attention |

### Search Tips
- **By Name:** "Krishna" or "Raj"
- **By Phone:** "8879508890"
- **By Topic:** "personal loan" or "business"
- Partial matches work: "Kris" finds "Krishna"

### Combined Filtering
1. Select category (e.g., 🔥 HOT)
2. Then search within results
3. Example: HOT leads named "Krishna"

---

## 12. Tips for Sales Success

### Daily Workflow
1. **Start with DUE filter** - Handle overdue follow-ups first
2. **Check POSITIVE leads** - Call high-interest leads
3. **Review HOT leads** - Focus on named, high-quality leads
4. **Add follow-ups** - Log every interaction
5. **Upload documents** - Keep records organized

### Priority Calling Order
1. 🔥 HOT + 😊 POSITIVE = Call immediately!
2. 🔥 HOT + 😐 NEUTRAL = Call today
3. 🔥 HOT + 😠 NEGATIVE = Handle objections carefully
4. ❄️ COLD + 😊 POSITIVE = Good potential, collect more info
5. ❄️ COLD + 😠 NEGATIVE = Low priority

### Best Practices
- **Log every call** as a follow-up
- **Upload documents** immediately after collection
- **Use email generator** for consistent communication
- **Check sentiment** before calling to prepare approach
- **Set next follow-up dates** to stay organized
- **Hard refresh** (Ctrl+Shift+R) if data seems old

### Keyboard Shortcuts
- **Ctrl+Shift+R** - Hard refresh (load latest data)
- **Click phone number** - Direct dial on mobile
- **Scroll down** - Load more leads (pagination)

---

## 🆘 Troubleshooting

### Data Not Loading
1. Check internet connection
2. Hard refresh: **Ctrl+Shift+R**
3. Clear browser cache
4. Check if GitHub Pages is loading

### Follow-ups Not Saving
- Ensure you're logged in
- Check browser localStorage is enabled
- Try refreshing after adding follow-up

### Documents Not Uploading
- Check file size (max 2MB)
- Ensure file format is supported
- Try a different browser

### Login Issues
- Verify username/password
- Check if Caps Lock is on
- Try "user/user123" if "admin/admin123" fails

---

## 📞 Support Contact

**Technical Issues:**
- Phone: 1800267 629 6 (Toll-Free)
- Mobile: +91 83568 44010

**Feature Requests:**
- Contact admin user
- Submit through GitHub issues

---

## 🎯 Quick Reference Card

### Login
- Admin: `admin` / `admin123`
- User: `user` / `user123`

### Lead Priority
1. 🔥 HOT + 😊 Positive
2. 🔥 HOT + 😐 Neutral
3. ❄️ COLD + 😊 Positive
4. 📅 DUE follow-ups

### Actions per Lead
- 📋 Summary - Quick overview
- 📖 Transcript - Full conversation
- 📅 Follow-ups - Log interactions
- 📄 Docs - Upload/view documents
- 📧 Generate Email - Auto-create email

### Sentiment Guide
- 😊 Positive (Score > 0.3) = Ready to buy
- 😐 Neutral (Score -0.3 to 0.3) = Gathering info
- 😠 Negative (Score < -0.3) = Has concerns

---

**Happy Selling! 🚀**

*RupeeBoss CRM - Making Sales Smarter*
