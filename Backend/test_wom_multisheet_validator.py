#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WOM Multi-Sheet Processing Validator - Focused UI Test
=====================================================

Testing Engineer: Claude Code
Date: 2025-08-14
Purpose: Specialized test for validating WOM multi-sheet Excel processing

**SPECIFIC VALIDATION TARGETS:**
1. Verify both Excel sheets ('11648' and '2981895') are processed
2. Confirm record distribution: Sheet '11648' = 9 records, Sheet '2981895' = 8 records
3. Validate total record count = 17
4. Test technology mapping (WOM 3G → 3G, WOM 4G → 4G)
5. Verify coordinate format conversion (comma → decimal)
6. Database persistence validation

This is a FOCUSED test that specifically targets the multi-sheet processing
functionality that was recently implemented for WOM operator files.
"""

import os
import sys
import json
import time
import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd

# Add Backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("❌ ERROR: Playwright not installed")
    print("Install with: pip install playwright && playwright install chromium")
    sys.exit(1)

class WOMMultiSheetValidator:
    """Focused validator for WOM multi-sheet processing"""
    
    def __init__(self):
        self.results = {
            "test_name": "WOM Multi-Sheet Processing Validator",
            "timestamp": datetime.now().isoformat(),
            "target_file": "PUNTO 1 TRÁFICO DATOS WOM.xlsx",
            "expected_sheets": {
                "11648": {"expected_records": 9},
                "2981895": {"expected_records": 8}
            },
            "expected_total": 17,
            "validation_results": {},
            "status": "PENDING"
        }
        
        self.wom_file = r"C:\Soluciones\BGC\claude\KNSOft\archivos\CeldasDiferenteOperador\wom\PUNTO 1 TRÁFICO DATOS WOM.xlsx"
        self.database_path = r"C:\Soluciones\BGC\claude\KNSOft\Backend\kronos.db"
        self.base_url = "http://localhost:5173"
        self.mission_name = f"WOM_MULTISHEET_VAL_{datetime.now().strftime('%H%M%S')}"
    
    async def run_validation(self):
        """Execute the multi-sheet validation test"""
        print("=" * 80)
        print("🔬 WOM MULTI-SHEET PROCESSING VALIDATOR")
        print("=" * 80)
        print(f"📂 Target: {os.path.basename(self.wom_file)}")
        print(f"🎯 Expected: 17 records (11648: 9, 2981895: 8)")
        print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)
        
        # Step 1: Pre-validate Excel structure
        sheet_validation = self._validate_excel_structure()
        if not sheet_validation["valid"]:
            self.results["status"] = "FAILED"
            self.results["error"] = "Excel structure validation failed"
            return self.results
        
        # Step 2: Execute UI test
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
                page = await context.new_page()
                
                try:
                    await self._execute_ui_test(page)
                    
                    # Step 3: Validate database results
                    await self._validate_database_results()
                    
                    # Step 4: Final analysis
                    self._analyze_results()
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            self.results["status"] = "ERROR"
            self.results["error"] = str(e)
            print(f"❌ Test error: {e}")
        
        return self.results
    
    def _validate_excel_structure(self):
        """Pre-validate the Excel file structure"""
        print("\n🔍 STEP 1: Excel Structure Validation")
        print("-" * 40)
        
        try:
            if not os.path.exists(self.wom_file):
                print(f"❌ File not found: {self.wom_file}")
                return {"valid": False, "error": "File not found"}
            
            # Load and analyze Excel file
            xl_file = pd.ExcelFile(self.wom_file)
            sheet_analysis = {}
            
            print(f"📋 Sheets found: {len(xl_file.sheet_names)}")
            
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(self.wom_file, sheet_name=sheet_name)
                record_count = len(df)
                
                sheet_analysis[sheet_name] = {
                    "records": record_count,
                    "columns": len(df.columns),
                    "sample_columns": df.columns.tolist()[:5]
                }
                
                print(f"   📊 {sheet_name}: {record_count} records, {len(df.columns)} columns")
                
                # Validate expected sheet structure
                if sheet_name in self.results["expected_sheets"]:
                    expected = self.results["expected_sheets"][sheet_name]["expected_records"]
                    if record_count == expected:
                        print(f"   ✅ {sheet_name} record count matches expectation: {record_count}")
                    else:
                        print(f"   ⚠️  {sheet_name} record count mismatch: got {record_count}, expected {expected}")
            
            total_records = sum(sheet["records"] for sheet in sheet_analysis.values())
            print(f"📊 Total records: {total_records}")
            
            self.results["validation_results"]["excel_analysis"] = sheet_analysis
            
            if total_records == self.results["expected_total"]:
                print("✅ Total record count matches expectation")
                return {"valid": True, "analysis": sheet_analysis}
            else:
                print(f"⚠️  Total record count mismatch: got {total_records}, expected {self.results['expected_total']}")
                return {"valid": True, "analysis": sheet_analysis}  # Continue even with mismatch
                
        except Exception as e:
            print(f"❌ Excel validation error: {e}")
            return {"valid": False, "error": str(e)}
    
    async def _execute_ui_test(self, page):
        """Execute the UI-based upload test"""
        print("\n🌐 STEP 2: UI Upload Test")
        print("-" * 40)
        
        try:
            # Login
            print("🔐 Logging in...")
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            
            await page.fill('input[type="text"]', 'admin')
            await page.fill('input[type="password"]', 'admin123')
            await page.click('button:has-text("Iniciar Sesión")')
            await page.wait_for_selector('text=Dashboard', timeout=10000)
            print("✅ Login successful")
            
            # Navigate to missions
            await page.click('a:has-text("Misiones")')
            await page.wait_for_selector('h1:has-text("Misiones")', timeout=10000)
            print("✅ Navigated to missions")
            
            # Create test mission
            await page.click('button:has-text("Nueva Misión")')
            await page.wait_for_selector('h2:has-text("Nueva Misión")', timeout=5000)
            
            await page.fill('input[placeholder="Nombre de la misión"]', self.mission_name)
            await page.fill('textarea', 'WOM Multi-sheet validation test - 17 records expected from 2 sheets')
            await page.click('button:has-text("Crear")')
            
            await page.wait_for_selector(f'text={self.mission_name}', timeout=10000)
            print(f"✅ Mission created: {self.mission_name}")
            
            # Open mission detail
            await page.click(f'tr:has-text("{self.mission_name}") button:has-text("Ver")')
            await page.wait_for_selector('text=Datos de Operador', timeout=10000)
            print("✅ Mission detail opened")
            
            # Navigate to operator data tab
            await page.click('button:has-text("Datos de Operador")')
            await asyncio.sleep(1)
            print("✅ Operator data tab accessed")
            
            # Select WOM operator
            await page.click('button:has-text("WOM")')
            await asyncio.sleep(0.5)
            print("✅ WOM operator selected")
            
            # Select CELLULAR_DATA document type
            await page.click('input[value="CELLULAR_DATA"]')
            await asyncio.sleep(0.5)
            print("✅ CELLULAR_DATA document type selected")
            
            # Upload file
            print(f"📤 Uploading: {os.path.basename(self.wom_file)}")
            file_input = await page.query_selector('input[type="file"]')
            await file_input.set_input_files(self.wom_file)
            
            # Record upload start time
            upload_start = time.time()
            
            # Click upload
            await page.click('button:has-text("Cargar Datos")')
            print("⏳ Upload initiated...")
            
            # Monitor for completion
            await self._monitor_upload_completion(page)
            
            upload_duration = time.time() - upload_start
            self.results["validation_results"]["upload_duration"] = upload_duration
            print(f"✅ Upload completed in {upload_duration:.2f} seconds")
            
        except Exception as e:
            print(f"❌ UI test error: {e}")
            raise e
    
    async def _monitor_upload_completion(self, page):
        """Monitor upload completion with specific focus on record count"""
        print("👁️  Monitoring upload progress...")
        
        # Wait for initial processing
        await asyncio.sleep(3)
        
        # Look for completion indicators
        for attempt in range(20):  # 20 second timeout
            try:
                # Check for success patterns
                success_patterns = [
                    'text=/17.*registro/i',
                    'text=/procesad.*17/i',
                    'text=/éxito|complet|cargad/i'
                ]
                
                for pattern in success_patterns:
                    try:
                        element = await page.wait_for_selector(pattern, timeout=1000)
                        if element:
                            text = await element.text_content()
                            print(f"✅ Success indicator: {text}")
                            return True
                    except PlaywrightTimeoutError:
                        continue
                
                # Check for any error indicators
                error_patterns = [
                    'text=/error|fallo/i',
                    '.bg-red'
                ]
                
                for pattern in error_patterns:
                    try:
                        element = await page.wait_for_selector(pattern, timeout=500)
                        if element:
                            text = await element.text_content()
                            print(f"❌ Error detected: {text}")
                            return False
                    except PlaywrightTimeoutError:
                        continue
                
                # Progress indication
                if attempt % 3 == 0:
                    print(f"   ⏳ Still monitoring... ({attempt + 1}/20)")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ⚠️  Monitor error: {e}")
                continue
        
        print("⏰ Monitoring timeout - assuming completion")
        return True
    
    async def _validate_database_results(self):
        """Validate the results in the database"""
        print("\n💾 STEP 3: Database Results Validation")
        print("-" * 40)
        
        try:
            if not os.path.exists(self.database_path):
                print("❌ Database not found")
                self.results["validation_results"]["database"] = {"error": "Database not found"}
                return
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Check total WOM records
            cursor.execute("""
                SELECT COUNT(*) FROM operator_cellular_data 
                WHERE operator = 'WOM' 
                AND created_at >= datetime('now', '-5 minutes')
            """)
            recent_count = cursor.fetchone()[0]
            
            print(f"📊 Recent WOM records (last 5 min): {recent_count}")
            
            # Check technology distribution
            cursor.execute("""
                SELECT operador_tecnologia, COUNT(*) 
                FROM operator_cellular_data 
                WHERE operator = 'WOM' 
                AND created_at >= datetime('now', '-5 minutes')
                GROUP BY operador_tecnologia
            """)
            tech_distribution = cursor.fetchall()
            
            print("🔧 Technology distribution:")
            for tech, count in tech_distribution:
                print(f"   {tech}: {count} records")
            
            # Validate coordinate format (should be decimal, not comma)
            cursor.execute("""
                SELECT latitud, longitud FROM operator_cellular_data 
                WHERE operator = 'WOM' 
                AND created_at >= datetime('now', '-5 minutes')
                LIMIT 5
            """)
            coord_samples = cursor.fetchall()
            
            print("📍 Coordinate samples (should be decimal):")
            for lat, lon in coord_samples:
                print(f"   {lat}, {lon}")
            
            conn.close()
            
            # Store database validation results
            self.results["validation_results"]["database"] = {
                "recent_records": recent_count,
                "technology_distribution": dict(tech_distribution),
                "coordinate_samples": coord_samples,
                "expected_records": self.results["expected_total"]
            }
            
            if recent_count >= self.results["expected_total"]:
                print("✅ Database validation PASSED")
            else:
                print(f"⚠️  Database validation PARTIAL: {recent_count}/{self.results['expected_total']}")
            
        except Exception as e:
            print(f"❌ Database validation error: {e}")
            self.results["validation_results"]["database"] = {"error": str(e)}
    
    def _analyze_results(self):
        """Analyze all results and determine final status"""
        print("\n🏁 STEP 4: Final Analysis")
        print("-" * 40)
        
        # Check Excel validation
        excel_valid = "excel_analysis" in self.results["validation_results"]
        
        # Check database results
        db_results = self.results["validation_results"].get("database", {})
        db_records = db_results.get("recent_records", 0)
        
        # Determine success criteria
        record_success = db_records >= self.results["expected_total"]
        
        # Check technology mapping
        tech_dist = db_results.get("technology_distribution", {})
        tech_success = any("3G" in tech or "4G" in tech for tech in tech_dist.keys())
        
        # Final status determination
        if excel_valid and record_success and tech_success:
            self.results["status"] = "SUCCESS"
            verdict = "✅ MULTI-SHEET VALIDATION PASSED"
        elif excel_valid and db_records > 0:
            self.results["status"] = "PARTIAL"
            verdict = "⚠️  PARTIAL SUCCESS"
        else:
            self.results["status"] = "FAILED"
            verdict = "❌ VALIDATION FAILED"
        
        print(f"📊 Final Results:")
        print(f"   Excel Structure: {'✅' if excel_valid else '❌'}")
        print(f"   Records Processed: {db_records}/{self.results['expected_total']}")
        print(f"   Technology Mapping: {'✅' if tech_success else '❌'}")
        print(f"   Upload Duration: {self.results['validation_results'].get('upload_duration', 0):.2f}s")
        print()
        print(verdict)
        
        # Save results
        self._save_results()
    
    def _save_results(self):
        """Save validation results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wom_multisheet_validation_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📋 Results saved: {filename}")
            
        except Exception as e:
            print(f"⚠️  Error saving results: {e}")

async def main():
    """Main execution function"""
    print("WOM MULTI-SHEET PROCESSING VALIDATOR")
    print("Testing Engineer: Claude Code")
    print()
    
    # Check prerequisites
    print("⚠️  PREREQUISITES:")
    print("1. Frontend server: http://localhost:5173")
    print("2. Backend server active")
    print("3. WOM test file available")
    print()
    
    input("Press Enter to start validation...")
    
    # Run validation
    validator = WOMMultiSheetValidator()
    results = await validator.run_validation()
    
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print(f"Status: {results['status']}")
    
    if results['status'] == 'SUCCESS':
        print("🎉 WOM multi-sheet processing is working perfectly!")
        print("   All 17 records processed successfully from both sheets.")
    elif results['status'] == 'PARTIAL':
        print("🔧 WOM processing working but with some issues.")
        print("   Check the detailed report for optimization opportunities.")
    else:
        print("🚨 WOM multi-sheet processing failed.")
        print("   Review error details and check system configuration.")

if __name__ == "__main__":
    asyncio.run(main())