"""
Load testing suite for AI Service.

This module contains comprehensive load tests including:
- Baseline performance tests
- Stress tests
- Spike tests
- Endurance tests
"""

import pytest
import time
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from fastapi.testclient import TestClient
from app.main import app


class PerformanceMetrics:
    """Container for performance test metrics."""
    
    def __init__(self):
        self.latencies: List[float] = []
        self.errors: List[Dict] = []
        self.start_time: float = 0
        self.end_time: float = 0
    
    def record_latency(self, latency: float):
        """Record a request latency."""
        self.latencies.append(latency)
    
    def record_error(self, error: Dict):
        """Record an error."""
        self.errors.append(error)
    
    def get_stats(self) -> Dict:
        """Calculate performance statistics."""
        if not self.latencies:
            return {}
        
        sorted_latencies = sorted(self.latencies)
        total_requests = len(self.latencies)
        total_errors = len(self.errors)
        duration = self.end_time - self.start_time
        
        return {
            'total_requests': total_requests,
            'total_errors': total_errors,
            'success_rate': ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 0,
            'duration_seconds': duration,
            'throughput_rps': total_requests / duration if duration > 0 else 0,
            'latency': {
                'min_ms': min(self.latencies) * 1000,
                'max_ms': max(self.latencies) * 1000,
                'mean_ms': statistics.mean(self.latencies) * 1000,
                'median_ms': statistics.median(self.latencies) * 1000,
                'p50_ms': sorted_latencies[int(len(sorted_latencies) * 0.50)] * 1000,
                'p95_ms': sorted_latencies[int(len(sorted_latencies) * 0.95)] * 1000,
                'p99_ms': sorted_latencies[int(len(sorted_latencies) * 0.99)] * 1000,
            }
        }


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestBaselinePerformance:
    """Baseline performance tests - normal load conditions."""
    
    def test_health_endpoint_baseline(self, client):
        """Test health endpoint under baseline load."""
        metrics = PerformanceMetrics()
        iterations = 100
        
        metrics.start_time = time.time()
        for _ in range(iterations):
            start = time.time()
            response = client.get("/healthz")
            latency = time.time() - start
            metrics.record_latency(latency)
            
            if response.status_code != 200:
                metrics.record_error({
                    'status_code': response.status_code,
                    'response': response.text
                })
        metrics.end_time = time.time()
        
        stats = metrics.get_stats()
        print(f"\nHealth Endpoint Baseline Performance:")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Success Rate: {stats['success_rate']:.2f}%")
        print(f"  Throughput: {stats['throughput_rps']:.2f} req/s")
        print(f"  P95 Latency: {stats['latency']['p95_ms']:.2f}ms")
        print(f"  P99 Latency: {stats['latency']['p99_ms']:.2f}ms")
        
        # Assertions
        assert stats['success_rate'] >= 99.0, "Success rate should be >= 99%"
        assert stats['latency']['p95_ms'] < 100, "P95 latency should be < 100ms"
        assert stats['latency']['p99_ms'] < 200, "P99 latency should be < 200ms"
    
    def test_agents_endpoint_baseline(self, client):
        """Test agents list endpoint under baseline load."""
        metrics = PerformanceMetrics()
        iterations = 50
        
        metrics.start_time = time.time()
        for _ in range(iterations):
            start = time.time()
            response = client.get("/v1/agents")
            latency = time.time() - start
            metrics.record_latency(latency)
            
            if response.status_code != 200:
                metrics.record_error({
                    'status_code': response.status_code,
                    'response': response.text
                })
        metrics.end_time = time.time()
        
        stats = metrics.get_stats()
        print(f"\nAgents Endpoint Baseline Performance:")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Success Rate: {stats['success_rate']:.2f}%")
        print(f"  P95 Latency: {stats['latency']['p95_ms']:.2f}ms")
        
        assert stats['success_rate'] >= 99.0, "Success rate should be >= 99%"
        assert stats['latency']['p95_ms'] < 200, "P95 latency should be < 200ms"


