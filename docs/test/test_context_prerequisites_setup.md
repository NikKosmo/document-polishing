# ---

**\[Workflow\] Legacy Data Archival Process**

**Purpose:** Standardized procedure for moving inactive user logs from hot storage to cold archival systems.

## ---

**Required Files**

| File/Resource | Purpose |
| :---- | :---- |
| archival\_config.yaml | Defines compression ratios and retention periods |
| schema/log\_entry\_v3.json | JSON schema for validating log integrity |
| sys\_env/paths.env | Source of environment variable definitions |

### **System Environment Requirements**

The following environment variables **must** be set in the active shell before execution:

| Variable | Value Description |
| :---- | :---- |
| ETL\_MOUNT\_POINT | Root path to the attached storage volume (e.g., /mnt/data\_volume) |
| ARCHIVE\_TIER\_KEY | Authentication key for the cold storage bucket |
| BATCH\_ID | Unique identifier for this run (Format: YYYYMMDD\_HH) |

⚠️ **STOP** if ETL\_MOUNT\_POINT is not accessible or ARCHIVE\_TIER\_KEY is unset.

## ---

**Input**

* **Source:** Directory located at $ETL\_MOUNT\_POINT/raw\_logs/  
* **Format:** Rotated log files (.log or .txt)  
* **Constraints:**  
  * Files must be older than 30 days (based on file modification time)  
  * Files must not be empty (0 bytes)  
  * Filenames must match pattern: server\_log\_\*.txt

## ---

**Output**

* **File:** archive\_manifest\_$BATCH\_ID.json  
* **Format:** JSON summary of processed files  
* **Location:** Project root  
* **Schema:** Validated against schema/manifest\_output.json (implied standard)

## ---

**Steps**

### **Step 1: Initialize Workspace**

**Action:** specific setup of temporary directories.

**Details:**

* Create a temporary working directory at $ETL\_MOUNT\_POINT/temp/$BATCH\_ID.  
* Verify write access to this directory.  
* Load the settings from archival\_config.yaml into memory.

**Verify:** Directory exists and is writable.

### **Step 2: Filter Candidate Files**

**Action:** Identify files eligible for archival.

**Details:**

* Scan $ETL\_MOUNT\_POINT/raw\_logs/ for files.  
* Filter files based on the "Constraints" defined in the Input section above.  
* Exclude any file currently locked by another process.

**Verify:** List of candidate files is not empty.

### **Step 3: Validate and Compress**

**Action:** Process the filtered log files.

**Details:**

* For each candidate file:  
  1. Validate the first 10 lines against schema/log\_entry\_v3.json.  
  2. If valid, compress the file using the compression ratio specified in archival\_config.yaml.  
  3. Move the compressed file to $ETL\_MOUNT\_POINT/temp/$BATCH\_ID.

**Condition:**

* **If validation fails:** Log error to std\_err and skip the file. Do not stop the workflow.

**Verify:** Count of compressed files in temp directory matches count of valid source files.

### **Step 4: Upload to Cold Storage**

**Action:** Transmit processed data.

**Details:**

* Authenticate using ARCHIVE\_TIER\_KEY.  
* Upload the entire contents of $ETL\_MOUNT\_POINT/temp/$BATCH\_ID to the cold storage bucket.  
* Tag the upload with the current BATCH\_ID.

**Verify:** Receive "200 OK" status from storage API for all transferred files.

### **Step 5: Cleanup and Manifest**

**Action:** Finalize the batch.

**Details:**

* Generate the output JSON file.  
* Write the file to the Project Root.  
* Delete the temporary directory $ETL\_MOUNT\_POINT/temp/$BATCH\_ID.

**Verify:** Output file exists and temporary directory is gone.

## ---

**Validation**

After completion, verify:

1. \[ \] archive\_manifest\_$BATCH\_ID.json exists in project root.  
2. \[ \] JSON is parseable and contains a "success\_count" field.  
3. \[ \] Source files in $ETL\_MOUNT\_POINT/raw\_logs/ remain untouched (this is a copy-archive workflow, not a move workflow).

If validation fails, report which check failed and stop.

## ---

**Error Handling**

| Error | Action |
| :---- | :---- |
| ConfigMissingError | Ensure archival\_config.yaml is in the execution path. |
| AuthFailure | Verify ARCHIVE\_TIER\_KEY is correct and not expired. |
| DiskFull | Check available space on $ETL\_MOUNT\_POINT. |
| SchemaMismatch | Flag file for manual review; do not halt batch. |

