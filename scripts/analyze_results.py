#!/usr/bin/env python3
"""
Analyze CI/CD test results and generate report data.
Takes JSON output from test_cicd.py and produces analysis and visualizations.
"""

import json
import argparse
from datetime import datetime
import statistics


def parse_timestamp(ts_str):
    """Parse ISO format timestamp string to datetime."""
    return datetime.fromisoformat(ts_str)


def analyze_results(json_file):
    """
    Analyze test results from JSON file.
    
    Args:
        json_file: Path to JSON results file
        
    Returns:
        dict: Analysis results
    """
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    summary = data['summary']
    changes = data['changes']
    results = data['detailed_results']
    test_info = data['test_info']
    
    print("=" * 80)
    print(f"CI/CD TEST ANALYSIS: {json_file}")
    print("=" * 80)
    
    # Basic statistics
    print(f"\nTest Duration: {test_info['duration_seconds']/60:.2f} minutes")
    print(f"Total Requests: {summary['total_requests']}")
    print(f"Success Rate: {summary['success_rate']*100:.2f}%")
    print(f"Errors: {summary['errors']}")
    print(f"Downtime Events: {summary['downtime_count']}")
    print(f"Estimated Downtime: {summary['downtime_seconds']:.1f} seconds")
    
    # Response time statistics
    response_times = [r['response_time'] for r in results if r['status'] == 'success']
    if response_times:
        print(f"\nResponse Time Statistics:")
        print(f"  Min: {min(response_times):.3f}s")
        print(f"  Max: {max(response_times):.3f}s")
        print(f"  Mean: {statistics.mean(response_times):.3f}s")
        print(f"  Median: {statistics.median(response_times):.3f}s")
        if len(response_times) > 1:
            print(f"  Std Dev: {statistics.stdev(response_times):.3f}s")
    
    # Version changes
    version_changes = changes['version_changes']
    model_changes = changes['model_changes']
    
    print(f"\n{'='*80}")
    print(f"DEPLOYMENT CHANGES DETECTED")
    print(f"{'='*80}")
    
    print(f"\nVersion Changes: {len(version_changes)}")
    for i, change in enumerate(version_changes, 1):
        change_time = parse_timestamp(change['timestamp'])
        test_start = parse_timestamp(test_info['start_time'])
        elapsed = (change_time - test_start).total_seconds()
        
        print(f"\n  Change {i}:")
        print(f"    Time: {change['timestamp']}")
        print(f"    Elapsed: {elapsed/60:.2f} minutes from test start")
        print(f"    Old Version: {change['old_version']}")
        print(f"    New Version: {change['new_version']}")
        print(f"    Request #: {change['request_number']}")
        
        # Calculate downtime around this change
        downtime_before = 0
        downtime_after = 0
        window = 10  # Check 10 requests before and after
        
        req_idx = change['request_number'] - 1
        for i in range(max(0, req_idx-window), min(len(results), req_idx+window)):
            if results[i]['status'] in ['connection_error', 'timeout']:
                if i < req_idx:
                    downtime_before += 1
                else:
                    downtime_after += 1
        
        print(f"    Downtime (±{window} requests): {downtime_before} before, {downtime_after} after")
    
    print(f"\nModel Changes: {len(model_changes)}")
    for i, change in enumerate(model_changes, 1):
        change_time = parse_timestamp(change['timestamp'])
        test_start = parse_timestamp(test_info['start_time'])
        elapsed = (change_time - test_start).total_seconds()
        
        print(f"\n  Change {i}:")
        print(f"    Time: {change['timestamp']}")
        print(f"    Elapsed: {elapsed/60:.2f} minutes from test start")
        print(f"    Old Model: {change['old_model']}")
        print(f"    New Model: {change['new_model']}")
        print(f"    Request #: {change['request_number']}")
    
    # Analyze downtime periods
    print(f"\n{'='*80}")
    print(f"DOWNTIME ANALYSIS")
    print(f"{'='*80}")
    
    downtime_periods = []
    in_downtime = False
    downtime_start = None
    
    for i, result in enumerate(results):
        if result['status'] in ['connection_error', 'timeout']:
            if not in_downtime:
                in_downtime = True
                downtime_start = i
        else:
            if in_downtime:
                in_downtime = False
                period = {
                    'start_request': downtime_start,
                    'end_request': i - 1,
                    'duration_requests': i - downtime_start,
                    'start_time': results[downtime_start]['timestamp'],
                    'end_time': results[i-1]['timestamp']
                }
                downtime_periods.append(period)
    
    # Handle case where downtime extends to end of test
    if in_downtime:
        period = {
            'start_request': downtime_start,
            'end_request': len(results) - 1,
            'duration_requests': len(results) - downtime_start,
            'start_time': results[downtime_start]['timestamp'],
            'end_time': results[-1]['timestamp']
        }
        downtime_periods.append(period)
    
    if downtime_periods:
        print(f"\nDowntime Periods Detected: {len(downtime_periods)}")
        for i, period in enumerate(downtime_periods, 1):
            duration_sec = period['duration_requests'] * test_info['request_interval']
            print(f"\n  Period {i}:")
            print(f"    Requests: {period['start_request']} to {period['end_request']}")
            print(f"    Duration: ~{duration_sec:.1f} seconds ({period['duration_requests']} requests)")
            print(f"    Start: {period['start_time']}")
            print(f"    End: {period['end_time']}")
    else:
        print("\n✓ No downtime periods detected!")
    
    # Summary statistics
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    
    if version_changes:
        print(f"\n✓ Version updates detected: {len(version_changes)}")
        print(f"  Application was successfully redeployed with new version(s)")
    else:
        print(f"\n✗ No version updates detected during test period")
    
    if model_changes:
        print(f"\n✓ Model updates detected: {len(model_changes)}")
        print(f"  ML pipeline successfully updated the model")
    else:
        print(f"\n✗ No model updates detected during test period")
    
    availability = (summary['successful'] / summary['total_requests']) * 100
    print(f"\nAvailability: {availability:.2f}%")
    
    if summary['downtime_seconds'] > 0:
        print(f"Total Downtime: {summary['downtime_seconds']:.1f} seconds")
        print(f"Downtime Percentage: {(summary['downtime_count']/summary['total_requests'])*100:.2f}%")
    else:
        print(f"Total Downtime: 0 seconds (100% uptime!)")
    
    print("=" * 80)
    
    return {
        'summary': summary,
        'changes': changes,
        'response_times': response_times,
        'downtime_periods': downtime_periods,
        'availability': availability
    }


