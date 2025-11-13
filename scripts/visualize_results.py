#!/usr/bin/env python3
"""
Generate visualizations from CI/CD test results.
Creates charts and graphs for the PDF report.
"""

import json
import argparse
from datetime import datetime
import sys

# Try to import matplotlib, but make it optional
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed. Visualizations will not be generated.")
    print("Install with: pip install matplotlib")


def parse_timestamp(ts_str):
    """Parse ISO format timestamp string to datetime."""
    return datetime.fromisoformat(ts_str)


def plot_timeline(json_file, output_file):
    """
    Create a timeline visualization showing request success/failure over time.
    
    Args:
        json_file: Path to JSON results file
        output_file: Path to save the plot image
    """
    if not HAS_MATPLOTLIB:
        print("Matplotlib not available. Skipping timeline plot.")
        return
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    results = data['detailed_results']
    
    # Extract timestamps and status
    timestamps = [parse_timestamp(r['timestamp']) for r in results]
    statuses = [r['status'] for r in results]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot success/failure
    success_times = [t for t, s in zip(timestamps, statuses) if s == 'success']
    error_times = [t for t, s in zip(timestamps, statuses) if s not in ['success', 'connection_error', 'timeout']]
    downtime_times = [t for t, s in zip(timestamps, statuses) if s in ['connection_error', 'timeout']]
    
    if success_times:
        ax.scatter(success_times, [1]*len(success_times), c='green', label='Success', alpha=0.6, s=10)
    if error_times:
        ax.scatter(error_times, [1]*len(error_times), c='orange', label='Error', alpha=0.8, s=20)
    if downtime_times:
        ax.scatter(downtime_times, [1]*len(downtime_times), c='red', label='Downtime', alpha=0.8, s=30, marker='x')
    
    # Mark version changes
    version_changes = data['changes']['version_changes']
    for change in version_changes:
        change_time = parse_timestamp(change['timestamp'])
        ax.axvline(x=change_time, color='blue', linestyle='--', alpha=0.7, linewidth=2)
        ax.text(change_time, 1.05, 'Version\nChange', ha='center', fontsize=8, color='blue')
    
    # Mark model changes
    model_changes = data['changes']['model_changes']
    for change in model_changes:
        change_time = parse_timestamp(change['timestamp'])
        ax.axvline(x=change_time, color='purple', linestyle='--', alpha=0.7, linewidth=2)
        ax.text(change_time, 0.95, 'Model\nChange', ha='center', fontsize=8, color='purple')
    
    # Format
    ax.set_ylim(0.9, 1.1)
    ax.set_yticks([])
    ax.set_xlabel('Time', fontsize=12)
    ax.set_title(f'Request Status Timeline - {json_file}', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Timeline plot saved to: {output_file}")
    plt.close()


def plot_response_times(json_file, output_file):
    """
    Create a plot showing response times over time.
    
    Args:
        json_file: Path to JSON results file
        output_file: Path to save the plot image
    """
    if not HAS_MATPLOTLIB:
        print("Matplotlib not available. Skipping response time plot.")
        return
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    results = data['detailed_results']
    
    # Extract successful requests
    success_results = [r for r in results if r['status'] == 'success']
    if not success_results:
        print("No successful requests to plot.")
        return
    
    timestamps = [parse_timestamp(r['timestamp']) for r in success_results]
    response_times = [r['response_time'] * 1000 for r in success_results]  # Convert to ms
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot response times
    ax.plot(timestamps, response_times, 'b-', alpha=0.5, linewidth=0.5)
    ax.scatter(timestamps, response_times, c='blue', alpha=0.3, s=5)
    
    # Add mean line
    mean_rt = sum(response_times) / len(response_times)
    ax.axhline(y=mean_rt, color='red', linestyle='--', label=f'Mean: {mean_rt:.1f}ms')
    
    # Format
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Response Time (ms)', fontsize=12)
    ax.set_title(f'Response Times - {json_file}', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Response time plot saved to: {output_file}")
    plt.close()


def plot_comparison_bar(json_files, output_file):
    """
    Create a bar chart comparing metrics across multiple tests.
    
    Args:
        json_files: List of JSON result files
        output_file: Path to save the plot image
    """
    if not HAS_MATPLOTLIB:
        print("Matplotlib not available. Skipping comparison plot.")
        return
    
    test_names = []
    deployment_times = []
    downtimes = []
    success_rates = []
    
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Extract test name
        if 'replicas' in json_file:
            test_names.append('Replica\nScaling')
        elif 'code' in json_file:
            test_names.append('Code\nUpdate')
        elif 'dataset' in json_file:
            test_names.append('Dataset\nUpdate')
        else:
            test_names.append(json_file)
        
        # Extract metrics
        summary = data['summary']
        test_info = data['test_info']
        deployment_times.append(test_info['duration_seconds'] / 60)  # Convert to minutes
        downtimes.append(summary['downtime_seconds'])
        success_rates.append(summary['success_rate'] * 100)
    
    # Create figure with subplots
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
    # Plot 1: Deployment Time
    bars1 = ax1.bar(test_names, deployment_times, color='steelblue', alpha=0.7)
    ax1.set_ylabel('Time (minutes)', fontsize=11)
    ax1.set_title('Test Duration', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}m', ha='center', va='bottom', fontsize=9)
    
    # Plot 2: Downtime
    bars2 = ax2.bar(test_names, downtimes, color='coral', alpha=0.7)
    ax2.set_ylabel('Downtime (seconds)', fontsize=11)
    ax2.set_title('Service Downtime', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.0f}s', ha='center', va='bottom', fontsize=9)
    
    # Plot 3: Success Rate
    bars3 = ax3.bar(test_names, success_rates, color='mediumseagreen', alpha=0.7)
    ax3.set_ylabel('Success Rate (%)', fontsize=11)
    ax3.set_title('Service Availability', fontsize=12, fontweight='bold')
    ax3.set_ylim(95, 101)
    ax3.grid(True, alpha=0.3, axis='y')
    
    for bar in bars3:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Comparison plot saved to: {output_file}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description='Generate visualizations from CI/CD test results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate timeline for single test
  python visualize_results.py test1_replicas.json --timeline timeline1.png
  
  # Generate comparison chart for all tests
  python visualize_results.py test1_replicas.json test2_code.json test3_dataset.json --comparison comparison.png
  
  # Generate all visualizations
  python visualize_results.py test1_replicas.json --all
        """
    )
    
    parser.add_argument(
        'json_files',
        nargs='+',
        help='JSON result file(s) to visualize'
    )
    parser.add_argument(
        '--timeline',
        type=str,
        help='Generate timeline plot and save to this file'
    )
    parser.add_argument(
        '--response-times',
        type=str,
        help='Generate response time plot and save to this file'
    )
    parser.add_argument(
        '--comparison',
        type=str,
        help='Generate comparison plot (requires multiple JSON files)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Generate all visualizations with default names'
    )
    
    args = parser.parse_args()
    
    if not HAS_MATPLOTLIB:
        print("ERROR: matplotlib is required for visualizations")
        print("Install with: pip install matplotlib")
        sys.exit(1)
    
    # Generate requested visualizations
    if args.all:
        # Generate timeline and response time for first file
        if len(args.json_files) >= 1:
            base_name = args.json_files[0].replace('.json', '')
            plot_timeline(args.json_files[0], f'{base_name}_timeline.png')
            plot_response_times(args.json_files[0], f'{base_name}_response.png')
        
        # Generate comparison if multiple files
        if len(args.json_files) > 1:
            plot_comparison_bar(args.json_files, 'comparison.png')
    else:
        if args.timeline:
            plot_timeline(args.json_files[0], args.timeline)
        
        if args.response_times:
            plot_response_times(args.json_files[0], args.response_times)
        
        if args.comparison:
            if len(args.json_files) < 2:
                print("ERROR: Comparison plot requires at least 2 JSON files")
                sys.exit(1)
            plot_comparison_bar(args.json_files, args.comparison)
    
    print("\n✓ Visualization complete!")


if __name__ == '__main__':
    main()
