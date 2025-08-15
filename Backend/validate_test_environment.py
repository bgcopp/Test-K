#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KRONOS Test Environment Validator
=================================

Testing Engineer: Claude Code
Purpose: Validate that all prerequisites are met for WOM comprehensive testing

This script performs a comprehensive check of the test environment to ensure
all components are ready for the WOM operator testing suite.
"""

import os
import sys
import json
import requests
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

class TestEnvironmentValidator:
    """Validates the complete test environment for WOM testing"""
    
    def __init__(self):
        self.results = {
            "validation_timestamp": datetime.now().isoformat(),
            "environment_status": "PENDING",
            "checks": {},
            "recommendations": []
        }
        
        # Paths
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "Backend"
        self.frontend_dir = self.project_root / "Frontend"
        self.wom_file = self.project_root / "archivos" / "CeldasDiferenteOperador" / "wom" / "PUNTO 1 TRÁFICO DATOS WOM.xlsx"
        self.database_path = self.backend_dir / "kronos.db"
        
        # URLs
        self.frontend_url = "http://localhost:5173"
        self.backend_url = "http://localhost:8000"  # If applicable
    
    def run_validation(self):
        """Run complete environment validation"""
        print("=" * 80)
        print("🔍 KRONOS TEST ENVIRONMENT VALIDATOR")
        print("=" * 80)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Project Root: {self.project_root}")
        print("=" * 80)
        
        # Run all validation checks
        self._check_python_environment()
        self._check_project_structure()
        self._check_wom_test_file()
        self._check_database_status()
        self._check_frontend_server()
        self._check_test_scripts()
        self._check_dependencies()
        
        # Generate final assessment
        self._generate_final_assessment()
        
        # Save results
        self._save_validation_report()
        
        return self.results
    
    def _check_python_environment(self):
        """Validate Python and required packages"""
        print("\n🐍 PYTHON ENVIRONMENT CHECK")
        print("-" * 40)
        
        try:
            # Python version
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            print(f"Python Version: {python_version}")
            
            # Required packages
            required_packages = [
                'pandas', 'sqlite3', 'asyncio', 'json', 'pathlib', 'datetime'
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                    print(f"✅ {package}")
                except ImportError:
                    print(f"❌ {package}")
                    missing_packages.append(package)
            
            # Check Playwright
            try:
                import playwright
                print("✅ playwright")
                
                # Check if browsers are installed
                try:
                    from playwright.sync_api import sync_playwright
                    print("✅ playwright browsers accessible")
                    playwright_ready = True
                except Exception as e:
                    print(f"⚠️  playwright browser issue: {e}")
                    playwright_ready = False
                    self.results["recommendations"].append(
                        "Run: playwright install chromium"
                    )
                    
            except ImportError:
                print("❌ playwright")
                missing_packages.append('playwright')
                playwright_ready = False
                self.results["recommendations"].append(
                    "Install Playwright: pip install playwright && playwright install chromium"
                )
            
            self.results["checks"]["python_environment"] = {
                "status": "SUCCESS" if not missing_packages else "PARTIAL",
                "python_version": python_version,
                "missing_packages": missing_packages,
                "playwright_ready": playwright_ready
            }
            
        except Exception as e:
            self.results["checks"]["python_environment"] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Python environment check failed: {e}")
    
    def _check_project_structure(self):
        """Validate project directory structure"""
        print("\n📁 PROJECT STRUCTURE CHECK")
        print("-" * 40)
        
        try:
            required_paths = [
                ("Backend", self.backend_dir),
                ("Frontend", self.frontend_dir),
                ("WOM Test Scripts", self.backend_dir / "test_wom_comprehensive_guarantee.py"),
                ("Multi-sheet Validator", self.backend_dir / "test_wom_multisheet_validator.py"),
                ("Test Batch File", self.project_root / "run-wom-comprehensive-test.bat"),
                ("Archivos Directory", self.project_root / "archivos"),
                ("WOM Directory", self.project_root / "archivos" / "CeldasDiferenteOperador" / "wom")
            ]
            
            structure_ok = True
            for name, path in required_paths:
                if path.exists():
                    print(f"✅ {name}: {path}")
                else:
                    print(f"❌ {name}: {path} (MISSING)")
                    structure_ok = False
            
            self.results["checks"]["project_structure"] = {
                "status": "SUCCESS" if structure_ok else "PARTIAL",
                "project_root": str(self.project_root),
                "all_paths_exist": structure_ok
            }
            
        except Exception as e:
            self.results["checks"]["project_structure"] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Project structure check failed: {e}")
    
    def _check_wom_test_file(self):
        """Validate WOM test file structure and content"""
        print("\n📊 WOM TEST FILE CHECK")
        print("-" * 40)
        
        try:
            if not self.wom_file.exists():
                print(f"❌ WOM file not found: {self.wom_file}")
                self.results["checks"]["wom_test_file"] = {
                    "status": "FAILED",
                    "error": "WOM test file not found"
                }
                return
            
            # File size
            file_size_mb = self.wom_file.stat().st_size / (1024 * 1024)
            print(f"📁 File: {self.wom_file.name}")
            print(f"📏 Size: {file_size_mb:.2f} MB")
            
            # Analyze Excel structure
            xl_file = pd.ExcelFile(str(self.wom_file))
            sheet_info = {}
            total_records = 0
            
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(str(self.wom_file), sheet_name=sheet_name)
                records = len(df)
                total_records += records
                sheet_info[sheet_name] = {
                    "records": records,
                    "columns": len(df.columns)
                }
                print(f"📋 Sheet '{sheet_name}': {records} records, {len(df.columns)} columns")
            
            print(f"📊 Total Records: {total_records}")
            
            # Validate expected structure
            expected_sheets = ['11648', '2981895']
            expected_total = 17
            
            structure_valid = (
                set(xl_file.sheet_names) == set(expected_sheets) and
                total_records == expected_total
            )
            
            if structure_valid:
                print("✅ WOM file structure is VALID")
                status = "SUCCESS"
            else:
                print("⚠️  WOM file structure differs from expected")
                status = "PARTIAL"
                self.results["recommendations"].append(
                    f"Verify WOM file has expected sheets {expected_sheets} with {expected_total} total records"
                )
            
            self.results["checks"]["wom_test_file"] = {
                "status": status,
                "file_path": str(self.wom_file),
                "file_size_mb": file_size_mb,
                "sheet_count": len(xl_file.sheet_names),
                "sheets": sheet_info,
                "total_records": total_records,
                "expected_records": expected_total,
                "structure_valid": structure_valid
            }
            
        except Exception as e:
            self.results["checks"]["wom_test_file"] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ WOM file check failed: {e}")
    
    def _check_database_status(self):
        """Check database accessibility and schema"""
        print("\n💾 DATABASE STATUS CHECK")
        print("-" * 40)
        
        try:
            if self.database_path.exists():
                print(f"✅ Database exists: {self.database_path}")
                
                # Check database accessibility
                conn = sqlite3.connect(str(self.database_path))
                cursor = conn.cursor()
                
                # Check key tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['missions', 'operator_cellular_data', 'operator_call_data']
                table_status = {}
                
                for table in required_tables:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        table_status[table] = count
                        print(f"✅ Table {table}: {count} records")
                    else:
                        table_status[table] = "MISSING"
                        print(f"⚠️  Table {table}: Missing")
                
                conn.close()
                
                self.results["checks"]["database"] = {
                    "status": "SUCCESS",
                    "database_path": str(self.database_path),
                    "accessible": True,
                    "tables": table_status
                }
                
            else:
                print("⚠️  Database not found - will be created during first run")
                self.results["checks"]["database"] = {
                    "status": "INFO",
                    "database_path": str(self.database_path),
                    "accessible": False,
                    "note": "Database will be created during first run"
                }
                
        except Exception as e:
            self.results["checks"]["database"] = {
                "status": "ERROR", 
                "error": str(e)
            }
            print(f"❌ Database check failed: {e}")
    
    def _check_frontend_server(self):
        """Check if frontend server is running"""
        print("\n🌐 FRONTEND SERVER CHECK")
        print("-" * 40)
        
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Frontend server responding: {self.frontend_url}")
                print(f"📊 Status: {response.status_code}")
                server_running = True
            else:
                print(f"⚠️  Frontend server responding with status: {response.status_code}")
                server_running = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Frontend server not reachable: {self.frontend_url}")
            print("💡 Start with: cd Frontend && npm run dev")
            server_running = False
            self.results["recommendations"].append(
                "Start frontend server: cd Frontend && npm run dev"
            )
            
        except Exception as e:
            print(f"❌ Frontend server check failed: {e}")
            server_running = False
        
        self.results["checks"]["frontend_server"] = {
            "status": "SUCCESS" if server_running else "FAILED",
            "url": self.frontend_url,
            "running": server_running
        }
    
    def _check_test_scripts(self):
        """Validate test scripts are ready"""
        print("\n🧪 TEST SCRIPTS CHECK")
        print("-" * 40)
        
        test_scripts = [
            ("Comprehensive Test", "test_wom_comprehensive_guarantee.py"),
            ("Multi-sheet Validator", "test_wom_multisheet_validator.py"),
            ("Environment Validator", "validate_test_environment.py"),
        ]
        
        scripts_ready = True
        script_status = {}
        
        for name, filename in test_scripts:
            script_path = self.backend_dir / filename
            if script_path.exists():
                size_kb = script_path.stat().st_size / 1024
                print(f"✅ {name}: {filename} ({size_kb:.1f} KB)")
                script_status[name] = "READY"
            else:
                print(f"❌ {name}: {filename} (MISSING)")
                script_status[name] = "MISSING"
                scripts_ready = False
        
        # Check batch file
        batch_file = self.project_root / "run-wom-comprehensive-test.bat"
        if batch_file.exists():
            print(f"✅ Launch Script: {batch_file.name}")
            script_status["Launch Script"] = "READY"
        else:
            print(f"❌ Launch Script: {batch_file.name} (MISSING)")
            script_status["Launch Script"] = "MISSING"
            scripts_ready = False
        
        self.results["checks"]["test_scripts"] = {
            "status": "SUCCESS" if scripts_ready else "PARTIAL",
            "scripts": script_status,
            "all_ready": scripts_ready
        }
    
    def _check_dependencies(self):
        """Check Node.js and npm dependencies"""
        print("\n📦 DEPENDENCIES CHECK")
        print("-" * 40)
        
        try:
            # Check if package.json exists
            package_json = self.frontend_dir / "package.json"
            if package_json.exists():
                print(f"✅ package.json found")
                
                # Check node_modules
                node_modules = self.frontend_dir / "node_modules"
                if node_modules.exists():
                    print("✅ node_modules exists")
                    deps_installed = True
                else:
                    print("⚠️  node_modules missing - run npm install")
                    deps_installed = False
                    self.results["recommendations"].append(
                        "Install frontend dependencies: cd Frontend && npm install"
                    )
                
            else:
                print("❌ package.json not found")
                deps_installed = False
            
            self.results["checks"]["dependencies"] = {
                "status": "SUCCESS" if deps_installed else "PARTIAL",
                "package_json_exists": package_json.exists(),
                "node_modules_exists": node_modules.exists() if package_json.exists() else False
            }
            
        except Exception as e:
            self.results["checks"]["dependencies"] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ Dependencies check failed: {e}")
    
    def _generate_final_assessment(self):
        """Generate final assessment and recommendations"""
        print("\n🏁 FINAL ASSESSMENT")
        print("=" * 50)
        
        # Count successful checks
        total_checks = len(self.results["checks"])
        success_checks = len([c for c in self.results["checks"].values() 
                             if c.get("status") == "SUCCESS"])
        partial_checks = len([c for c in self.results["checks"].values() 
                             if c.get("status") == "PARTIAL"])
        failed_checks = len([c for c in self.results["checks"].values() 
                            if c.get("status") in ["FAILED", "ERROR"]])
        
        print(f"📊 Check Results: {success_checks}/{total_checks} successful")
        print(f"   ✅ Success: {success_checks}")
        print(f"   ⚠️  Partial: {partial_checks}")
        print(f"   ❌ Failed: {failed_checks}")
        
        # Determine overall status
        if failed_checks == 0 and partial_checks <= 1:
            overall_status = "READY"
            verdict = "🎉 ENVIRONMENT READY FOR TESTING!"
        elif failed_checks <= 1:
            overall_status = "MOSTLY_READY"
            verdict = "⚠️  ENVIRONMENT MOSTLY READY - Minor issues to address"
        else:
            overall_status = "NOT_READY"
            verdict = "❌ ENVIRONMENT NOT READY - Critical issues detected"
        
        self.results["environment_status"] = overall_status
        
        print(f"\n{verdict}")
        
        # Print recommendations
        if self.results["recommendations"]:
            print("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "=" * 50)
    
    def _save_validation_report(self):
        """Save validation report to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"environment_validation_{timestamp}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📋 Validation report saved: {report_file}")
            
        except Exception as e:
            print(f"⚠️  Error saving report: {e}")

def main():
    """Main validation execution"""
    print("KRONOS TEST ENVIRONMENT VALIDATOR")
    print("Testing Engineer: Claude Code")
    print()
    
    validator = TestEnvironmentValidator()
    results = validator.run_validation()
    
    # Final summary
    status = results["environment_status"]
    if status == "READY":
        print("\n🚀 Ready to run WOM comprehensive tests!")
        print("   Execute: run-wom-comprehensive-test.bat")
    elif status == "MOSTLY_READY":
        print("\n🔧 Address minor issues then run tests:")
        print("   Execute: run-wom-comprehensive-test.bat")
    else:
        print("\n🚨 Critical issues must be resolved before testing.")
        print("   Review recommendations above.")
    
    return results

if __name__ == "__main__":
    main()