def generate_text_report(json_files, output_file):
    """
    Generate a text report comparing multiple test results.
    
    Args:
        json_files: List of JSON result files
        output_file: Output text file path
    """
    with open(output_file, 'w') as f:
        f.write("CI/CD PIPELINE TEST REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        
        for json_file in json_files:
            f.write("=" * 80 + "\n")
            f.write(f"Test: {json_file}\n")
            f.write("=" * 80 + "\n\n")
            
            with open(json_file, 'r') as jf:
                data = json.load(jf)
            
            summary = data['summary']
            changes = data['changes']
            
            f.write(f"Duration: {summary['duration_seconds']/60:.2f} minutes\n")
            f.write(f"Total Requests: {summary['total_requests']}\n")
            f.write(f"Success Rate: {summary['success_rate']*100:.2f}%\n")
            f.write(f"Downtime: {summary['downtime_seconds']:.1f} seconds\n")
            f.write(f"Version Changes: {len(changes['version_changes'])}\n")
            f.write(f"Model Changes: {len(changes['model_changes'])}\n")
            f.write("\n")
    
    print(f"\n✓ Text report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze CI/CD test results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single test result
  python analyze_results.py test1_replicas.json
  
  # Generate comparison report
  python analyze_results.py test1_replicas.json test2_code.json test3_dataset.json -o report.txt
        """
    )
    
    parser.add_argument(
        'json_files',
        nargs='+',
        help='JSON result file(s) to analyze'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Generate comparison report to this file'
    )
    
    args = parser.parse_args()
    
    # Analyze each file
    for json_file in args.json_files:
        try:
            analyze_results(json_file)
            print("\n")
        except Exception as e:
            print(f"Error analyzing {json_file}: {e}")
    
    # Generate comparison report if requested
    if args.output:
        generate_text_report(args.json_files, args.output)


if __name__ == '__main__':
    main()
