# Feedback for test_context_cross_references_steps.md

**Date:** 2025-12-27
**Testing Result:** 2 critical ambiguities detected with session management enabled
**Purpose:** Improve document clarity by resolving ambiguities

---

## Critical Issues Found

### Issue 1: Section "Step 2: Sanitize Data" - PII Handling Unclear

**Current Text:**
```
* If priority_level (from Input) is "High-Security", perform a regex sweep for PII (emails/phone numbers).
```

**Problem:**
Models disagree on what "perform a regex sweep for PII" means:
- Claude interprets: Delete PII entirely
- Gemini interprets: Replace with placeholders like `[REDACTED_EMAIL]`, `[REDACTED_PHONE]`
- Codex interprets: "Remove or flag" - leaving action ambiguous

**Required Clarification:**
Please specify EXACTLY what should happen to detected PII:

**Option A (Deletion):**
```
* If priority_level (from Input) is "High-Security", perform a regex sweep to detect and DELETE all PII (emails/phone numbers) from the string.
```

**Option B (Redaction with placeholders):**
```
* If priority_level (from Input) is "High-Security", perform a regex sweep to detect and REPLACE all PII with placeholders:
  - Email addresses → `[EMAIL_REDACTED]`
  - Phone numbers → `[PHONE_REDACTED]`
```

**Option C (Masking):**
```
* If priority_level (from Input) is "High-Security", perform a regex sweep to detect and MASK all PII:
  - Email addresses → Show only domain (e.g., `***@example.com`)
  - Phone numbers → Show only last 4 digits (e.g., `***-***-1234`)
```

Choose ONE approach and state it explicitly.

---

### Issue 2: Section "Step 2: Sanitize Data" - Script Delimiter Definition Unclear

**Current Text:**
```
* Remove all HTML tags and script delimiters.
```

**Problem:**
Models disagree on what "script delimiters" means:
- Claude: Questions if it includes template literals (`${}`, `%%`, `[[]]`)
- Gemini: Questions if it includes server-side delimiters (`<?php ?>`, `<% %>`)
- Codex: Keeps it vague as "similar markers"

**Required Clarification:**
Please specify EXACTLY what script delimiters to remove:

**Recommended Clarification:**
```
* Remove all HTML tags (e.g., `<div>`, `<p>`, `<script>`, `</script>`, `<style>`) and their content.
* Script delimiters include: `<script>` and `</script>` tags only. Leave template syntax like `${}` or `<% %>` unchanged.
```

Or if broader:
```
* Remove all HTML tags and script delimiters, including:
  - HTML tags: `<tag>`, `</tag>` (all standard HTML tags)
  - JavaScript: `<script>...</script>` blocks
  - Server-side: `<?php ... ?>`, `<% ... %>`
  - Template literals: `${}`, `%%`, `[[]]`
```

Choose ONE scope and list it explicitly.

---

### Issue 3: Section "Step 2: Sanitize Data" - Phone Number Format Unclear

**Current Text:**
```
* If priority_level (from Input) is "High-Security", perform a regex sweep for PII (emails/phone numbers).
```

**Problem:**
All three models question which phone number formats to detect:
- US-only? (e.g., `(555) 123-4567`, `555-123-4567`, `555.123.4567`)
- International? (e.g., `+1-555-123-4567`, `+44 20 1234 5678`)
- With/without country codes?

**Required Clarification:**
```
* If priority_level (from Input) is "High-Security", perform a regex sweep for PII:
  - Email addresses: Standard format (e.g., `user@example.com`)
  - Phone numbers: US format only - detect patterns like:
    - `(555) 123-4567`
    - `555-123-4567`
    - `555.123.4567`
    - `+1-555-123-4567`
```

Or if international:
```
* If priority_level (from Input) is "High-Security", perform a regex sweep for PII:
  - Email addresses: Standard format (e.g., `user@example.com`)
  - Phone numbers: International formats including:
    - US: `(555) 123-4567`, `555-123-4567`, `+1-555-123-4567`
    - UK: `+44 20 1234 5678`
    - Generic: Any sequence starting with `+` followed by 10-15 digits with optional separators
```

