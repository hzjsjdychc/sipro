#!/usr/bin/env python3
"""Backend API Testing for SIPRO Fase 40 - IA & Design System V2

Tests all backend endpoints for Fase 40 including:
- GET /api/work/home - KPI drill-down data
- GET /api/work/tasks - new bucket/sla/unassigned params, wide counts
- GET /api/finance/ar - correct counts keys (unpaid/partial/paid)
- RBAC for scope=all/division (403 for sales)
- Complaints API with SLA filter
"""
import sys
import requests
from datetime import datetime

# Use public endpoint from frontend/.env
BASE_URL = "https://real-estate-stage.preview.emergentagent.com/api"
PASSWORD = "Sipro#2026"

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tokens = {}
        
    def test(self, name, condition, detail=""):
        """Run a single test assertion"""
        if condition:
            self.passed += 1
            print(f"  ✓ PASS: {name}")
            if detail:
                print(f"         {detail}")
        else:
            self.failed += 1
            print(f"  ✗ FAIL: {name}")
            if detail:
                print(f"         {detail}")
        return condition
    
    def login(self, email):
        """Login and store token"""
        try:
            r = requests.post(f"{BASE_URL}/auth/login", 
                            json={"email": email, "password": PASSWORD}, 
                            timeout=30)
            if r.status_code == 200:
                self.tokens[email] = r.json()["access_token"]
                return True
            else:
                print(f"  Login failed for {email}: {r.status_code} - {r.text[:100]}")
                return False
        except Exception as e:
            print(f"  Login error for {email}: {str(e)}")
            return False
    
    def headers(self, email):
        """Get auth headers for user"""
        return {"Authorization": f"Bearer {self.tokens.get(email, '')}"}
    
    def get(self, path, email, params=None):
        """GET request"""
        try:
            return requests.get(f"{BASE_URL}{path}", 
                              headers=self.headers(email),
                              params=params or {},
                              timeout=30)
        except Exception as e:
            print(f"  GET {path} error: {str(e)}")
            return None
    
    def summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        print("\n" + "="*60)
        print(f"TEST SUMMARY: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"FAILED: {self.failed} tests")
            return 1
        else:
            print("ALL TESTS PASSED ✓")
            return 0


def main():
    runner = TestRunner()
    
    print("="*60)
    print("SIPRO FASE 40 - IA & DESIGN SYSTEM V2 - BACKEND TESTS")
    print("="*60)
    
    # ========== AUTHENTICATION ==========
    print("\n[1] AUTHENTICATION")
    runner.test("Login superadmin@sipro.co.id", runner.login("superadmin@sipro.co.id"))
    runner.test("Login owner@sipro.co.id", runner.login("owner@sipro.co.id"))
    runner.test("Login manager@sipro.co.id", runner.login("manager@sipro.co.id"))
    runner.test("Login sales@sipro.co.id", runner.login("sales@sipro.co.id"))
    runner.test("Login finance@sipro.co.id", runner.login("finance@sipro.co.id"))
    runner.test("Login pm@sipro.co.id", runner.login("pm@sipro.co.id"))
    
    if not runner.tokens.get("superadmin@sipro.co.id"):
        print("\n✗ Cannot proceed without superadmin login")
        return 1
    
    # ========== WORK HOME - KPI DRILL-DOWN ==========
    print("\n[2] GET /api/work/home - KPI DRILL-DOWN DATA")
    r = runner.get("/work/home", "superadmin@sipro.co.id")
    runner.test("GET /api/work/home returns 200", r and r.status_code == 200,
                f"Status: {r.status_code if r else 'N/A'}")
    
    if r and r.status_code == 200:
        response = r.json()
        data = response.get("data", {})
        kpis = data.get("kpis", [])
        runner.test("KPIs list is not empty", len(kpis) > 0,
                   f"Found {len(kpis)} KPIs")
        
        # Check every KPI has drill-down link
        kpis_with_drill = [k for k in kpis if k.get("drill")]
        runner.test("Every KPI has non-empty 'drill' field", 
                   len(kpis_with_drill) == len(kpis),
                   f"{len(kpis_with_drill)}/{len(kpis)} KPIs have drill")
        
        # Check team stats for supervisor/owner roles
        team = data.get("team", {})
        if team:
            drills = team.get("drills", {})
            runner.test("Team stats have drills for supervisor/owner", 
                       bool(drills),
                       f"Drills: {list(drills.keys())[:3]}")
    
    # Test for different roles
    for role_email in ["owner@sipro.co.id", "manager@sipro.co.id", "finance@sipro.co.id", "pm@sipro.co.id"]:
        if runner.tokens.get(role_email):
            r = runner.get("/work/home", role_email)
            runner.test(f"GET /api/work/home for {role_email.split('@')[0]} returns 200",
                       r and r.status_code == 200)
    
    # ========== WORK TASKS - NEW FILTERS ==========
    print("\n[3] GET /api/work/tasks - NEW BUCKET/SLA/UNASSIGNED FILTERS")
    
    # Test bucket filters
    buckets = ["overdue", "today", "upcoming", "waiting", "review"]
    for bucket in buckets:
        r = runner.get("/work/tasks", "superadmin@sipro.co.id", 
                      {"bucket": bucket, "limit": 10})
        runner.test(f"GET /api/work/tasks?bucket={bucket} returns 200",
                   r and r.status_code == 200)
        
        if r and r.status_code == 200:
            data = r.json()
            # Check counts are "wide" (all buckets present even when filtered)
            counts = data.get("counts", {})
            runner.test(f"Counts are 'wide' for bucket={bucket}",
                       len(counts) >= 5,
                       f"Counts keys: {list(counts.keys())}")
    
    # Test SLA filter
    r = runner.get("/work/tasks", "superadmin@sipro.co.id", 
                  {"sla": "breached", "limit": 10})
    runner.test("GET /api/work/tasks?sla=breached returns 200",
               r and r.status_code == 200)
    
    # Test unassigned filter
    r = runner.get("/work/tasks", "superadmin@sipro.co.id", 
                  {"unassigned": "1", "limit": 10})
    runner.test("GET /api/work/tasks?unassigned=1 returns 200",
               r and r.status_code == 200)
    
    # ========== WORK TASKS - SCOPE RBAC ==========
    print("\n[4] GET /api/work/tasks - SCOPE RBAC")
    
    # Test scope=all for owner (should work)
    r = runner.get("/work/tasks", "owner@sipro.co.id", 
                  {"scope": "all", "limit": 10})
    runner.test("Owner can access scope=all",
               r and r.status_code == 200,
               f"Status: {r.status_code if r else 'N/A'}")
    
    # Test scope=all for sales (should be 403)
    if runner.tokens.get("sales@sipro.co.id"):
        r = runner.get("/work/tasks", "sales@sipro.co.id", 
                      {"scope": "all", "limit": 10})
        runner.test("Sales CANNOT access scope=all (403)",
                   r and r.status_code == 403,
                   f"Status: {r.status_code if r else 'N/A'}")
        
        # Test scope=division for sales (should be 403)
        r = runner.get("/work/tasks", "sales@sipro.co.id", 
                      {"scope": "division", "limit": 10})
        runner.test("Sales CANNOT access scope=division (403)",
                   r and r.status_code == 403,
                   f"Status: {r.status_code if r else 'N/A'}")
        
        # Test scope=mine for sales (should work)
        r = runner.get("/work/tasks", "sales@sipro.co.id", 
                      {"scope": "mine", "limit": 10})
        runner.test("Sales CAN access scope=mine",
                   r and r.status_code == 200,
                   f"Status: {r.status_code if r else 'N/A'}")
    
    # ========== FINANCE AR - CORRECT COUNTS ==========
    print("\n[5] GET /api/finance/ar - CORRECT COUNTS KEYS")
    
    r = runner.get("/finance/ar", "finance@sipro.co.id", {"limit": 10})
    runner.test("GET /api/finance/ar returns 200",
               r and r.status_code == 200,
               f"Status: {r.status_code if r else 'N/A'}")
    
    if r and r.status_code == 200:
        data = r.json()
        counts = data.get("counts", {})
        
        # Check counts keys are exactly unpaid/partial/paid (NOT draft/open/void)
        expected_keys = {"unpaid", "partial", "paid"}
        actual_keys = set(counts.keys())
        runner.test("Counts keys are unpaid/partial/paid (NOT draft/open/void)",
                   expected_keys.issubset(actual_keys),
                   f"Keys: {list(counts.keys())}")
        
        # Check no wrong keys
        wrong_keys = {"draft", "open", "void"} & actual_keys
        runner.test("No wrong keys (draft/open/void) in counts",
                   len(wrong_keys) == 0,
                   f"Wrong keys found: {wrong_keys}" if wrong_keys else "Clean")
    
    # Test status filter
    r = runner.get("/finance/ar", "finance@sipro.co.id", 
                  {"status": "unpaid,partial", "limit": 10})
    runner.test("GET /api/finance/ar?status=unpaid,partial returns 200",
               r and r.status_code == 200)
    
    # Test sort
    r = runner.get("/finance/ar", "finance@sipro.co.id", 
                  {"sort": "outstanding", "direction": "desc", "limit": 10})
    runner.test("GET /api/finance/ar?sort=outstanding&direction=desc returns 200",
               r and r.status_code == 200)
    
    # ========== COMPLAINTS - SLA FILTER ==========
    print("\n[6] GET /api/complaints - SLA FILTER")
    
    r = runner.get("/complaints", "superadmin@sipro.co.id", {"limit": 10})
    runner.test("GET /api/complaints returns 200",
               r and r.status_code == 200)
    
    # Test SLA filter
    r = runner.get("/complaints", "superadmin@sipro.co.id", 
                  {"sla": "breached", "limit": 10})
    runner.test("GET /api/complaints?sla=breached returns 200",
               r and r.status_code == 200)
    
    if r and r.status_code == 200:
        data = r.json()
        items = data.get("data", [])
        # All items should have SLA breached
        if items:
            breached_items = [i for i in items if i.get("sla_breached")]
            runner.test("All items in sla=breached have sla_breached=true",
                       len(breached_items) == len(items),
                       f"{len(breached_items)}/{len(items)} items breached")
    
    # ========== REGRESSION TESTS ==========
    print("\n[7] REGRESSION - EXISTING ENDPOINTS")
    
    # Projects
    r = runner.get("/projects", "pm@sipro.co.id")
    runner.test("GET /api/projects returns 200", r and r.status_code == 200)
    
    # Leads
    r = runner.get("/leads", "manager@sipro.co.id", {"limit": 10})
    runner.test("GET /api/leads returns 200", r and r.status_code == 200)
    
    # Customers
    r = runner.get("/customers", "manager@sipro.co.id", {"limit": 10})
    runner.test("GET /api/customers returns 200", r and r.status_code == 200)
    
    # Build summary
    r = runner.get("/build/summary", "pm@sipro.co.id")
    runner.test("GET /api/build/summary returns 200", r and r.status_code == 200)
    
    # ========== FINAL SUMMARY ==========
    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
