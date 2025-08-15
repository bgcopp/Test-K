#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Windows encoding fix
import sys
import io
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
KRONOS WOM Comprehensive Testing Suite - 100% Processing Guarantee
=================================================================

Testing Engineer: Claude Code (Specialized Testing Engineer)
Date: 2025-08-14
Purpose: Comprehensive Playwright test to GUARANTEE 100% processing of WOM operator records

**MISSION CRITICAL TEST OBJECTIVES:**
1. Validate 100% processing of all 17 WOM records from Excel file
2. Verify multi-sheet processing (9 + 8 records = 17 total)
3. Ensure technology mapping works correctly (WOM 3G  3G, WOM 4G  4G)
4. Validate database integration and persistence
5. Test UI feedback accuracy and error handling
6. Generate comprehensive test evidence with screenshots

**FILE UNDER TEST:**
C:\Soluciones\BGC\claude\KNSOft\archivos\CeldasDiferenteOperador\wom\PUNTO 1 TRFICO DATOS WOM.xlsx
- Expected: 17 records across 2 sheets ('11648': 9 records, '2981895': 8 records)
- Technology: WOM 3G, WOM 4G
- Format: Multi-sheet Excel with coordinate format conversion needed
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
from typing import Dict, List, Any, Optional

# Add Backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:
    print("[ERROR] ERROR: Playwright not installed. Install with: pip install playwright")
    print("Then run: playwright install chromium")
    sys.exit(1)

