#!/usr/bin/env python3
"""
CI/CD Testing Script for Playlist Recommender System
Tests ArgoCD redeployment for:
1. Kubernetes deployment changes (replica count)
2. Code updates (container image version)
3. Training dataset changes (ds1 vs ds2)

Measures deployment time and downtime by continuously monitoring the service.
"""

import requests
import time
import json
import argparse
from datetime import datetime, timedelta
import sys
import os


class CICDTester:
    """Test and monitor CI/CD pipeline deployment updates."""
    
    def __init__(self, service_url, test_songs=None):
        """
        Initialize the CI/CD tester.
        
        Args:
            service_url: URL of the recommendation service
            test_songs: List of songs to use for testing (default: sample songs)
        """
        self.service_url = service_url
        self.test_songs = test_songs or [
            "shape of you",
            "blinding lights",
            "dance monkey"
        ]
        self.request_interval = 2  # seconds between requests
        
    def make_request(self):
        """
        Make a single request to the recommendation service.
        
        Returns:
            dict: Response with status, version, model_date, and response_time
        """
        start_time = time.time()
        
        try:
            response = requests.post(
                self.service_url,
                json={"songs": self.test_songs},
                timeout=5
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'success',
                    'version': data.get('version'),
                    'model_date': data.get('model_date'),
                    'num_recommendations': len(data.get('songs', [])),
                    'response_time': response_time,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'error_code': response.status_code,
                    'response_time': response_time,
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'timeout',
                'response_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'connection_error',
                'response_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'exception',
                'error': str(e),
                'response_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
    
    def monitor_continuous(self, duration_minutes=10, output_file=None):
        """
        Continuously monitor the service for changes.
        
        Args:
            duration_minutes: How long to monitor (minutes)
            output_file: File to save monitoring results (JSON)
        
        Returns:
            list: List of all responses
        """
        print("=" * 80)
        print(f"Starting continuous monitoring for {duration_minutes} minutes")
        print(f"Service URL: {self.service_url}")
        print(f"Request interval: {self.request_interval} seconds")
        print("=" * 80)
        
        results = []
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        request_count = 0
        success_count = 0
        error_count = 0
        downtime_count = 0
        
        last_version = None
        last_model_date = None
        version_changes = []
        model_changes = []
        
        try:
            while datetime.now() < end_time:
                request_count += 1
                result = self.make_request()
                results.append(result)
                
                # Track statistics
                if result['status'] == 'success':
                    success_count += 1
                    
                    # Check for version change
                    current_version = result.get('version')
                    if last_version and current_version != last_version:
                        change_info = {
                            'timestamp': result['timestamp'],
                            'old_version': last_version,
                            'new_version': current_version,
                            'request_number': request_count
                        }
                        version_changes.append(change_info)
                        print(f"\n🔄 VERSION CHANGE DETECTED!")
                        print(f"   Old: {last_version} → New: {current_version}")
                        print(f"   Time: {result['timestamp']}")
                    last_version = current_version
                    
                    # Check for model date change
                    current_model = result.get('model_date')
                    if last_model_date and current_model != last_model_date:
                        change_info = {
                            'timestamp': result['timestamp'],
                            'old_model': last_model_date,
                            'new_model': current_model,
                            'request_number': request_count
                        }
                        model_changes.append(change_info)
                        print(f"\n🔄 MODEL CHANGE DETECTED!")
                        print(f"   Old: {last_model_date}")
                        print(f"   New: {current_model}")
                        print(f"   Time: {result['timestamp']}")
                    last_model_date = current_model
                    
                    # Print status
                    print(f"[{request_count:04d}] ✓ Success | v{current_version} | "
                          f"{result['response_time']:.3f}s | "
                          f"{result['num_recommendations']} recs")
                    
                else:
                    if result['status'] in ['connection_error', 'timeout']:
                        downtime_count += 1
                        print(f"[{request_count:04d}] ✗ DOWNTIME | {result['status']}")
                    else:
                        error_count += 1
                        print(f"[{request_count:04d}] ✗ Error | {result['status']}")
                
                # Wait before next request
                time.sleep(self.request_interval)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring interrupted by user")
        
        # Calculate statistics
        total_time = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("MONITORING SUMMARY")
        print("=" * 80)
        print(f"Duration: {total_time/60:.2f} minutes ({total_time:.1f} seconds)")
        print(f"Total requests: {request_count}")
        print(f"Successful: {success_count} ({success_count/request_count*100:.1f}%)")
        print(f"Errors: {error_count} ({error_count/request_count*100:.1f}%)")
        print(f"Downtime: {downtime_count} ({downtime_count/request_count*100:.1f}%)")
        
        if downtime_count > 0:
            downtime_duration = downtime_count * self.request_interval
            print(f"Estimated downtime: ~{downtime_duration:.1f} seconds")
        else:
            print(f"Estimated downtime: 0 seconds (no connection failures detected)")
        
        print(f"\nVersion changes detected: {len(version_changes)}")
        for change in version_changes:
            print(f"  - {change['old_version']} → {change['new_version']} at {change['timestamp']}")
        
        print(f"\nModel changes detected: {len(model_changes)}")
        for change in model_changes:
            print(f"  - {change['old_model'][:19]} → {change['new_model'][:19]} at {change['timestamp']}")
        
        # Save results to file
        if output_file:
            report = {
                'test_info': {
                    'service_url': self.service_url,
                    'start_time': start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'duration_seconds': total_time,
                    'request_interval': self.request_interval
                },
                'summary': {
                    'total_requests': request_count,
                    'successful': success_count,
                    'errors': error_count,
                    'downtime_count': downtime_count,
                    'downtime_seconds': downtime_count * self.request_interval,
                    'success_rate': success_count/request_count if request_count > 0 else 0
                },
                'changes': {
                    'version_changes': version_changes,
                    'model_changes': model_changes
                },
                'detailed_results': results
            }
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n✓ Results saved to: {output_file}")
        
        print("=" * 80)
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description='Monitor and test CI/CD pipeline for playlist recommender',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor for 10 minutes (default)
  python test_cicd.py http://localhost:50013/api/recommend
  
  # Monitor for 30 minutes and save results
  python test_cicd.py http://localhost:50013/api/recommend -d 30 -o results.json
  
  # Use with port forwarding to k8s service
  kubectl port-forward svc/playlist-recommender-svc 50013:50013 -n giovanamachado
  python test_cicd.py http://localhost:50013/api/recommend
        """
    )
    
    parser.add_argument(
        'service_url',
        type=str,
        help='URL of the recommendation service API endpoint'
    )
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=10,
        help='Duration to monitor in minutes (default: 10)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file to save results (JSON format)'
    )
    parser.add_argument(
        '-i', '--interval',
        type=float,
        default=2.0,
        help='Interval between requests in seconds (default: 2.0)'
    )
    
    args = parser.parse_args()
    
    # Create tester
    tester = CICDTester(args.service_url)
    tester.request_interval = args.interval
    
    # Run monitoring
    tester.monitor_continuous(
        duration_minutes=args.duration,
        output_file=args.output
    )


if __name__ == '__main__':
    main()