---

### Issue 4: Section "Validation" - Ambiguous Reference to "item 2 in Step 2"

**Current Text:**
```
3. [ ] If priority_level was "High-Security", confirm that **item 2 in Step 2** was executed by checking for the absence of email patterns in the final payload.
```

**Problem:**
"item 2 in Step 2" is ambiguous. Step 2 contains:
- **Action** (first line)
- **Details** (bulleted list with 2 items)
- **Verify** (last line)

Models disagree on what "item 2" refers to:
- Is it the second bullet point under Details?
- Is it the second numbered step in a sequence?
- Is it something else?

**Required Clarification:**

**Option A (Be specific about bullet point):**
```
3. [ ] If priority_level was "High-Security", confirm that the PII regex sweep (the second bullet point under Details in Step 2) was executed by checking for the absence of email patterns in the final payload.
```

**Option B (Reference the action directly):**
```
3. [ ] If priority_level was "High-Security", confirm that PII removal was executed (as specified in Step 2: "perform a regex sweep for PII") by checking for the absence of email patterns in the final payload.
```

**Option C (Avoid cross-references entirely):**
```
3. [ ] If priority_level was "High-Security", confirm PII removal was successful by checking for the absence of email patterns in the final payload.
```

Choose ONE approach and avoid ambiguous cross-references.

---

### Issue 5: Section "Validation" - Check 3 Only Validates Emails, Not Phone Numbers

**Current Text:**
```
3. [ ] If priority_level was "High-Security", confirm that **item 2 in Step 2** was executed by checking for the absence of email patterns in the final payload.
```

**Problem:**
Step 2 mentions removing BOTH emails AND phone numbers, but Check 3 only validates emails.

**Why this is confusing:**
- Models question: "Should phone numbers also be checked?"
- Models note: "Validation is incomplete if phone numbers aren't verified"
- Models ask: "Was this intentional or an oversight?"

**Required Clarification:**

**Option A (Validate both):**
```
3. [ ] If priority_level was "High-Security", confirm PII removal was successful by checking for the absence of BOTH:
   - Email address patterns (e.g., `user@example.com`)
   - Phone number patterns (e.g., `555-123-4567`, `(555) 123-4567`)
```

**Option B (Validate emails only, explain why):**
```
3. [ ] If priority_level was "High-Security", confirm PII removal was successful by checking for the absence of email patterns.

   **Note:** Phone numbers are also removed in Step 2, but validation only checks emails as a sample verification. Full PII audit can be performed manually if needed.
```

**Option C (Add separate check for phone numbers):**
```
3. [ ] If priority_level was "High-Security", confirm email removal by checking for absence of email patterns.
4. [ ] If priority_level was "High-Security", confirm phone number removal by checking for absence of phone patterns.
```

Choose ONE approach and be explicit.

---

### Issue 6: Section "Validation" - Session ID Retrieval Mechanism Unclear

**Current Text:**
```
1. [ ] The sid in the final package matches the ID recorded in Step 1.
```

**Problem:**
Models disagree on HOW to retrieve the Session ID from Step 1:
- Claude assumes: Read from `logs/session_manifest.md` file
- Gemini assumes: "Session ID is accessible" (no mechanism)
- Codex assumes: "Session ID was recorded" (no mechanism)

**Required Clarification:**
```
1. [ ] The sid in the final package matches the ID recorded in Step 1.

   **Verification method:**
   - Open the `logs/session_manifest.md` file
   - Locate the most recent entry with status "IN_PROGRESS"
   - Extract the Session ID from that entry (format: `[Timestamp] - ID: [Session_ID] - Status: IN_PROGRESS`)
   - Compare this ID with the `sid` field in the final package JSON
```

---

### Issue 7: Section "Validation" - Test Environment Determination Unclear

**Current Text:**
```
2. [ ] The payload is successfully decryptable using the corresponding private key (test environment only).
```

**Problem:**
Models disagree on HOW to determine "test environment only":
- Environment variable?
- Configuration file?
- Command-line flag?
- Hard-coded check?

