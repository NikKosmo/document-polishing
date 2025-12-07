Based on your requirements for a **lightweight, CPU-friendly** Python tool, here is the research on sentence embedding options.

### 📊 Quick Comparison

| Feature | **FastEmbed** (Recommended) | **Sentence-Transformers** | **OpenAI API** | **LLM-as-a-Judge** |
| :--- | :--- | :--- | :--- | :--- |
| **Install Size** | **Tiny** (\~150MB w/ model) | Heavy (\~600MB - 1.5GB) | **Micro** (\<10MB) | Micro (\<10MB) |
| **Dependencies** | Minimal (ONNX based) | Heavy (PyTorch) | Minimal (`openai`) | Minimal (`openai` / `anthropic`) |
| **Speed (CPU)** | ⚡️ **Fast** (\~20ms/pair) | ⚡️ Fast (\~30ms/pair) | 🐢 Network bound (\~300ms) | 🐌 Slow (\~1-2s) |
| **Cost** | Free | Free | \~$0.000002 (negligible) | ~$0.05 - $0.50 |
| **Accuracy** | High (BGE/E5 models) | High (SOTA models) | High | **Highest** (Nuanced) |

-----

### 1\. 🏆 Recommendation: FastEmbed (by Qdrant)

This is the best fit for your "lightweight CLI" requirement. It strips out heavy PyTorch dependencies by using ONNX Runtime, designed specifically for CPU inference.

  * **Install Size:** Core library is tiny. Downloads quantized models (\~40MB-200MB) on first run.
  * **Dependencies:** `onnxruntime`, `tokenizers`, `numpy` (No PyTorch/TensorFlow).
  * **CPU Performance:** Optimized for CPU. Very fast for 50-100 pairs.

**Code Example:**

```python
# pip install fastembed
from fastembed import TextEmbedding
from typing import List

def get_similarity(text1: str, text2: str) -> float:
    # Initialize model (downloads ~40MB BGE-small quantization on first run)
    # Using 'bge-small-en-v1.5' is efficient and high quality
    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # Embed both texts (returns generator of numpy arrays)
    embeddings = list(model.embed([text1, text2]))

    # Calculate Cosine Similarity
    import numpy as np
    vec1, vec2 = embeddings[0], embeddings[1]

    # Cosine similarity formula: (A . B) / (||A|| * ||B||)
    similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    return float(similarity)

# Usage
score = get_similarity("Create 3 files", "Generate three documents")
print(f"Similarity: {score:.4f}") # Expect > 0.8
```

  * **Pros:** Zero heavy ML frameworks, fast cold-start, models are pre-quantized for CPU.
  * **Cons:** Fewer model choices than full HuggingFace ecosystem (but covers the best ones like BGE, E5).

-----

### 2\. Standard: Sentence-Transformers

The industry standard. If you already have PyTorch in your environment, use this. If not, it adds significant bloat.

  * **Install Size:** Large. Requires `torch` (\~100MB-800MB depending on OS/Hardware).
  * **Dependencies:** `torch`, `transformers`, `scikit-learn`.
  * **CPU Performance:** Excellent (especially on Apple Silicon via MPS, though FastEmbed is competitive on pure CPU).

**Code Example:**

```python
# pip install sentence-transformers
from sentence_transformers import SentenceTransformer, util

# Load model (downloads ~120MB)
# 'all-MiniLM-L6-v2' is the classic speed/performance balance
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_similarity_st(text1: str, text2: str) -> float:
    embeddings = model.encode([text1, text2])
    # Compute cosine similarity
    score = util.cos_sim(embeddings[0], embeddings[1])
    return float(score.item())

# Usage
print(get_similarity_st("Create 3 files", "Generate three documents"))
```

-----

### 3\. API Option: OpenAI Embeddings

The "Zero Config" option. If you don't want *any* model files locally and have an internet connection.

  * **Install Size:** Minimal (`pip install openai`).
  * **Cost:** `text-embedding-3-small` is priced at $0.02 per 1M tokens. For 100 comparisons, it is effectively **free** ($0.000001).
  * **Anthropic Note:** Anthropic does **not** offer a native first-party embedding API similar to OpenAI's. They typically recommend using Voyage AI. For simplicity, stick to OpenAI if going the API route.

**Code Example:**

```python
# pip install openai
from openai import OpenAI
import numpy as np

client = OpenAI(api_key="YOUR_KEY")

def get_similarity_openai(text1: str, text2: str) -> float:
    resp = client.embeddings.create(
        input=[text1, text2],
        model="text-embedding-3-small"
    )

    v1 = resp.data[0].embedding
    v2 = resp.data[1].embedding

    # Manual Cosine Similarity
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
```

-----

### 4\. Alternative: LLM-as-a-Judge

Is it a viable alternative? **Yes, but with caveats.**

**Tradeoffs:**

  * **Nuance (Winner: LLM):** Embeddings might score "Create 3 files" and "Delete 3 files" as highly similar (0.8+) because they share context and words. An LLM sees the *contradiction*.
  * **Speed (Winner: Embeddings):** An LLM call takes 0.5s - 2s. Comparing 100 pairs sequentially = \~2 minutes. Embeddings take \<1 second total.
  * **Cost (Winner: Embeddings):** LLMs are 100x-1000x more expensive per comparison (though still cheap in absolute terms for small volumes).

**Verdict for your tool:**
Since you only process \~50 text pairs, **LLM-as-a-Judge is actually viable** and likely **more accurate** for "documentation polishing" where subtle logic errors matter more than rough topic similarity.

**Hybrid Strategy (Best of both):**
Use embeddings as a fast filter. If similarity is `> 0.6` (vaguely related) but `< 0.95` (not identical), trigger the LLM to verify if they *actually* agree.

**LLM Judge Code:**

```python
def check_agreement_llm(text1: str, text2: str) -> bool:
    prompt = f"""
    Do these two documentation instructions mean the same thing?
    A: "{text1}"
    B: "{text2}"

    Reply ONLY with JSON: {{"agree": boolean, "reason": "short explanation"}}
    """
    # ... call GPT-4o-mini or Claude-3-Haiku ...
    return json_response['agree']
```

### Final Summary for Your CLI Tool

1.  **Primary Engine:** Use **`FastEmbed`** with `BAAI/bge-small-en-v1.5`. It meets every requirement: Python 3.8+, no heavy PyTorch, runs on CPU, fast, \<200MB total footprint.
2.  **Validation:** If you find embeddings are "too loose" (marking contradictions as similar), switch to the **LLM-as-a-Judge** method using `gpt-4o-mini` or `claude-3-haiku`, as your volume (50-100) is low enough to handle the latency.

Here is a video explaining embeddings further:
[Embeddings and Vector Databases Crash Course](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DySus5ZB0b_c)
This video is relevant as it provides a solid conceptual foundation for understanding how embeddings work and how to choose the right model for semantic similarity tasks.