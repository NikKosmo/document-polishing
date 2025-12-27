# Multi-Stage Secure Data Transmission Workflow

**Purpose:** This workflow coordinates the sanitization, encryption, and packaging of data for secure transmission between internal services.

## Required Files

| File | Purpose |
| :---- | :---- |
| ENCRYPTION\_STANDARDS.md | Contains the specific algorithms and padding rules. |
| keys/public\_key.pem | The RSA key used for the encryption step. |
| logs/session\_manifest.md | The source of truth for all generated session metadata. |

⚠️ **STOP** if any file above is not accessible. Report which file is missing.

## Input

* **Source:** raw\_payload.json
* **Format:** JSON object containing user\_id, data\_string, and priority\_level.
* **Constraints:**
  * priority\_level must be either "Standard" or "High-Security".
  * data\_string must not exceed 4096 characters.

## Output

* **File:** final\_transmission.pkg
* **Format:** Binary package containing the encrypted payload and metadata.
* **Location:** ./output/ directory.

## Steps

### Step 1: Initialize Session

**Action:** Generate a unique Session ID and record it.

**Details:**

1. Generate a 16-character alphanumeric string.
2. Open logs/session\_manifest.md.
3. Append a new entry: \[Timestamp\] \- ID: \[Session\_ID\] \- Status: IN\_PROGRESS.

**Verify:** The Session ID is written to the manifest file.

### Step 2: Sanitize Data

**Action:** Strip restricted characters from the data\_string found in the **Input** section.

**Details:**

* Remove all HTML tags and script delimiters.
* If priority\_level (from Input) is "High-Security", perform a regex sweep for PII (emails/phone numbers).

**Verify:** The sanitized string is held in memory for Step 3\.

### Step 3: Encrypt Payload

**Action:** Encrypt the sanitized string using the key listed in **Required Files**.

**Details:**

* **Take the sanitized string from Step 2\.**
* Apply RSA encryption using public\_key.pem.
* Use the padding rules specified in ENCRYPTION\_STANDARDS.md.

**Verify:** The output is a Base64 encoded string.

### Step 4: Assemble Package

**Action:** Combine all previous outputs into a final package.

**Details:**

1. Create a JSON structure with the following fields:
   * sid: **The Session ID generated in Step 1\.**
   * payload: **The encrypted string created in Step 3\.**
   * security\_flag: The original priority\_level from Input.

**Verify:** The object contains all three fields with no null values.

### Step 5: Write Output

**Action:** Convert the object from **Step 4** into a binary format and save.

**Verify:** File final\_transmission.pkg exists in the ./output/ directory.

## Validation

After completion, verify:

1. \[ \] The sid in the final package matches the ID recorded in Step 1\.
2. \[ \] The payload is successfully decryptable using the corresponding private key (test environment only).
3. \[ \] If priority\_level was "High-Security", confirm that **item 2 in Step 2** was executed by checking for the absence of email patterns in the final payload.

If validation fails, report which check failed and stop.

## Error Handling

| Error | Action |
| :---- | :---- |
| public\_key.pem missing | Stop and report missing dependency from **Required Files**. |
| Step 3 encryption fails | Log error to session\_manifest.md referencing the **Session ID from Step 1** and Exit. |
| Input format invalid | Report "Schema mismatch in Input" and do not proceed to **Step 1**. |

Would you like me to generate a Python script that implements the logic of this specific workflow?