"""
Extended tests for date parser - testing month/day formats
"""
import pytest
from datetime import datetime

from backend.app.services.date_parser import parse_relative_date


class TestMonthDayFormats:
    """Tests for month/day formats like '这个月19号'"""
    
    def test_this_month_with_day(self):
        """Test parsing '这个月19号'"""
        reference = datetime(2025, 10, 5, 15, 30, 0)
        result = parse_relative_date("这个月19号", reference)
        
        expected = datetime(2025, 10, 19, 0, 0, 0)
        assert result == expected
    
    def test_this_month_day_chinese(self):
        """Test parsing '本月19日'"""
        reference = datetime(2025, 10, 5, 15, 30, 0)
        result = parse_relative_date("本月19日", reference)
        
        expected = datetime(2025, 10, 19, 0, 0, 0)
        assert result == expected
    
    def test_month_day_format(self):
        """Test parsing '10月19号'"""
        reference = datetime(2025, 10, 5, 15, 30, 0)
        result = parse_relative_date("10月19号", reference)
        
        expected = datetime(2025, 10, 19, 0, 0, 0)
        assert result == expected
    
    def test_month_day_ri_format(self):
        """Test parsing '10月19日'"""
        reference = datetime(2025, 10, 5, 15, 30, 0)
        result = parse_relative_date("10月19日", reference)
        
        expected = datetime(2025, 10, 19, 0, 0, 0)
        assert result == expected
    
    def test_next_month(self):
        """Test parsing '11月5号' (next month)"""
        reference = datetime(2025, 10, 5, 15, 30, 0)
        result = parse_relative_date("11月5号", reference)
        
        expected = datetime(2025, 11, 5, 0, 0, 0)
        assert result == expected

