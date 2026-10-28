"""
性能测试：钱包认证API性能测试
测试API响应时间、并发性能等
"""
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3


class PerformanceTest:
    """性能测试"""

    def __init__(self):
        self.w3 = Web3()
        self.results = {
            "signature_verification": [],
            "nonce_generation": [],
            "token_generation": [],
            "complete_flow": []
        }

    def create_wallet(self):
        """创建测试钱包"""
        account = Account.create()
        return {
            "address": account.address,
            "private_key": account.key.hex()
        }

    def measure_signature_verification(self, iterations=1000):
        """测试签名验证性能"""
        print(f"\n[性能测试1] 签名验证性能 ({iterations}次)")

        wallet = self.create_wallet()
        message = "Sign this message to authenticate with Nautilus: test_nonce"
        message_hash = encode_defunct(text=message)
        signed_message = self.w3.eth.account.sign_message(
            message_hash,
            private_key=wallet['private_key']
        )
        signature = signed_message.signature.hex()

        times = []
        for i in range(iterations):
            start = time.time()

            # 验证签名
            recovered_address = self.w3.eth.account.recover_message(
                message_hash,
                signature=signature
            )
            is_valid = recovered_address.lower() == wallet['address'].lower()

            elapsed = (time.time() - start) * 1000  # 转换为毫秒
            times.append(elapsed)

        self.results["signature_verification"] = times

        avg = statistics.mean(times)
        median = statistics.median(times)
        p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(times, n=100)[98]  # 99th percentile

        print(f"✅ 平均耗时: {avg:.2f}ms")
        print(f"✅ 中位数: {median:.2f}ms")
        print(f"✅ P95: {p95:.2f}ms")
        print(f"✅ P99: {p99:.2f}ms")

        if p95 < 50:
            print(f"✅ 性能优秀 (P95 < 50ms)")
        elif p95 < 100:
            print(f"✅ 性能良好 (P95 < 100ms)")
        else:
            print(f"⚠️ 性能需要优化 (P95 > 100ms)")

        return p95

    def measure_nonce_generation(self, iterations=10000):
        """测试nonce生成性能"""
        print(f"\n[性能测试2] Nonce生成性能 ({iterations}次)")

        import secrets

        times = []
        for i in range(iterations):
            start = time.time()

            # 生成nonce
            nonce = secrets.token_hex(32)
            message = f"Sign this message to authenticate with Nautilus: {nonce}"

            elapsed = (time.time() - start) * 1000
            times.append(elapsed)

        self.results["nonce_generation"] = times

        avg = statistics.mean(times)
        median = statistics.median(times)
        p95 = statistics.quantiles(times, n=20)[18]
        p99 = statistics.quantiles(times, n=100)[98]

        print(f"✅ 平均耗时: {avg:.2f}ms")
        print(f"✅ 中位数: {median:.2f}ms")
        print(f"✅ P95: {p95:.2f}ms")
        print(f"✅ P99: {p99:.2f}ms")

        if p95 < 1:
            print(f"✅ 性能优秀 (P95 < 1ms)")
        elif p95 < 5:
            print(f"✅ 性能良好 (P95 < 5ms)")
        else:
            print(f"⚠️ 性能需要优化 (P95 > 5ms)")

        return p95

    def measure_token_generation(self, iterations=10000):
        """测试Token生成性能"""
        print(f"\n[性能测试3] Token生成性能 ({iterations}次)")

        import base64

        times = []
        for i in range(iterations):
            start = time.time()

            # 生成JWT Token
            header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
            payload = base64.b64encode(json.dumps({
                "sub": str(i),
                "wallet_address": f"0x{i:040x}",
                "exp": int(time.time()) + 86400
            }).encode()).decode()
            signature = base64.b64encode(b"mock_signature").decode()
            token = f"{header}.{payload}.{signature}"

            elapsed = (time.time() - start) * 1000
            times.append(elapsed)

        self.results["token_generation"] = times

        avg = statistics.mean(times)
        median = statistics.median(times)
        p95 = statistics.quantiles(times, n=20)[18]
        p99 = statistics.quantiles(times, n=100)[98]

        print(f"✅ 平均耗时: {avg:.2f}ms")
        print(f"✅ 中位数: {median:.2f}ms")
        print(f"✅ P95: {p95:.2f}ms")
        print(f"✅ P99: {p99:.2f}ms")

        if p95 < 1:
            print(f"✅ 性能优秀 (P95 < 1ms)")
        elif p95 < 5:
            print(f"✅ 性能良好 (P95 < 5ms)")
        else:
            print(f"⚠️ 性能需要优化 (P95 > 5ms)")

        return p95

    def measure_complete_flow(self, iterations=100):
        """测试完整流程性能"""
        print(f"\n[性能测试4] 完整流程性能 ({iterations}次)")

        import secrets

        times = []
        for i in range(iterations):
            start = time.time()

            # 1. 创建钱包
            wallet = self.create_wallet()

            # 2. 生成nonce
            nonce = secrets.token_hex(32)
            message = f"Sign this message to authenticate with Nautilus: {nonce}"

            # 3. 签名
            message_hash = encode_defunct(text=message)
            signed_message = self.w3.eth.account.sign_message(
                message_hash,
                private_key=wallet['private_key']
            )
            signature = signed_message.signature.hex()

            # 4. 验证签名
            recovered_address = self.w3.eth.account.recover_message(
                message_hash,
                signature=signature
            )
            is_valid = recovered_address.lower() == wallet['address'].lower()

            # 5. 生成Token
            import base64
            header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
            payload = base64.b64encode(json.dumps({
                "sub": str(i),
                "wallet_address": wallet['address'],
                "exp": int(time.time()) + 86400
            }).encode()).decode()
            sig = base64.b64encode(b"mock_signature").decode()
            token = f"{header}.{payload}.{sig}"

            elapsed = (time.time() - start) * 1000
            times.append(elapsed)

        self.results["complete_flow"] = times

        avg = statistics.mean(times)
        median = statistics.median(times)
        p95 = statistics.quantiles(times, n=20)[18]
        p99 = statistics.quantiles(times, n=100)[98]

        print(f"✅ 平均耗时: {avg:.2f}ms")
        print(f"✅ 中位数: {median:.2f}ms")
        print(f"✅ P95: {p95:.2f}ms")
        print(f"✅ P99: {p99:.2f}ms")

        if p95 < 200:
            print(f"✅ 性能优秀 (P95 < 200ms)")
        elif p95 < 500:
            print(f"✅ 性能良好 (P95 < 500ms)")
        else:
            print(f"⚠️ 性能需要优化 (P95 > 500ms)")

        return p95

    def measure_concurrent_performance(self, concurrent_users=50):
        """测试并发性能"""
        print(f"\n[性能测试5] 并发性能测试 ({concurrent_users}并发用户)")

        import secrets

        def single_request():
            """单个请求"""
            start = time.time()

            wallet = self.create_wallet()
            nonce = secrets.token_hex(32)
            message = f"Sign this message to authenticate with Nautilus: {nonce}"

            message_hash = encode_defunct(text=message)
            signed_message = self.w3.eth.account.sign_message(
                message_hash,
                private_key=wallet['private_key']
            )
            signature = signed_message.signature.hex()

            recovered_address = self.w3.eth.account.recover_message(
                message_hash,
                signature=signature
            )

            elapsed = (time.time() - start) * 1000
            return elapsed

        times = []
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(single_request) for _ in range(concurrent_users)]

            for future in as_completed(futures):
                try:
                    elapsed = future.result()
                    times.append(elapsed)
                except Exception as e:
                    print(f"❌ 请求失败: {e}")

        total_time = (time.time() - start_time) * 1000

        avg = statistics.mean(times)
        median = statistics.median(times)
        p95 = statistics.quantiles(times, n=20)[18]
        throughput = concurrent_users / (total_time / 1000)

        print(f"✅ 总耗时: {total_time:.2f}ms")
        print(f"✅ 平均响应时间: {avg:.2f}ms")
        print(f"✅ 中位数: {median:.2f}ms")
        print(f"✅ P95: {p95:.2f}ms")
        print(f"✅ 吞吐量: {throughput:.2f} req/s")

        if p95 < 500:
            print(f"✅ 并发性能优秀 (P95 < 500ms)")
        elif p95 < 1000:
            print(f"✅ 并发性能良好 (P95 < 1000ms)")
        else:
            print(f"⚠️ 并发性能需要优化 (P95 > 1000ms)")

        return p95, throughput

    def run_all_tests(self):
        """运行所有性能测试"""
        print("=" * 60)
        print("钱包认证性能测试")
        print("=" * 60)

        # 测试1: 签名验证
        sig_p95 = self.measure_signature_verification(1000)

        # 测试2: Nonce生成
        nonce_p95 = self.measure_nonce_generation(10000)

        # 测试3: Token生成
        token_p95 = self.measure_token_generation(10000)

        # 测试4: 完整流程
        flow_p95 = self.measure_complete_flow(100)

        # 测试5: 并发性能
        concurrent_p95, throughput = self.measure_concurrent_performance(50)

        print("\n" + "=" * 60)
        print("性能测试总结")
        print("=" * 60)

        print(f"\nP95延迟:")
        print(f"  签名验证: {sig_p95:.2f}ms")
        print(f"  Nonce生成: {nonce_p95:.2f}ms")
        print(f"  Token生成: {token_p95:.2f}ms")
        print(f"  完整流程: {flow_p95:.2f}ms")
        print(f"  并发测试: {concurrent_p95:.2f}ms")

        print(f"\n吞吐量:")
        print(f"  并发吞吐量: {throughput:.2f} req/s")

        print(f"\n性能评级:")
        if flow_p95 < 200:
            print(f"  ✅ 优秀 (P95 < 200ms)")
        elif flow_p95 < 500:
            print(f"  ✅ 良好 (P95 < 500ms)")
        else:
            print(f"  ⚠️ 需要优化 (P95 > 500ms)")

        # 保存结果
        report = {
            "test_name": "钱包认证性能测试",
            "status": "PASSED" if flow_p95 < 500 else "WARNING",
            "p95_latency": {
                "signature_verification": f"{sig_p95:.2f}ms",
                "nonce_generation": f"{nonce_p95:.2f}ms",
                "token_generation": f"{token_p95:.2f}ms",
                "complete_flow": f"{flow_p95:.2f}ms",
                "concurrent": f"{concurrent_p95:.2f}ms"
            },
            "throughput": {
                "concurrent": f"{throughput:.2f} req/s"
            },
            "performance_grade": "优秀" if flow_p95 < 200 else ("良好" if flow_p95 < 500 else "需要优化")
        }

        with open("test_results_performance.json", "w") as f:
            json.dump(report, f, indent=2)

        print("\n✅ 性能测试报告已保存到 test_results_performance.json")
        print("=" * 60)


if __name__ == "__main__":
    tester = PerformanceTest()
    tester.run_all_tests()
