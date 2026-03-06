#!/usr/bin/env python
"""
====================================
Performance Test Runner - Cantina Tita
Comprehensive performance testing orchestrator
====================================

Runs different types of performance tests:
- Load testing with Locust
- API performance benchmarks  
- Database performance tests
- System resource monitoring

Usage:
    python run_performance_tests.py --test-type all
    python run_performance_tests.py --test-type load --duration 300
    python run_performance_tests.py --test-type api --host http://localhost:8000
"""

import os
import sys
import time
import json
import argparse
import subprocess
import multiprocessing
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class PerformanceTestRunner:
    """Orchestrates performance testing across different components"""
    
    def __init__(self, base_url: str = "http://localhost:8000", results_dir: str = "performance_results"):
        self.base_url = base_url
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Test configurations
        self.load_test_configs = {
            "light": {"users": 10, "spawn_rate": 2, "duration": 60},
            "medium": {"users": 50, "spawn_rate": 5, "duration": 300},
            "heavy": {"users": 100, "spawn_rate": 10, "duration": 600},
            "stress": {"users": 200, "spawn_rate": 20, "duration": 300}
        }
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def setup_environment(self):
        """Setup testing environment"""
        print("🔧 Setting up performance testing environment...")
        
        # Check if Django server is running
        try:
            import requests
            response = requests.get(f"{self.base_url}/health/", timeout=5)
            if response.status_code == 200:
                print("✅ Django server is running")
            else:
                print("❌ Django server responded with error")
                return False
        except Exception:
            print("❌ Django server is not accessible")
            print("Please start the Django server first:")
            print("cd backend && python manage.py runserver")
            return False
        
        # Check required tools
        tools = ["locust", "pytest"]
        for tool in tools:
            if not self._check_tool_installed(tool):
                print(f"❌ {tool} is not installed")
                return False
        
        print("✅ Environment setup complete")
        return True

    def _check_tool_installed(self, tool: str) -> bool:
        """Check if a tool is installed"""
        try:
            subprocess.run([tool, "--version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def run_load_tests(self, intensity: str = "medium", duration: Optional[int] = None):
        """Run load tests using Locust"""
        print(f"🚀 Running load tests (intensity: {intensity})...")
        
        config = self.load_test_configs.get(intensity, self.load_test_configs["medium"])
        if duration:
            config["duration"] = duration
        
        # Prepare results directory
        load_results_dir = self.results_dir / f"load_test_{self.timestamp}"
        load_results_dir.mkdir(exist_ok=True)
        
        # Run Locust
        cmd = [
            "locust",
            "-f", "locustfile.py",
            "--headless",
            "--users", str(config["users"]),
            "--spawn-rate", str(config["spawn_rate"]),
            "--host", self.base_url,
            "--run-time", f"{config['duration']}s",
            "--html", str(load_results_dir / "load_test_report.html"),
            "--csv", str(load_results_dir / "load_test_results")
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd="performance_tests",
                capture_output=True,
                text=True,
                timeout=config["duration"] + 120  # Extra time for shutdown
            )
            
            if result.returncode == 0:
                print("✅ Load tests completed successfully")
                self._save_load_test_metadata(load_results_dir, config, result.stdout)
                return load_results_dir
            else:
                print(f"❌ Load tests failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Load tests timed out")
            return None

    def run_api_performance_tests(self):
        """Run API-specific performance tests"""
        print("⚡ Running API performance tests...")
        
        # Use Locust for API performance testing
        api_results_dir = self.results_dir / f"api_performance_{self.timestamp}"
        api_results_dir.mkdir(exist_ok=True)
        
        cmd = [
            "locust",
            "-f", "api_performance.py",
            "--headless",
            "--users", "20",
            "--spawn-rate", "5",
            "--host", self.base_url,
            "--run-time", "120s",
            "--html", str(api_results_dir / "api_performance_report.html"),
            "--csv", str(api_results_dir / "api_performance_results")
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd="performance_tests",
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0:
                print("✅ API performance tests completed")
                self._save_test_metadata(api_results_dir, "api_performance", result.stdout)
                return api_results_dir
            else:
                print(f"❌ API performance tests failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ API performance tests timed out")
            return None

    def run_database_performance_tests(self):
        """Run database performance tests"""
        print("🗄️  Running database performance tests...")
        
        db_results_dir = self.results_dir / f"db_performance_{self.timestamp}"
        db_results_dir.mkdir(exist_ok=True)
        
        cmd = [
            "pytest",
            "database_performance.py",
            "-m", "performance",
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file={db_results_dir / 'db_performance_report.json'}",
            "--html", str(db_results_dir / "db_performance_report.html"),
            "--self-contained-html"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd="performance_tests",
                capture_output=True,
                text=True,
                timeout=300
            )
            
            print("✅ Database performance tests completed")
            self._save_test_metadata(db_results_dir, "database_performance", result.stdout)
            
            # Also save stderr which might contain useful info
            with open(db_results_dir / "db_test_output.txt", "w") as f:
                f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
            
            return db_results_dir
            
        except subprocess.TimeoutExpired:
            print("❌ Database performance tests timed out")
            return None

    def run_stress_tests(self):
        """Run stress tests to find breaking points"""
        print("💪 Running stress tests...")
        
        stress_results_dir = self.results_dir / f"stress_test_{self.timestamp}"
        stress_results_dir.mkdir(exist_ok=True)
        
        # Progressive stress test
        user_counts = [50, 100, 150, 200, 300]
        results = {}
        
        for users in user_counts:
            print(f"  Testing with {users} concurrent users...")
            
            cmd = [
                "locust",
                "-f", "locustfile.py",
                "--headless",
                "--users", str(users),
                "--spawn-rate", str(users // 5),
                "--host", self.base_url,
                "--run-time", "60s",
                "--csv", str(stress_results_dir / f"stress_{users}users")
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    cwd="performance_tests",
                    capture_output=True,
                    text=True,
                    timeout=90
                )
                
                results[users] = {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "errors": result.stderr
                }
                
            except subprocess.TimeoutExpired:
                results[users] = {"success": False, "error": "timeout"}
                print(f"    ❌ Stress test with {users} users timed out")
                break
        
        # Save stress test summary
        with open(stress_results_dir / "stress_test_summary.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("✅ Stress tests completed")
        return stress_results_dir

    def monitor_system_resources(self, duration: int = 300):
        """Monitor system resources during testing"""
        print(f"📊 Monitoring system resources for {duration}s...")
        
        monitor_results_dir = self.results_dir / f"resource_monitor_{self.timestamp}"
        monitor_results_dir.mkdir(exist_ok=True)
        
        try:
            import psutil
            import matplotlib.pyplot as plt
            
            # Monitoring data
            timestamps = []
            cpu_usage = []
            memory_usage = []
            disk_io = []
            network_io = []
            
            start_time = time.time()
            
            while (time.time() - start_time) < duration:
                current_time = time.time() - start_time
                timestamps.append(current_time)
                
                # CPU usage
                cpu_usage.append(psutil.cpu_percent(interval=1))
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_usage.append(memory.percent)
                
                # Disk I/O
                disk_io_counters = psutil.disk_io_counters()
                if disk_io_counters:
                    disk_io.append(disk_io_counters.read_bytes + disk_io_counters.write_bytes)
                else:
                    disk_io.append(0)
                
                # Network I/O
                net_io_counters = psutil.net_io_counters()
                if net_io_counters:
                    network_io.append(net_io_counters.bytes_sent + net_io_counters.bytes_recv)
                else:
                    network_io.append(0)
            
            # Create monitoring charts
            self._create_resource_charts(monitor_results_dir, timestamps, cpu_usage, memory_usage)
            
            # Save raw monitoring data
            monitoring_data = {
                "timestamps": timestamps,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_io": disk_io,
                "network_io": network_io
            }
            
            with open(monitor_results_dir / "resource_data.json", "w") as f:
                json.dump(monitoring_data, f, indent=2)
            
            print("✅ Resource monitoring completed")
            return monitor_results_dir
            
        except ImportError:
            print("❌ psutil not available for resource monitoring")
            return None

    def _create_resource_charts(self, results_dir: Path, timestamps: List, cpu_usage: List, memory_usage: List):
        """Create resource usage charts"""
        try:
            import matplotlib.pyplot as plt
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # CPU usage chart
            ax1.plot(timestamps, cpu_usage, label='CPU Usage %', color='blue')
            ax1.set_ylabel('CPU Usage (%)')
            ax1.set_title('System Resource Usage During Performance Tests')
            ax1.legend()
            ax1.grid(True)
            
            # Memory usage chart
            ax2.plot(timestamps, memory_usage, label='Memory Usage %', color='red')
            ax2.set_xlabel('Time (seconds)')
            ax2.set_ylabel('Memory Usage (%)')
            ax2.legend()
            ax2.grid(True)
            
            plt.tight_layout()
            plt.savefig(results_dir / 'resource_usage.png', dpi=300, bbox_inches='tight')
            plt.close()
            
        except ImportError:
            print("⚠️  matplotlib not available for charts")

    def _save_load_test_metadata(self, results_dir: Path, config: Dict, output: str):
        """Save load test metadata"""
        metadata = {
            "test_type": "load_test",
            "timestamp": self.timestamp,
            "config": config,
            "base_url": self.base_url,
            "output_summary": output.split('\n')[-10:] if output else []
        }
        
        with open(results_dir / "test_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    def _save_test_metadata(self, results_dir: Path, test_type: str, output: str):
        """Save general test metadata"""
        metadata = {
            "test_type": test_type,
            "timestamp": self.timestamp,
            "base_url": self.base_url,
            "output_summary": output.split('\n')[-10:] if output else []
        }
        
        with open(results_dir / "test_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    def generate_comprehensive_report(self, test_results: List[Path]):
        """Generate a comprehensive performance report"""
        print("📋 Generating comprehensive performance report...")
        
        report_file = self.results_dir / f"performance_report_{self.timestamp}.html"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Test Report - Cantina Tita</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .success {{ background-color: #d4edda; border-color: #c3e6cb; }}
                .warning {{ background-color: #fff3cd; border-color: #ffeaa7; }}
                .error {{ background-color: #f8d7da; border-color: #f5c6cb; }}
                ul {{ list-style-type: none; padding: 0; }}
                li {{ padding: 5px; margin: 5px 0; background-color: #f8f9fa; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Performance Test Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Target: {self.base_url}</p>
            </div>
            
            <div class="section success">
                <h2>📊 Test Results Summary</h2>
                <ul>
        """
        
        for result_dir in test_results:
            if result_dir and result_dir.exists():
                test_name = result_dir.name
                html_content += f"<li>✅ {test_name} - Results available</li>"
            else:
                html_content += f"<li>❌ Test failed or incomplete</li>"
        
        html_content += f"""
                </ul>
            </div>
            
            <div class="section">
                <h2>📁 Result Files</h2>
                <p>Detailed results are available in the following directories:</p>
                <ul>
        """
        
        for result_dir in test_results:
            if result_dir and result_dir.exists():
                files = list(result_dir.glob("*"))
                html_content += f"<li><strong>{result_dir.name}</strong> ({len(files)} files)</li>"
        
        html_content += """
                </ul>
            </div>
            
            <div class="section">
                <h2>🔗 Quick Links</h2>
                <ul>
                    <li><a href="load_test_*/load_test_report.html">Load Test Report</a></li>
                    <li><a href="api_performance_*/api_performance_report.html">API Performance Report</a></li>
                    <li><a href="db_performance_*/db_performance_report.html">Database Performance Report</a></li>
                    <li><a href="resource_monitor_*/resource_usage.png">Resource Usage Charts</a></li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        with open(report_file, "w") as f:
            f.write(html_content)
        
        print(f"✅ Comprehensive report generated: {report_file}")
        return report_file

    def run_all_tests(self, load_intensity: str = "medium", monitor_duration: int = 300):
        """Run all performance tests"""
        print("🎯 Running comprehensive performance test suite...")
        
        if not self.setup_environment():
            return False
        
        results = []
        
        # Run tests
        results.append(self.run_load_tests(intensity=load_intensity))
        results.append(self.run_api_performance_tests())
        results.append(self.run_database_performance_tests())
        
        # Optional: Run resource monitoring in background
        # results.append(self.monitor_system_resources(duration=monitor_duration))
        
        # Generate report
        report_file = self.generate_comprehensive_report([r for r in results if r])
        
        print("🎉 All performance tests completed!")
        print(f"📋 Report: {report_file}")
        
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run performance tests for Cantina Tita")
    parser.add_argument("--test-type", choices=["load", "api", "database", "stress", "monitor", "all"], 
                       default="all", help="Type of test to run")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host URL")
    parser.add_argument("--intensity", choices=["light", "medium", "heavy", "stress"], 
                       default="medium", help="Load test intensity")
    parser.add_argument("--duration", type=int, help="Test duration in seconds")
    parser.add_argument("--results-dir", default="performance_results", help="Results directory")
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner(base_url=args.host, results_dir=args.results_dir)
    
    if args.test_type == "all":
        runner.run_all_tests(load_intensity=args.intensity, monitor_duration=args.duration or 300)
    elif args.test_type == "load":
        runner.run_load_tests(intensity=args.intensity, duration=args.duration)
    elif args.test_type == "api":
        runner.run_api_performance_tests()
    elif args.test_type == "database":
        runner.run_database_performance_tests()
    elif args.test_type == "stress":
        runner.run_stress_tests()
    elif args.test_type == "monitor":
        runner.monitor_system_resources(duration=args.duration or 300)


if __name__ == "__main__":
    main()