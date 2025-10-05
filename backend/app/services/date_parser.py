"""
Date Parser - 日期解析工具
精确计算相对日期（明天、下周一等）
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple


def parse_relative_date(
    relative_date_str: str,
    reference_time: Optional[datetime] = None
) -> Optional[datetime]:
    """
    解析相对日期为具体日期
    
    Args:
        relative_date_str: 相对日期字符串（如"明天"、"下周一"）
        reference_time: 参考时间（默认为当前时间）
        
    Returns:
        解析后的日期（保留时分秒为00:00:00）
    """
    if reference_time is None:
        reference_time = datetime.now()
    
    # 标准化输入
    date_str = relative_date_str.strip().lower()
    
    # 今天
    if date_str in ['今天', '今日']:
        return reference_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 明天
    if date_str in ['明天', '明日']:
        tomorrow = reference_time + timedelta(days=1)
        return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 后天
    if date_str in ['后天']:
        day_after = reference_time + timedelta(days=2)
        return day_after.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 大后天
    if date_str in ['大后天']:
        day_after_after = reference_time + timedelta(days=3)
        return day_after_after.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 下周X
    weekday_map = {
        '周一': 0, '星期一': 0, '礼拜一': 0,
        '周二': 1, '星期二': 1, '礼拜二': 1,
        '周三': 2, '星期三': 2, '礼拜三': 2,
        '周四': 3, '星期四': 3, '礼拜四': 3,
        '周五': 4, '星期五': 4, '礼拜五': 4,
        '周六': 5, '星期六': 5, '礼拜六': 5,
        '周日': 6, '星期日': 6, '礼拜日': 6, '周天': 6
    }
    
    # 下周X（按日常理解：下一个出现的该星期X）
    if date_str.startswith('下周') or date_str.startswith('下星期'):
        for weekday_name, weekday_num in weekday_map.items():
            if weekday_name in date_str:
                current_weekday = reference_time.weekday()
                
                # 简单算法：从明天开始往后找，找到第一个匹配的星期X
                for days in range(1, 15):  # 最多找2周
                    candidate = reference_time + timedelta(days=days)
                    if candidate.weekday() == weekday_num:
                        return candidate.replace(hour=0, minute=0, second=0, microsecond=0)
                break
        
        return None
    
    # 本周X（这周）
    if date_str.startswith('本周') or date_str.startswith('这周') or date_str.startswith('这星期'):
        for weekday_name, weekday_num in weekday_map.items():
            if weekday_name in date_str:
                current_weekday = reference_time.weekday()
                days_ahead = weekday_num - current_weekday
                
                # 如果是负数，说明这天已经过了，取下周
                if days_ahead < 0:
                    days_ahead += 7
                elif days_ahead == 0:
                    # 就是今天
                    return reference_time.replace(hour=0, minute=0, second=0, microsecond=0)
                
                target_date = reference_time + timedelta(days=days_ahead)
                return target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # X天后
    if '天后' in date_str or '日后' in date_str:
        try:
            # 提取数字
            import re
            numbers = re.findall(r'\d+', date_str)
            if numbers:
                days = int(numbers[0])
                return reference_time + timedelta(days=days)
        except:
            pass
    
    # 这个月X号、本月X号
    if '这个月' in date_str or '本月' in date_str:
        try:
            import re
            # 提取数字（号数）
            numbers = re.findall(r'\d+', date_str)
            if numbers:
                day_num = int(numbers[0])
                # 使用当前月份
                target_date = reference_time.replace(
                    day=day_num,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                return target_date
        except ValueError:
            pass
    
    # X月X号（如"10月19号"）
    try:
        import re
        # 匹配 "X月X号" 或 "X月X日"
        match = re.search(r'(\d+)月(\d+)[号日]', date_str)
        if match:
            month_num = int(match.group(1))
            day_num = int(match.group(2))
            
            # 使用当前年份
            year = reference_time.year
            
            # 如果月份小于当前月份，可能是明年
            if month_num < reference_time.month:
                year += 1
            
            target_date = datetime(year, month_num, day_num, 0, 0, 0)
            return target_date
    except (ValueError, AttributeError):
        pass
    
    return None


def parse_time_period(time_period_str: str) -> Tuple[Optional[int], Optional[int]]:
    """
    解析时间段为小时范围
    
    Args:
        time_period_str: 时间段字符串（如"上午"、"下午"）
        
    Returns:
        (start_hour, end_hour) 或 (None, None)
    """
    period = time_period_str.strip().lower()
    
    if period in ['上午', '早上']:
        return (9, 12)
    elif period in ['中午']:
        return (12, 13)
    elif period in ['下午']:
        return (14, 18)
    elif period in ['晚上', '傍晚']:
        return (18, 23)
    elif period in ['凌晨', '深夜']:
        return (0, 6)
    
    return (None, None)


def build_datetime(
    date: datetime,
    hour: Optional[int] = None,
    minute: Optional[int] = None
) -> datetime:
    """
    构建完整的datetime对象
    
    Args:
        date: 基础日期
        hour: 小时（可选）
        minute: 分钟（可选）
        
    Returns:
        完整的datetime对象
    """
    return date.replace(
        hour=hour if hour is not None else 0,
        minute=minute if minute is not None else 0,
        second=0,
        microsecond=0
    )