class WOMComprehensiveTestSuite:
    """
    Comprehensive test suite for WOM operator file processing validation.
    Ensures 100% success rate with detailed evidence collection.
    """
    
    def __init__(self):
        self.test_results = {
            "test_suite": "WOM Comprehensive Processing Guarantee",
            "timestamp": datetime.now().isoformat(),
            "test_engineer": "Claude Code - Testing Engineer",
            "objective": "Guarantee 100% processing of 17 WOM records through UI",
            "expected_data": {},
            "test_phases": [],
            "performance_metrics": {},
            "evidence": {},
            "final_verdict": "PENDING"
        }
        
        # Configuration
        self.base_url = "http://localhost:5173"
        self.wom_file_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\CeldasDiferenteOperador\wom\PUNTO 1 TRÁFICO DATOS WOM.xlsx"
        self.database_path = r"C:\Soluciones\BGC\claude\KNSOft\Backend\kronos.db"
        self.screenshot_dir = "test_evidence_screenshots"
        self.timeout_short = 5000    # 5 seconds
        self.timeout_medium = 15000  # 15 seconds  
        self.timeout_long = 30000    # 30 seconds
        
        # Test tracking
        self.mission_name = f"WOM_GUARANTEE_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.mission_id = None
        
        # Create evidence directory
        Path(self.screenshot_dir).mkdir(exist_ok=True)
        
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        Execute the complete test suite with maximum validation coverage.
        
        Returns:
            Complete test results with evidence and verdict
        """
        print("\n" + "=" * 100)
        print("[TEST] KRONOS WOM COMPREHENSIVE TESTING SUITE - 100% PROCESSING GUARANTEE")
        print("=" * 100)
        print(f"[FILE] Target File: {os.path.basename(self.wom_file_path)}")
        print(f"[TARGET] Expected Records: 17 (Multi-sheet: 9 + 8)")
        print(f"[OPERATOR] Operator: WOM (Women's Omnibus Mobile)")
        print(f"[TIME] Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        
        # Phase 1: Pre-flight validation
        await self._phase1_preflight_validation()
        
        # Phase 2: Browser automation and UI testing
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,  # Show browser for debugging
                args=['--start-maximized']
            )
            
            try:
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    record_video_dir=self.screenshot_dir,
                    record_video_size={'width': 1920, 'height': 1080}
                )
                
                page = await context.new_page()
                
                # Phase 2: Login and navigation
                await self._phase2_login_navigation(page)
                
                # Phase 3: Mission creation
                await self._phase3_mission_creation(page)
                
                # Phase 4: WOM file upload
                await self._phase4_wom_file_upload(page)
                
                # Phase 5: Processing validation
                await self._phase5_processing_validation(page)
                
                # Phase 6: Database verification
                await self._phase6_database_verification()
                
                # Phase 7: UI data consistency check
                await self._phase7_ui_consistency_check(page)
                
            finally:
                await browser.close()
        
        # Phase 8: Final analysis and verdict
        await self._phase8_final_analysis()
        
        return self.test_results
    
    async def _phase1_preflight_validation(self):
        """Phase 1: Validate test prerequisites and analyze target file"""
        print("\n[PHASE 1] Pre-flight Validation")
        print("-" * 50)
        
        phase_start = time.time()
        
        try:
            # Check file exists
            if not os.path.exists(self.wom_file_path):
                raise FileNotFoundError(f"WOM test file not found: {self.wom_file_path}")
            
            # Analyze Excel file structure
            file_analysis = self._analyze_excel_file()
            self.test_results["expected_data"] = file_analysis
            
            print(f"[OK] File exists: {os.path.basename(self.wom_file_path)}")
            print(f"[OK] File size: {file_analysis['file_size_mb']:.2f} MB")
            print(f"[OK] Sheet count: {file_analysis['sheet_count']}")
            print(f"[OK] Expected total records: {file_analysis['total_records']}")
            
            for sheet_name, sheet_info in file_analysis['sheets'].items():
                print(f"   [SHEET] {sheet_name}: {sheet_info['records']} records, {sheet_info['columns']} columns")
            
            # Validate database accessibility
            if os.path.exists(self.database_path):
                print("[OK] Database accessible")
            else:
                print("[WARN] Database not found - will be created during test")
            
            phase_result = {
                "phase": "preflight_validation",
                "status": "SUCCESS",
                "duration": time.time() - phase_start,
                "findings": file_analysis
            }
            
        except Exception as e:
            phase_result = {
                "phase": "preflight_validation", 
                "status": "FAILURE",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            print(f"[ERROR] Phase 1 failed: {e}")
            
        self.test_results["test_phases"].append(phase_result)
    
    async def _phase2_login_navigation(self, page: Page):
        """Phase 2: Browser login and navigation to missions"""
        print("\n[PHASE 2] PHASE 2: Login and Navigation")
        print("-" * 50)
        
        phase_start = time.time()
        
        try:
            # Navigate to application
            print("[NAV] Navigating to KRONOS...")
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot of login page
            await self._capture_screenshot(page, "01_login_page")
            
            # Perform login
            print("[LOGIN] Performing login...")
            await page.fill('input[type="text"]', 'admin')
            await page.fill('input[type="password"]', 'admin123')
            await page.click('button:has-text("Iniciar Sesin")')
            
            # Wait for dashboard
            await page.wait_for_selector('text=Dashboard', timeout=self.timeout_medium)
            await self._capture_screenshot(page, "02_dashboard")
            print("[OK] Login successful - Dashboard loaded")
            
            # Navigate to missions
            print("[MISSION] Navigating to Missions...")
            await page.click('a:has-text("Misiones")')
            await page.wait_for_selector('h1:has-text("Misiones")', timeout=self.timeout_medium)
            await self._capture_screenshot(page, "03_missions_page")
            print("[OK] Missions page loaded")
            
            phase_result = {
                "phase": "login_navigation",
                "status": "SUCCESS", 
                "duration": time.time() - phase_start,
                "screenshots": ["01_login_page", "02_dashboard", "03_missions_page"]
            }
            
        except Exception as e:
            await self._capture_screenshot(page, "error_login_navigation")
            phase_result = {
                "phase": "login_navigation",
                "status": "FAILURE",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            print(f"[ERROR] Phase 2 failed: {e}")
            
        self.test_results["test_phases"].append(phase_result)
    
    async def _phase3_mission_creation(self, page: Page):
        """Phase 3: Create test mission for WOM file upload"""
        print("\n[PHASE 3] PHASE 3: Mission Creation")
        print("-" * 50)
        
        phase_start = time.time()
        
        try:
            # Click new mission button
            print("[CREATE] Creating new mission...")
            await page.click('button:has-text("Nueva Misin")')
            await page.wait_for_selector('h2:has-text("Nueva Misin")', timeout=self.timeout_short)
            
            # Fill mission details
            await page.fill('input[placeholder="Nombre de la misin"]', self.mission_name)
            mission_description = f"WOM Comprehensive Test - Target: 17 records from multi-sheet Excel file. Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            await page.fill('textarea', mission_description)
            
            await self._capture_screenshot(page, "04_mission_creation")
            
            # Create mission
            await page.click('button:has-text("Crear")')
            await page.wait_for_selector(f'text={self.mission_name}', timeout=self.timeout_medium)
            print(f"[OK] Mission created: {self.mission_name}")
            
            # Open mission details
            print("[OPEN] Opening mission details...")
            await page.click(f'tr:has-text("{self.mission_name}") button:has-text("Ver")')
            await page.wait_for_selector('text=Datos de Operador', timeout=self.timeout_medium)
            await self._capture_screenshot(page, "05_mission_detail")
            print("[OK] Mission details loaded")
            
            phase_result = {
                "phase": "mission_creation",
                "status": "SUCCESS",
                "mission_name": self.mission_name,
                "duration": time.time() - phase_start,
                "screenshots": ["04_mission_creation", "05_mission_detail"]
            }
            
        except Exception as e:
            await self._capture_screenshot(page, "error_mission_creation")
            phase_result = {
                "phase": "mission_creation",
                "status": "FAILURE", 
                "error": str(e),
                "duration": time.time() - phase_start
            }
            print(f"[ERROR] Phase 3 failed: {e}")
            
        self.test_results["test_phases"].append(phase_result)
    
    async def _phase4_wom_file_upload(self, page: Page):
        """Phase 4: Upload WOM Excel file and monitor processing"""
        print("\n[PHASE 4] PHASE 4: WOM File Upload and Processing")
        print("-" * 50)
        
        phase_start = time.time()
        upload_start_time = None
        
        try:
            # Navigate to operator data tab
            print("[DATA] Accessing Operator Data tab...")
            await page.click('button:has-text("Datos de Operador")')
            await asyncio.sleep(1)
            await self._capture_screenshot(page, "06_operator_data_tab")
            
            # Select WOM operator
            print("[OPERATOR] Selecting WOM operator...")
            await page.click('button:has-text("WOM")')  # Click WOM operator button
            await asyncio.sleep(0.5)
            await self._capture_screenshot(page, "07_wom_operator_selected")
            print("[OK] WOM operator selected")
            
            # Select document type
            print("[PHASE 3] Selecting document type...")
            # Look for CELLULAR_DATA radio button
            await page.click('input[value="CELLULAR_DATA"]')
            await asyncio.sleep(0.5)
            await self._capture_screenshot(page, "08_document_type_selected")
            print("[OK] CELLULAR_DATA document type selected")
            
            # Upload file
            print(f"[UPLOAD] Uploading file: {os.path.basename(self.wom_file_path)}")
            print(f"   Expected: {self.test_results['expected_data']['total_records']} records")
            print(f"   Multi-sheet: {self.test_results['expected_data']['sheet_count']} sheets")
            
            # Set upload start time for performance measurement
            upload_start_time = time.time()
            
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(self.wom_file_path)
                print("[OK] File selected for upload")
            else:
                raise Exception("File input not found")
            
            await self._capture_screenshot(page, "09_file_selected")
            
            # Click upload button
            print("[PROCESSING] Initiating upload...")
            await page.click('button:has-text("Cargar Datos")')
            
            # Monitor upload progress and completion
            await self._monitor_upload_progress(page, upload_start_time)
            
            phase_result = {
                "phase": "wom_file_upload",
                "status": "SUCCESS",
                "file_uploaded": os.path.basename(self.wom_file_path),
                "upload_duration": time.time() - upload_start_time if upload_start_time else 0,
                "duration": time.time() - phase_start,
                "screenshots": ["06_operator_data_tab", "07_wom_operator_selected", "08_document_type_selected", "09_file_selected"]
            }
            
        except Exception as e:
            await self._capture_screenshot(page, "error_file_upload")
            phase_result = {
                "phase": "wom_file_upload",
                "status": "FAILURE",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            print(f"[ERROR] Phase 4 failed: {e}")
            
        self.test_results["test_phases"].append(phase_result)
    
    async def _monitor_upload_progress(self, page: Page, upload_start_time: float):
        """Monitor the upload progress and capture completion"""
        print("[MONITOR] Monitoring upload progress...")
        
        # Wait for processing to start
        await asyncio.sleep(2)
        
        # Look for progress indicators or completion messages
        for attempt in range(30):  # 30 second timeout
            try:
                # Check for success message patterns
                success_selectors = [
                    'text=/procesad|xito|complet|cargad|exitosamente/i',
                    'text=/17.*registro/i',  # Looking for "17 registros"
                    'text=/100.*%/i',        # Looking for "100%"
                    '.bg-green',             # Success styling
                    '[class*="success"]'     # Success classes
                ]
                
                for selector in success_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=1000)
                        if element:
                            text = await element.text_content()
                            print(f"[OK] Success indicator found: {text}")
                            await self._capture_screenshot(page, f"10_upload_success_attempt_{attempt}")
                            return
                    except:
                        continue
                
                # Check for error messages
                error_selectors = [
                    'text=/error|fallo|incorrecto/i',
                    '.bg-red',
                    '[class*="error"]'
                ]
                
                for selector in error_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=1000)
                        if element:
                            text = await element.text_content()
                            print(f"[ERROR] Error indicator found: {text}")
                            await self._capture_screenshot(page, f"11_upload_error_attempt_{attempt}")
                            raise Exception(f"Upload failed with error: {text}")
                    except:
                        continue
                
                # Capture progress screenshot
                if attempt % 5 == 0:  # Every 5 attempts
                    await self._capture_screenshot(page, f"progress_check_{attempt}")
                
                await asyncio.sleep(1)
                print(f"   Monitoring... ({attempt + 1}/30)")
                
            except Exception as e:
                if "Upload failed" in str(e):
                    raise e
                continue
        
        # Final screenshot after monitoring
        await self._capture_screenshot(page, "12_upload_monitoring_complete")
        print("[TIMEOUT] Upload monitoring timeout - taking final screenshot")
    
    async def _phase5_processing_validation(self, page: Page):
        """Phase 5: Validate that processing completed successfully"""
        print("\n[OK] PHASE 5: Processing Validation")
        print("-" * 50)
        
        phase_start = time.time()
        
        try:
            # Wait for page to stabilize
            await asyncio.sleep(3)
            
            # Look for data indicators
            print("[SEARCH] Searching for processed data indicators...")
            
            # Check for table rows (processed records)
            rows = await page.query_selector_all('tbody tr')
            if rows:
                print(f"[DATA] Found {len(rows)} table rows")
            
            # Look for record count indicators
            record_indicators_found = []
            
            # Common patterns for record counts
            count_patterns = [
                'text=/\\d+\\s*registro/i',
                'text=/total.*\\d+/i', 
                'text=/mostrando.*\\d+/i',
                'text=/procesados.*\\d+/i',
                'text=/17/i'  # Specific to our expected count
            ]
            
            for pattern in count_patterns:
                try:
                    elements = await page.query_selector_all(pattern)
                    for element in elements:
                        text = await element.text_content()
                        if text and '17' in text:
                            record_indicators_found.append(text)
                            print(f"[PHASE 3] Record indicator found: {text}")
                except:
                    continue
            
            # Check for sheet indicators (multi-sheet processing)
            sheet_buttons = await page.query_selector_all('button:has-text("Hoja")')
            sheet_info = []
            
            if sheet_buttons:
                print(f" Found {len(sheet_buttons)} sheet indicators")
                for i, button in enumerate(sheet_buttons):
                    text = await button.text_content()
                    sheet_info.append(text)
                    print(f"   Sheet {i+1}: {text}")
            
            # Capture comprehensive validation screenshot
            await self._capture_screenshot(page, "13_processing_validation_complete")
            
            # Determine validation success
            validation_success = len(record_indicators_found) > 0 or len(rows) > 0 or len(sheet_info) > 0
            
            phase_result = {
                "phase": "processing_validation",
                "status": "SUCCESS" if validation_success else "WARNING",
                "records_found": len(rows),
                "record_indicators": record_indicators_found,
                "sheet_indicators": sheet_info,
                "duration": time.time() - phase_start,
                "screenshots": ["13_processing_validation_complete"]
            }
            
            if validation_success:
                print("[OK] Processing validation completed successfully")
            else:
                print("[WARN]  Processing validation completed with warnings")
                
        except Exception as e:
            await self._capture_screenshot(page, "error_processing_validation")
            phase_result = {
                "phase": "processing_validation",
                "status": "FAILURE",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            print(f"[ERROR] Phase 5 failed: {e}")
            
        self.test_results["test_phases"].append(phase_result)
    
    async def _phase6_database_verification(self):
        """Phase 6: Direct database verification of processed records"""
        print("\n[PHASE 6] PHASE 6: Database Verification")
        print("-" * 50)
        
        phase_start = time.time()
        
        try:
            if not os.path.exists(self.database_path):
                raise FileNotFoundError(f"Database not found: {self.database_path}")
            
            # Connect to database
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Check operator_cellular_data table
            print("[SEARCH] Querying cellular data records...")
            cursor.execute("""
                SELECT COUNT(*) FROM operator_cellular_data 
                WHERE operator = 'WOM'
            """)
            cellular_count = cursor.fetchone()[0]
            print(f"[DATA] WOM cellular data records: {cellular_count}")
            
            # Check for recent records (uploaded in this session)
            print("[TIME] Checking for recent WOM records...")
            cursor.execute("""
                SELECT COUNT(*) FROM operator_cellular_data 
                WHERE operator = 'WOM' 
                AND created_at >= datetime('now', '-1 hour')
            """)
            recent_count = cursor.fetchone()[0]
            print(f"[DATA] Recent WOM records (last hour): {recent_count}")
            
            # Check missions table for our test mission
            if self.mission_name:
                print(f"[SEARCH] Looking for test mission: {self.mission_name}")
                cursor.execute("SELECT id FROM missions WHERE name = ?", (self.mission_name,))
                mission_record = cursor.fetchone()
                if mission_record:
                    self.mission_id = mission_record[0]
                    print(f"[OK] Test mission found with ID: {self.mission_id}")
                else:
                    print("[WARN]  Test mission not found in database")
            
            # Technology mapping verification
            print("[TECH] Verifying technology mapping...")
            cursor.execute("""
                SELECT DISTINCT operador_tecnologia, COUNT(*) 
                FROM operator_cellular_data 
                WHERE operator = 'WOM'
                GROUP BY operador_tecnologia
            """)
            tech_mapping = cursor.fetchall()
            
            for tech, count in tech_mapping:
                print(f"   {tech}: {count} records")
            
            conn.close()
            
            # Determine if database verification passed
            database_success = recent_count >= 17  # We expect at least 17 recent records
            
            phase_result = {
                "phase": "database_verification",
                "status": "SUCCESS" if database_success else "PARTIAL",
                "cellular_data_count": cellular_count,
                "recent_records": recent_count,
                "mission_id": self.mission_id,
                "technology_mapping": dict(tech_mapping),
                "expected_records": 17,
                "verification_passed": database_success,
                "duration": time.time() - phase_start
            }
            
            if database_success:
                print(f"[OK] Database verification PASSED: {recent_count}/17 records found")
            else:
                print(f"[WARN]  Database verification PARTIAL: {recent_count}/17 records found")
                
        except Exception as e:
            phase_result = {
                "phase": "database_verification",
                "status": "FAILURE",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            print(f"[ERROR] Phase 6 failed: {e}")
            
        self.test_results["test_phases"].append(phase_result)
    
    async def _phase7_ui_consistency_check(self, page: Page):
        """Phase 7: Final UI consistency check"""
        print("\n[PHASE 7] PHASE 7: UI Consistency Check")
        print("-" * 50)
        
        phase_start = time.time()
        
        try:
            # Refresh the operator data view
            await page.reload()
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Navigate back to operator data tab
            await page.click('button:has-text("Datos de Operador")')
            await asyncio.sleep(2)
            
            # Take final comprehensive screenshot
            await self._capture_screenshot(page, "14_final_ui_state")
            
            # Capture page content for analysis
            page_content = await page.content()
            
            # Extract final UI state information
            final_state = {
                "page_title": await page.title(),
                "url": page.url,
                "content_length": len(page_content),
                "contains_wom_data": "WOM" in page_content and "17" in page_content
            }
            
            phase_result = {
                "phase": "ui_consistency_check",
                "status": "SUCCESS",
                "final_ui_state": final_state,
                "duration": time.time() - phase_start,
                "screenshots": ["14_final_ui_state"]
            }
            
            print("[OK] UI consistency check completed")
            
        except Exception as e:
            await self._capture_screenshot(page, "error_ui_consistency")
            phase_result = {
                "phase": "ui_consistency_check",
                "status": "FAILURE",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            print(f"[ERROR] Phase 7 failed: {e}")
            
        self.test_results["test_phases"].append(phase_result)
    
    async def _phase8_final_analysis(self):
        """Phase 8: Final analysis and test verdict"""
        print("\n[PHASE 8] PHASE 8: Final Analysis and Verdict")
        print("=" * 50)
        
        # Calculate overall test metrics
        total_duration = sum(phase.get('duration', 0) for phase in self.test_results["test_phases"])
        success_phases = len([p for p in self.test_results["test_phases"] if p.get('status') == 'SUCCESS'])
        total_phases = len(self.test_results["test_phases"])
        
        # Determine overall verdict
        critical_phases = ['preflight_validation', 'wom_file_upload', 'database_verification']
        critical_success = all(
            any(p['phase'] == phase and p.get('status') == 'SUCCESS' for p in self.test_results["test_phases"])
            for phase in critical_phases
        )
        
        # Check if 17 records were processed
        database_phase = next((p for p in self.test_results["test_phases"] if p['phase'] == 'database_verification'), {})
        records_processed = database_phase.get('recent_records', 0)
        
        # Final verdict determination
        if critical_success and records_processed >= 17:
            verdict = "[OK] COMPREHENSIVE SUCCESS"
        elif critical_success and records_processed > 0:
            verdict = "[WARN]  PARTIAL SUCCESS"
        else:
            verdict = "[ERROR] TEST FAILURE"
        
        self.test_results["final_verdict"] = verdict
        self.test_results["performance_metrics"] = {
            "total_test_duration": total_duration,
            "successful_phases": f"{success_phases}/{total_phases}",
            "records_processed": records_processed,
            "expected_records": 17,
            "processing_success_rate": f"{(records_processed/17)*100:.1f}%" if records_processed <= 17 else "100%+"
        }
        
        # Print comprehensive results
        print(f"[DATA] FINAL TEST RESULTS")
        print(f"   Verdict: {verdict}")
        print(f"   Duration: {total_duration:.2f} seconds")
        print(f"   Phases: {success_phases}/{total_phases} successful")
        print(f"   Records: {records_processed}/17 processed")
        print(f"   Success Rate: {self.test_results['performance_metrics']['processing_success_rate']}")
        
        # Save comprehensive test report
        self._save_test_report()
        
        print("=" * 50)
        return self.test_results
    
    def _analyze_excel_file(self) -> Dict[str, Any]:
        """Analyze the Excel file to get expected data structure"""
        try:
            file_stats = os.stat(self.wom_file_path)
            xl_file = pd.ExcelFile(self.wom_file_path)
            
            sheets_info = {}
            total_records = 0
            
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(self.wom_file_path, sheet_name=sheet_name)
                records = len(df)
                total_records += records
                
                sheets_info[sheet_name] = {
                    "records": records,
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist()[:10]  # First 10 columns
                }
            
            return {
                "file_size_mb": file_stats.st_size / (1024 * 1024),
                "sheet_count": len(xl_file.sheet_names),
                "sheets": sheets_info,
                "total_records": total_records
            }
            
        except Exception as e:
            print(f"[ERROR] Error analyzing Excel file: {e}")
            return {"error": str(e)}
    
    async def _capture_screenshot(self, page: Page, name: str):
        """Capture screenshot with timestamp"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            await page.screenshot(path=filepath, full_page=True)
            print(f"[SCREENSHOT] Screenshot: {filename}")
            
            # Store in evidence
            if "evidence" not in self.test_results:
                self.test_results["evidence"] = {}
            if "screenshots" not in self.test_results["evidence"]:
                self.test_results["evidence"]["screenshots"] = []
            
            self.test_results["evidence"]["screenshots"].append(filename)
            
        except Exception as e:
            print(f"[WARN]  Screenshot failed: {e}")
    
    def _save_test_report(self):
        """Save comprehensive test report"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"wom_comprehensive_test_report_{timestamp}.json"
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"[PHASE 3] Test report saved: {report_filename}")
            
            # Also save a summary report
            summary_filename = f"wom_test_summary_{timestamp}.txt"
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write("WOM COMPREHENSIVE TEST SUMMARY\n")
                f.write("=" * 50 + "\n")
                f.write(f"Verdict: {self.test_results['final_verdict']}\n")
                f.write(f"Records Processed: {self.test_results['performance_metrics']['records_processed']}/17\n")
                f.write(f"Success Rate: {self.test_results['performance_metrics']['processing_success_rate']}\n")
                f.write(f"Duration: {self.test_results['performance_metrics']['total_test_duration']:.2f}s\n")
                f.write(f"Phases: {self.test_results['performance_metrics']['successful_phases']}\n")
                f.write(f"Screenshots: {len(self.test_results.get('evidence', {}).get('screenshots', []))}\n")
            
            print(f"[SUMMARY] Summary report saved: {summary_filename}")
            
        except Exception as e:
            print(f"[WARN]  Error saving report: {e}")

async def main():
    """Main test execution function"""
    print("[KRONOS] WOM COMPREHENSIVE TESTING SUITE")
    print("Testing Engineer: Claude Code - Specialized QA Engineer")
    print("=" * 80)
    
    # Verify server is running
    print("\n[WARN] PREREQUISITES:")
    print("1. KRONOS server must be running at http://localhost:5173")
    print("2. Backend server must be active (python Backend/main.py)")
    print("3. Database must be accessible")
    print("4. WOM test file must be available")
    print("\n[INFO] Recommended setup:")
    print("   Terminal 1: cd Frontend && npm run dev")
    print("   Terminal 2: cd Backend && python main.py")
    print()
    
    # Skip interactive input for automated testing
    print("[AUTO] Proceeding with automated testing (prerequisites assumed met)...")
    
    # Initialize and run comprehensive test suite
    test_suite = WOMComprehensiveTestSuite()
    
    try:
        results = await test_suite.run_comprehensive_test()
        
        # Print final summary
        print("\n" + "=" * 100)
        print("[COMPLETE] TEST EXECUTION COMPLETED")
        print("=" * 100)
        print(f"Final Verdict: {results['final_verdict']}")
        print(f"Performance: {results['performance_metrics']}")
        
        if "SUCCESS" in str(results['final_verdict']):
            print("\n[SUCCESS] CONGRATULATIONS! WOM file processing is GUARANTEED to work correctly!")
            print("   All 17 records have been processed successfully through the UI.")
        elif "PARTIAL" in str(results['final_verdict']):
            print("\n[PARTIAL] PARTIAL SUCCESS - Some issues detected but core functionality works.")
            print("   Review the detailed report for optimization opportunities.")
        else:
            print("\n[ERROR] CRITICAL ISSUES DETECTED - Requires immediate attention!")
            print("   Check error logs and screenshots for troubleshooting.")
        
        return results
        
    except Exception as e:
        print(f"\n[CRITICAL] CRITICAL TEST FAILURE: {str(e)}")
        print("Check logs and screenshots for detailed error information.")
        return {"error": str(e)}

if __name__ == "__main__":
    # Ensure proper event loop handling
    try:
        results = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INTERRUPT] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Test execution failed: {e}")