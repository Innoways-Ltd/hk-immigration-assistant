"""
Comprehensive Test Script for Task Generation Optimization
"""
import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict

# Add agent directory to path
sys.path.insert(0, '/home/ubuntu/hk-immigration-assistant/agent')

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/home/ubuntu/hk-immigration-assistant/agent/.env')

from immigration.comprehensive_task_generator import generate_comprehensive_tasks

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(text.center(80))
    print("=" * 80)

def print_section(text):
    """Print a formatted section"""
    print("\n" + "-" * 80)
    print(text)
    print("-" * 80)

async def run_test(test_name, customer_info, messages):
    """Run a single test case"""
    print_header(f"TEST: {test_name}")
    
    print("\n📋 Test Configuration:")
    print(f"  Arrival: {customer_info['arrival_date']}")
    print(f"  Location: {customer_info['destination_city']}")
    print(f"  Accommodation: {customer_info.get('temporary_accommodation', 'N/A')}")
    print(f"  Office: {customer_info.get('office_location', 'N/A')}")
    
    print("\n💬 User Message:")
    for msg in messages:
        if msg.get('role') == 'user':
            content = msg.get('content', '')
            if len(content) > 150:
                content = content[:150] + "..."
            print(f"  {content}")
    
    print("\n⏳ Generating tasks...")
    start_time = datetime.now()
    
    try:
        tasks = await generate_comprehensive_tasks(messages, customer_info)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"✅ Generated {len(tasks)} tasks in {elapsed:.2f} seconds")
        
        return analyze_results(tasks, customer_info)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_results(tasks, customer_info):
    """Analyze test results"""
    if not tasks:
        print("❌ No tasks generated")
        return None
    
    # Group by day
    tasks_by_day = defaultdict(list)
    for task in tasks:
        day_offset = task.get("day_offset", 0)
        tasks_by_day[day_offset].append(task)
    
    # Calculate statistics
    stats = {
        "total_tasks": len(tasks),
        "total_days": len(tasks_by_day),
        "max_tasks_per_day": max(len(tasks) for tasks in tasks_by_day.values()),
        "avg_tasks_per_day": len(tasks) / len(tasks_by_day) if tasks_by_day else 0,
        "core_tasks": len([t for t in tasks if t.get("activity_type") == "core"]),
        "essential_tasks": len([t for t in tasks if t.get("activity_type") == "essential"]),
        "extended_tasks": len([t for t in tasks if t.get("activity_type") == "extended"]),
    }
    
    print_section("📊 Statistics")
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  Total days: {stats['total_days']}")
    print(f"  Max tasks per day: {stats['max_tasks_per_day']}")
    print(f"  Avg tasks per day: {stats['avg_tasks_per_day']:.1f}")
    print(f"  Core tasks: {stats['core_tasks']}")
    print(f"  Essential tasks: {stats['essential_tasks']}")
    print(f"  Extended tasks: {stats['extended_tasks']}")
    
    # Show daily distribution (first 10 days)
    print_section("📅 Daily Distribution (First 10 Days)")
    
    arrival_date = datetime.fromisoformat(customer_info['arrival_date'])
    
    for day in sorted(tasks_by_day.keys())[:10]:
        day_tasks = tasks_by_day[day]
        task_date = arrival_date + timedelta(days=day)
        
        # Count by type
        core_count = len([t for t in day_tasks if t.get("activity_type") == "core"])
        essential_count = len([t for t in day_tasks if t.get("activity_type") == "essential"])
        extended_count = len([t for t in day_tasks if t.get("activity_type") == "extended"])
        
        status_icon = "✅" if len(day_tasks) <= 4 else "⚠️"
        
        print(f"\n{status_icon} Day {day} ({task_date.strftime('%b %d')}): {len(day_tasks)} tasks")
        print(f"   Core: {core_count} | Essential: {essential_count} | Extended: {extended_count}")
        
        # Show task names
        for i, task in enumerate(day_tasks[:5], 1):  # Show first 5
            task_name = task.get("title", task.get("name", "Unnamed"))
            if len(task_name) > 50:
                task_name = task_name[:50] + "..."
            print(f"   {i}. {task_name}")
        
        if len(day_tasks) > 5:
            print(f"   ... and {len(day_tasks) - 5} more tasks")
    
    # Validation checks
    print_section("✓ Validation Checks")
    
    issues = []
    warnings = []
    
    # Check 1: Max tasks per day
    for day, day_tasks in tasks_by_day.items():
        if len(day_tasks) > 4:
            issues.append(f"Day {day} has {len(day_tasks)} tasks (exceeds limit of 4)")
    
    # Check 2: Core activity focus
    for day, day_tasks in tasks_by_day.items():
        core_tasks = [t for t in day_tasks if t.get("activity_type") == "core"]
        if core_tasks and len(day_tasks) > 2:
            warnings.append(f"Day {day} has {len(core_tasks)} core task(s) but {len(day_tasks)} total tasks")
    
    # Check 3: Task distribution
    if stats['max_tasks_per_day'] > 5:
        issues.append(f"Maximum tasks per day ({stats['max_tasks_per_day']}) is too high")
    
    if issues:
        print("\n❌ Issues Found:")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print("\n✅ All critical checks passed!")
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"  • {warning}")
    
    return {
        "stats": stats,
        "tasks_by_day": tasks_by_day,
        "issues": issues,
        "warnings": warnings
    }