class TestStressPerformance:
    """Stress tests - high load conditions."""
    
    def test_concurrent_health_requests(self, client):
        """Test health endpoint under high concurrency."""
        metrics = PerformanceMetrics()
        concurrent_requests = 50
        requests_per_thread = 10
        total_requests = concurrent_requests * requests_per_thread
        
        def make_request():
            start = time.time()
            response = client.get("/healthz")
            latency = time.time() - start
            metrics.record_latency(latency)
            
            if response.status_code != 200:
                metrics.record_error({
                    'status_code': response.status_code,
                    'response': response.text
                })
            return response.status_code == 200
        
        metrics.start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(make_request)
                for _ in range(total_requests)
            ]
            for future in as_completed(futures):
                future.result()
        metrics.end_time = time.time()
        
        stats = metrics.get_stats()
        print(f"\nConcurrent Health Requests Stress Test:")
        print(f"  Concurrent Threads: {concurrent_requests}")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Success Rate: {stats['success_rate']:.2f}%")
        print(f"  Throughput: {stats['throughput_rps']:.2f} req/s")
        print(f"  P95 Latency: {stats['latency']['p95_ms']:.2f}ms")
        print(f"  P99 Latency: {stats['latency']['p99_ms']:.2f}ms")
        
        # Stress test assertions (more lenient)
        assert stats['success_rate'] >= 95.0, "Success rate should be >= 95% under stress"
        assert stats['latency']['p95_ms'] < 500, "P95 latency should be < 500ms under stress"
    
    def test_sustained_load(self, client):
        """Test sustained load over time."""
        metrics = PerformanceMetrics()
        duration_seconds = 30
        requests_per_second = 10
        
        metrics.start_time = time.time()
        end_time = metrics.start_time + duration_seconds
        
        def make_request():
            start = time.time()
            response = client.get("/healthz")
            latency = time.time() - start
            metrics.record_latency(latency)
            
            if response.status_code != 200:
                metrics.record_error({
                    'status_code': response.status_code,
                    'response': response.text
                })
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            while time.time() < end_time:
                for _ in range(requests_per_second):
                    executor.submit(make_request)
                time.sleep(1)
        
        metrics.end_time = time.time()
        
        stats = metrics.get_stats()
        print(f"\nSustained Load Test:")
        print(f"  Duration: {duration_seconds}s")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Success Rate: {stats['success_rate']:.2f}%")
        print(f"  Average Throughput: {stats['throughput_rps']:.2f} req/s")
        
        assert stats['success_rate'] >= 98.0, "Success rate should be >= 98% under sustained load"


class TestSpikePerformance:
    """Spike tests - sudden load increases."""
    
    def test_sudden_load_spike(self, client):
        """Test sudden spike in load."""
        metrics = PerformanceMetrics()
        
        # Baseline: 10 req/s for 5 seconds
        baseline_rps = 10
        baseline_duration = 5
        
        # Spike: 100 req/s for 2 seconds
        spike_rps = 100
        spike_duration = 2
        
        def make_request():
            start = time.time()
            response = client.get("/healthz")
            latency = time.time() - start
            metrics.record_latency(latency)
            
            if response.status_code != 200:
                metrics.record_error({
                    'status_code': response.status_code,
                    'response': response.text
                })
        
        metrics.start_time = time.time()
        
        # Baseline phase
        with ThreadPoolExecutor(max_workers=20) as executor:
            baseline_end = metrics.start_time + baseline_duration
            while time.time() < baseline_end:
                for _ in range(baseline_rps):
                    executor.submit(make_request)
                time.sleep(1)
            
            # Spike phase
            spike_end = baseline_end + spike_duration
            while time.time() < spike_end:
                for _ in range(spike_rps):
                    executor.submit(make_request)
                time.sleep(0.1)  # More frequent requests during spike
        
        metrics.end_time = time.time()
        
        stats = metrics.get_stats()
        print(f"\nSudden Load Spike Test:")
        print(f"  Baseline: {baseline_rps} req/s for {baseline_duration}s")
        print(f"  Spike: {spike_rps} req/s for {spike_duration}s")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Success Rate: {stats['success_rate']:.2f}%")
        print(f"  P95 Latency: {stats['latency']['p95_ms']:.2f}ms")
        
        # Spike test should handle sudden increases gracefully
        assert stats['success_rate'] >= 90.0, "Success rate should be >= 90% during spike"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

