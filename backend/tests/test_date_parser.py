"""
Unit tests for date parser service.
Tests precise date calculation for relative dates.
"""
import pytest
from datetime import datetime, timedelta

from backend.app.services.date_parser import (
    parse_relative_date,
    parse_time_period,
    build_datetime
)


class TestParseRelativeDate:
    """Tests for parse_relative_date function"""
    
    def test_today(self):
        """Test parsing '今天'"""
        reference = datetime(2025, 10, 5, 15, 30, 0)  # 周六下午3:30
        result = parse_relative_date("今天", reference)
        
        assert result.date() == reference.date()
        assert result.hour == 0
        assert result.minute == 0
    
    def test_tomorrow(self):
        """Test parsing '明天'"""
        reference = datetime(2025, 10, 5, 15, 30, 0)  # 周六
        result = parse_relative_date("明天", reference)
        
        expected = datetime(2025, 10, 6, 0, 0, 0)  # 周日
        assert result == expected
    
    def test_day_after_tomorrow(self):
        """Test parsing '后天'"""
        reference = datetime(2025, 10, 5, 15, 30, 0)
        result = parse_relative_date("后天", reference)
        
        expected = datetime(2025, 10, 7, 0, 0, 0)
        assert result == expected
    
    def test_next_monday_from_sunday(self):
        """Test parsing '下周一' from Sunday"""
        reference = datetime(2025, 10, 5, 15, 30, 0)  # 周日(实际)
        result = parse_relative_date("下周一", reference)
        
        # 周日说"下周一"，应该是明天(10/6)
        expected = datetime(2025, 10, 6, 0, 0, 0)
        assert result == expected
    
    def test_next_wednesday(self):
        """Test parsing '下周三'"""
        reference = datetime(2025, 10, 5, 15, 30, 0)  # 周日
        result = parse_relative_date("下周三", reference)
        
        # 周日说"下周三" = 10/8
        expected = datetime(2025, 10, 8, 0, 0, 0)
        assert result == expected
    
    def test_next_monday_from_saturday(self):
        """Test parsing '下周一' from Saturday"""
        reference = datetime(2025, 10, 4, 15, 30, 0)  # 周六
        result = parse_relative_date("下周一", reference)
        
        # 周六说"下周一" = 10/6
        expected = datetime(2025, 10, 6, 0, 0, 0)
        assert result == expected


class TestParseTimePeriod:
    """Tests for parse_time_period function"""
    
    def test_morning(self):
        """Test parsing '上午'"""
        start, end = parse_time_period("上午")
        assert start == 9
        assert end == 12
    
    def test_afternoon(self):
        """Test parsing '下午'"""
        start, end = parse_time_period("下午")
        assert start == 14
        assert end == 18
    
    def test_evening(self):
        """Test parsing '晚上'"""
        start, end = parse_time_period("晚上")
        assert start == 18
        assert end == 23
    
    def test_unknown(self):
        """Test parsing unknown period"""
        start, end = parse_time_period("未知")
        assert start is None
        assert end is None


class TestBuildDatetime:
    """Tests for build_datetime function"""
    
    def test_build_with_hour(self):
        """Test building datetime with hour"""
        base = datetime(2025, 10, 5, 0, 0, 0)
        result = build_datetime(base, hour=10)
        
        assert result == datetime(2025, 10, 5, 10, 0, 0)
    
    def test_build_with_hour_and_minute(self):
        """Test building datetime with hour and minute"""
        base = datetime(2025, 10, 5, 0, 0, 0)
        result = build_datetime(base, hour=14, minute=30)
        
        assert result == datetime(2025, 10, 5, 14, 30, 0)