async def main():
    """Run all test cases"""
    print_header("COMPREHENSIVE TASK GENERATION TEST SUITE")
    print("\nTesting optimized task scheduling system...")
    print("Version: 2.0 (with geographic clustering)")
    
    # Test Case 1: Hong Kong arrival with specific dates
    test1_info = {
        "destination_city": "Hong Kong",
        "arrival_date": "2025-05-04",
        "temporary_accommodation": "Wan Chai Serviced Apartment",
        "office_location": "3 Lockhart Road, Wan Chai",
        "housing_budget": 65000,
        "housing_bedrooms": 2,
        "family_size": 1,
    }
    
    test1_messages = [
        {
            "role": "user",
            "content": "Hi! I'm moving to Hong Kong on May 4, 2025. I'll be staying at a serviced apartment in Wan Chai temporarily. My office is at 3 Lockhart Road, Wan Chai. I need to find a 2-bedroom apartment with a budget of HKD 65,000. I'd like to view properties on May 8 and open a bank account on May 9."
        }
    ]
    
    result1 = await run_test("Hong Kong Arrival with Specific Dates", test1_info, test1_messages)
    
    # Test Case 2: Simple arrival without specific dates
    test2_info = {
        "destination_city": "Hong Kong",
        "arrival_date": "2025-06-01",
        "temporary_accommodation": "Central Hotel",
        "family_size": 1,
    }
    
    test2_messages = [
        {
            "role": "user",
            "content": "I'm arriving in Hong Kong on June 1st and staying at a hotel in Central. I need help settling in."
        }
    ]
    
    result2 = await run_test("Simple Hong Kong Arrival", test2_info, test2_messages)
    
    # Summary
    print_header("TEST SUMMARY")
    
    all_passed = True
    
    if result1:
        print("\n✓ Test 1: Hong Kong Arrival with Specific Dates")
        print(f"  Tasks: {result1['stats']['total_tasks']}")
        print(f"  Days: {result1['stats']['total_days']}")
        print(f"  Max/day: {result1['stats']['max_tasks_per_day']}")
        if result1['issues']:
            print(f"  Issues: {len(result1['issues'])}")
            all_passed = False
        else:
            print("  Status: ✅ PASSED")
    else:
        print("\n✗ Test 1: FAILED")
        all_passed = False
    
    if result2:
        print("\n✓ Test 2: Simple Hong Kong Arrival")
        print(f"  Tasks: {result2['stats']['total_tasks']}")
        print(f"  Days: {result2['stats']['total_days']}")
        print(f"  Max/day: {result2['stats']['max_tasks_per_day']}")
        if result2['issues']:
            print(f"  Issues: {len(result2['issues'])}")
            all_passed = False
        else:
            print("  Status: ✅ PASSED")
    else:
        print("\n✗ Test 2: FAILED")
        all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED!".center(80))
    else:
        print("⚠️  SOME TESTS FAILED OR HAVE ISSUES".center(80))
    print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
