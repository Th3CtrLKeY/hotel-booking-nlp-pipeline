"""
Unit tests for email normalization module.

Tests signature removal, disclaimer removal, whitespace normalization,
and span tracking functionality.
"""

import pytest
from pathlib import Path
from pipeline.normalization import (
    EmailNormalizer,
    remove_signatures,
    remove_disclaimers,
    remove_greetings,
    normalize_whitespace
)


class TestSignatureRemoval:
    """Test email signature removal."""
    
    def test_iphone_signature(self):
        """Test removal of iPhone signature."""
        email = "I need a room.\n\nSent from my iPhone"
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert "Sent from my iPhone" not in result["normalized_text"]
        assert "I need a room." in result["normalized_text"]
        assert len(result["spans_removed"]) > 0
        assert result["spans_removed"][0][2] == "signature"
    
    def test_outlook_signature(self):
        """Test removal of Outlook signature."""
        email = "Book a double room.\n\nGet Outlook for iOS"
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert "Get Outlook" not in result["normalized_text"]
        assert "Book a double room." in result["normalized_text"]
    
    def test_best_regards_signature(self):
        """Test removal of 'Best regards' signature."""
        email = "Need a room from May 5-7.\n\nBest regards,\nJohn"
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert "Best regards" not in result["normalized_text"]
        assert "John" not in result["normalized_text"]
        assert "Need a room from May 5-7." in result["normalized_text"]
    
    def test_no_signature(self):
        """Test email with no signature."""
        email = "I need a double room for tonight."
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert result["normalized_text"] == email.strip()
        # May still have whitespace normalization
        assert "signature" not in [span[2] for span in result["spans_removed"]]


class TestDisclaimerRemoval:
    """Test legal disclaimer removal."""
    
    def test_confidential_disclaimer(self):
        """Test removal of confidential disclaimer."""
        email = """Need 5 rooms for May 20-22.

---
CONFIDENTIAL: This email may contain privileged information."""
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert "CONFIDENTIAL" not in result["normalized_text"]
        assert "Need 5 rooms for May 20-22." in result["normalized_text"]
        assert any(span[2] == "disclaimer" for span in result["spans_removed"])
    
    def test_disclaimer_keyword(self):
        """Test removal of DISCLAIMER keyword."""
        email = """Book a suite.

DISCLAIMER: This message is for the intended recipient only."""
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert "DISCLAIMER" not in result["normalized_text"]
        assert "Book a suite." in result["normalized_text"]


class TestWhitespaceNormalization:
    """Test whitespace normalization."""
    
    def test_multiple_spaces(self):
        """Test collapsing multiple spaces."""
        email = "I  need   a    room"
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert result["normalized_text"] == "I need a room"
    
    def test_excessive_newlines(self):
        """Test limiting excessive newlines."""
        email = "Hello\n\n\n\n\nI need a room"
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        # Should reduce to max 2 newlines
        assert "\n\n\n" not in result["normalized_text"]
        assert "Hello" in result["normalized_text"]
        assert "I need a room" in result["normalized_text"]
    
    def test_tab_normalization(self):
        """Test converting tabs to spaces."""
        email = "Name:\tJohn\nRooms:\t2"
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert "\t" not in result["normalized_text"]
        assert "Name:" in result["normalized_text"]
    
    def test_leading_trailing_whitespace(self):
        """Test trimming leading/trailing whitespace."""
        email = "   I need a room   \n\n  "
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert result["normalized_text"] == "I need a room"


class TestSpanTracking:
    """Test span tracking and provenance."""
    
    def test_span_structure(self):
        """Test that spans have correct structure."""
        email = "Need a room.\n\nSent from my iPhone"
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        for span in result["spans_removed"]:
            assert len(span) == 3
            assert isinstance(span[0], int)  # start
            assert isinstance(span[1], int)  # end
            assert isinstance(span[2], str)  # reason
            assert span[1] > span[0]  # end > start
    
    def test_multiple_removals(self):
        """Test tracking multiple removed spans."""
        email = """Hi there,

I need a double room.

Best regards,
John

Sent from my iPhone"""
        
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        # Should have signature removal
        assert len(result["spans_removed"]) > 0
    
    def test_metadata_accuracy(self):
        """Test metadata reflects actual changes."""
        email = "Hello   World\n\nSent from my iPhone"
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert result["metadata"]["original_length"] == len(email)
        assert result["metadata"]["normalized_length"] == len(result["normalized_text"])
        assert result["metadata"]["chars_removed"] > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_email(self):
        """Test handling of empty email."""
        normalizer = EmailNormalizer()
        result = normalizer.normalize("")
        
        assert result["normalized_text"] == ""
        assert result["spans_removed"] == []
        assert result["metadata"]["chars_removed"] == 0
    
    def test_only_signature(self):
        """Test email that is only a signature."""
        email = "Sent from my iPhone"
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        # Should be nearly empty after removal
        assert len(result["normalized_text"]) < 10
    
    def test_very_long_email(self):
        """Test handling of very long emails."""
        email = "I need a room. " * 1000 + "\n\nSent from my iPhone"
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert "Sent from my iPhone" not in result["normalized_text"]
        assert "I need a room." in result["normalized_text"]
    
    def test_special_characters(self):
        """Test emails with special characters."""
        email = "Need a room for €100/night.\nContacts: info@hotel.com\n\nSent from my iPhone"
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        assert "€100/night" in result["normalized_text"]
        assert "info@hotel.com" in result["normalized_text"]


class TestIntegration:
    """Integration tests with real synthetic emails."""
    
    def test_synthetic_email_007(self):
        """Test normalization on email_007.txt (has iPhone signature)."""
        email_path = Path(__file__).parent.parent / "data" / "raw_emails" / "email_007.txt"
        
        if not email_path.exists():
            pytest.skip("Synthetic email not found")
        
        with open(email_path, 'r') as f:
            email = f.read()
        
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        # Should remove "Sent from my iPhone"
        assert "Sent from my iPhone" not in result["normalized_text"]
        # Should keep booking content
        assert "single room" in result["normalized_text"].lower()
    
    def test_synthetic_email_008(self):
        """Test normalization on email_008.txt (has disclaimer)."""
        email_path = Path(__file__).parent.parent / "data" / "raw_emails" / "email_008.txt"
        
        if not email_path.exists():
            pytest.skip("Synthetic email not found")
        
        with open(email_path, 'r') as f:
            email = f.read()
        
        normalizer = EmailNormalizer()
        result = normalizer.normalize(email)
        
        # Should remove disclaimer
        assert "CONFIDENTIAL" not in result["normalized_text"]
        # Should keep booking content
        assert "10 rooms" in result["normalized_text"]


class TestPerformance:
    """Performance tests."""
    
    def test_normalization_speed(self):
        """Test that normalization is fast (<50ms per email)."""
        import time
        
        email = """Hi there,

I need a double room from May 12 to May 15, 2026 for 2 adults.

Please let me know availability.

Best regards,
John Smith

Sent from my iPhone"""
        
        normalizer = EmailNormalizer()
        
        start = time.time()
        for _ in range(100):
            normalizer.normalize(email)
        end = time.time()
        
        avg_time = (end - start) / 100
        assert avg_time < 0.05  # Less than 50ms per email


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
