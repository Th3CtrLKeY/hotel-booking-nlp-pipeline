"""
Example script demonstrating email normalization.

Shows how to use the EmailNormalizer to clean raw emails.
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.normalization import EmailNormalizer


def example_1_basic():
    """Basic example with signature removal."""
    print("=" * 60)
    print("Example 1: Basic Normalization with Signature")
    print("=" * 60)
    
    raw_email = """Hi there,

I need a double room from May 12-15, 2026.

Best regards,
John

Sent from my iPhone"""
    
    normalizer = EmailNormalizer()
    result = normalizer.normalize(raw_email)
    
    print("\nOriginal Email:")
    print("-" * 60)
    print(raw_email)
    
    print("\n\nNormalized Email:")
    print("-" * 60)
    print(result['normalized_text'])
    
    print("\n\nRemoved Spans:")
    print("-" * 60)
    for start, end, reason in result['spans_removed']:
        print(f"  {reason}: chars {start}-{end}")
    
    print("\n\nMetadata:")
    print("-" * 60)
    for key, value in result['metadata'].items():
        print(f"  {key}: {value}")
    print()


def example_2_disclaimer():
    """Example with legal disclaimer."""
    print("=" * 60)
    print("Example 2: Disclaimer Removal")
    print("=" * 60)
    
    raw_email = """Dear Reservations,

We need 10 rooms for May 20-22, 2026.

Best,
Jennifer

---
CONFIDENTIAL: This email may contain privileged information."""
    
    normalizer = EmailNormalizer()
    result = normalizer.normalize(raw_email)
    
    print("\nOriginal Length:", len(raw_email), "chars")
    print("Normalized Length:", len(result['normalized_text']), "chars")
    print("Removed:", result['metadata']['chars_removed'], "chars")
    
    print("\n\nNormalized Text:")
    print("-" * 60)
    print(result['normalized_text'])
    print()


def example_3_whitespace():
    """Example with excessive whitespace."""
    print("=" * 60)
    print("Example 3: Whitespace Normalization")
    print("=" * 60)
    
    raw_email = """Hello,


I   need  a   room   for    tonight.



Thanks!"""
    
    normalizer = EmailNormalizer()
    result = normalizer.normalize(raw_email)
    
    print("\nBefore normalization:")
    print(repr(raw_email))
    
    print("\nAfter normalization:")
    print(repr(result['normalized_text']))
    
    print("\n\nNormalization applied:")
    for method in result['metadata']['normalization_applied']:
        print(f"  [+] {method}")
    print()


def example_4_synthetic_email():
    """Example using a synthetic email from dataset."""
    print("=" * 60)
    print("Example 4: Real Synthetic Email (email_007.txt)")
    print("=" * 60)
    
    email_path = Path(__file__).parent.parent / "data" / "raw_emails" / "email_007.txt"
    
    if not email_path.exists():
        print("\nSynthetic email not found. Skipping.")
        return
    
    with open(email_path, 'r') as f:
        raw_email = f.read()
    
    normalizer = EmailNormalizer()
    result = normalizer.normalize(raw_email)
    
    print("\nOriginal:")
    print("-" * 60)
    print(raw_email)
    
    print("\n\nNormalized:")
    print("-" * 60)
    print(result['normalized_text'])
    
    print("\n\nChanges:")
    print("-" * 60)
    print(f"  Original length: {result['metadata']['original_length']} chars")
    print(f"  Normalized length: {result['metadata']['normalized_length']} chars")
    print(f"  Characters removed: {result['metadata']['chars_removed']}")
    print(f"  Spans removed: {len(result['spans_removed'])}")
    print()


def example_5_batch_processing():
    """Example of batch processing multiple emails."""
    print("=" * 60)
    print("Example 5: Batch Processing Synthetic Emails")
    print("=" * 60)
    
    emails_dir = Path(__file__).parent.parent / "data" / "raw_emails"
    
    if not emails_dir.exists():
        print("\nEmails directory not found. Skipping.")
        return
    
    normalizer = EmailNormalizer()
    results = []
    
    email_files = sorted(emails_dir.glob("email_*.txt"))
    
    print(f"\nProcessing {len(email_files)} emails...")
    
    for email_file in email_files[:5]:  # Process first 5
        with open(email_file, 'r') as f:
            raw_email = f.read()
        
        result = normalizer.normalize(raw_email)
        results.append({
            "filename": email_file.name,
            "original_length": result['metadata']['original_length'],
            "normalized_length": result['metadata']['normalized_length'],
            "chars_removed": result['metadata']['chars_removed'],
            "spans_removed": len(result['spans_removed'])
        })
    
    print("\n\nResults:")
    print("-" * 80)
    print(f"{'File':<20} {'Original':<10} {'Normalized':<12} {'Removed':<10} {'Spans':<8}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['filename']:<20} {r['original_length']:<10} {r['normalized_length']:<12} "
              f"{r['chars_removed']:<10} {r['spans_removed']:<8}")
    
    print()


if __name__ == "__main__":
    example_1_basic()
    example_2_disclaimer()
    example_3_whitespace()
    example_4_synthetic_email()
    example_5_batch_processing()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