**Required Clarification:**
```
2. [ ] The payload is successfully decryptable using the corresponding private key (test environment only).

   **Test environment determination:**
   - Check environment variable: `ENVIRONMENT` (values: "test" or "production")
   - If `ENVIRONMENT=test`, proceed with decryption check
   - If `ENVIRONMENT=production`, skip this check (mark as "N/A")
   - If variable not set, default to "production" (skip check)
```

Or if using config file:
```
2. [ ] The payload is successfully decryptable using the corresponding private key (test environment only).

   **Test environment determination:**
   - Read `config/environment.yaml` file
   - Check `environment` field (values: "test", "staging", "production")
   - If value is "test", proceed with decryption check
   - Otherwise, skip this check (mark as "N/A")
```

---

### Issue 8: Section "Validation" - Private Key Location Unclear

**Current Text:**
```
2. [ ] The payload is successfully decryptable using the corresponding private key (test environment only).
```

**Problem:**
- Required Files section lists: `keys/public_key.pem` (for encryption)
- Validation mentions: "corresponding private key"
- Models ask: "Where is the private key located?"

**Required Clarification:**
```
2. [ ] The payload is successfully decryptable using the corresponding private key (test environment only).

   **Private key location:**
   - File: `keys/private_key.pem`
   - This is the RSA private key corresponding to the `keys/public_key.pem` public key used in Step 3
```

And add to Required Files section:
```
| File | Purpose |
| :---- | :---- |
| keys/public_key.pem | The RSA public key used for the encryption step (Step 3). |
| keys/private_key.pem | The RSA private key used for decryption verification (test environment only). |
```

---

### Issue 9: Section "Validation" - Encrypted vs Decrypted Payload for Check 3

**Current Text:**
```
3. [ ] If priority_level was "High-Security", confirm that **item 2 in Step 2** was executed by checking for the absence of email patterns in the final payload.
```

**Problem:**
Models are confused about WHICH payload to check:
- Gemini: Explicitly states must check DECRYPTED payload (logical - can't search encrypted data)
- Codex: Notes contradiction of checking encrypted payload for email patterns
- Claude: Ambiguous about this

**Required Clarification:**
```
3. [ ] If priority_level was "High-Security", confirm PII removal was successful:

   **Verification method:**
   - First, decrypt the payload from the final package using the private key (see Check 2)
   - Apply regex pattern to search the DECRYPTED payload for email address patterns
   - Confirm NO email patterns are found
   - If any email patterns are found, validation fails

   **Note:** This check requires the decrypted payload from Check 2. If Check 2 was skipped (production environment), this check should also be skipped.
```

---

## Summary of Required Changes

### Critical (Must Fix)
1. **Step 2:** Specify whether PII is deleted, redacted, or masked
2. **Step 2:** Define exactly what "script delimiters" includes
3. **Step 2:** Specify phone number formats to detect
4. **Validation Check 3:** Fix ambiguous "item 2 in Step 2" reference
5. **Validation Check 3:** Either validate both emails+phones or explain why only emails
6. **Validation Check 1:** Specify how to retrieve Session ID
7. **Validation Check 2:** Specify how to determine test environment
8. **Validation Check 2:** Specify private key location
9. **Validation Check 3:** Clarify to check DECRYPTED payload

### Document Quality Improvements
- Add `keys/private_key.pem` to Required Files section
- Make cross-references explicit (avoid "item 2 in Step 2" style references)
- Add verification method details to each validation check
- Consider adding examples for regex patterns if specifying exact formats

---

## Testing Recommendation

After fixing these issues, re-test with the document polishing system to verify:
- ✅ Ambiguity count should decrease significantly
- ✅ Model interpretations should converge (higher similarity score)
- ✅ Models should agree on implementation details

Expected result: **0 critical ambiguities** (document fully specified)

---

**Feedback prepared by:** Document Polishing System v0.3.0
**Analysis method:** LLM-as-Judge with session management
**Models used:** Claude, Gemini, Codex
